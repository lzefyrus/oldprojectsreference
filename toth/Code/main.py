# -*- coding: utf-8 -*-
#
# FSVAS
#
import os
import logging
import configobj
import importlib
import argparse
import signal

# Tornado
import tornado.ioloop
import tornado.web
import tornado.escape
import tornado.httpserver

# Swagger
from documentacao.compile_json import yaml_to_json

# Wsdl
from suds.client import Client

# SSL
import requests
from suds.transport.http import HttpAuthenticated
from suds.transport import Reply


class JsonStaticHandler(tornado.web.StaticFileHandler):

    def initialize(self, path):
        self.set_header('Content-Type', 'application/json')
        super(JsonStaticHandler, self).initialize(path)

    def compute_etag(self):
        try:
            super(JsonStaticHandler, self).compute_etag()
        except Exception:
            raise tornado.web.HTTPError(404)

    def get(self, path, include_body=True):
        super(JsonStaticHandler, self).get(os.path.join(path.strip('/'), 'swagger.json'), include_body)


class RequestsTransport(HttpAuthenticated):

    def __init__(self, **kwargs):
        self.cert = kwargs.pop('cert', None)
        HttpAuthenticated.__init__(self, **kwargs)

    def send(self, request):
        # print(request.message)
        # print(request.headers)

        self.addcredentials(request)
        resp = requests.post(
            request.url,
            data=request.message,
            headers=request.headers,
            cert=self.cert)
        result = Reply(resp.status_code, resp.headers, resp.content)
        return result


def sig_handler(sig, frame):
    # print('signal:%s' % sig)
    # print('frame:%s' % frame)
    # os.system('killall python')
    tornado.ioloop.IOLoop.instance().add_callback(shutdown)

    # server.stop()
    # tornado.ioloop.IOLoop().instance().stop()
    # tornado.ioloop.IOLoop().instance().add_callback_from_signal(tornado.ioloop.IOLoop().instance().stop)
    # tornado.ioloop.IOLoop().instance().add_callback(tornado.ioloop.IOLoop().instance().stop)
    # tornado.ioloop.IOLoop().instance().add_callback(server.stop)


def shutdown():
    server.stop()
    tornado.ioloop.IOLoop().instance().add_callback(tornado.ioloop.IOLoop().instance().stop)
    tornado.ioloop.IOLoop().instance().add_callback_from_signal(tornado.ioloop.IOLoop().instance().stop)
    # slog.warning('Caught signal: %s', sig)
    # tornado.ioloop.IOLoop().current(instance=True)
    # tornado.ioloop.IOLoop.instance().stop()
    slog.info('stoping...')


# Funcao principal
def main(devel, homol, prod, debug, swagger, instances):

    global slog, server, app
    # armazeno o sinal para o desligamento
    # signal.signal(signal.SIGTERM, lambda sig, frame: tornado.ioloop.IOLoop().instance().add_callback(tornado.ioloop.IOLoop().instance().stop))
    signal.signal(signal.SIGINT, sig_handler)

    # Configuracoes do server
    serverConfig = configobj.ConfigObj('server.ini')
    # Configuracoes do app
    appConfig = configobj.ConfigObj('config.ini')

    # Caminho real dos arquivos
    path, fileName = os.path.split(os.path.realpath(__file__))

    # Import do utils pela versao do toth
    # IMPORTLIB soh usa variaveis LOCAIS
    utils = importlib.import_module('utils.%s' % (appConfig['versions']['utils']))

    # Para utilizar a sessoes
    sess = dict()

    # Valor default para dev e homol
    if not instances:
        instances = 2

    slog = utils.setup_logger(
        'tornado_oauthlib',
        logging.DEBUG if debug else logging.INFO,
        True if devel else False)

    # Desabilita o log do Suds
    logging.getLogger('suds').setLevel(logging.INFO)

    # Caso no ini esteja DEBUG ativo, grava log
    if devel:
        slog.info('DEVEL MODE')
        # Swagger urlBase
        swaggerUrlBase = appConfig['swagger']['dev']
        debug = True
        level = 'devel'
        msgUpserver = 'Server Develop Starting'

    elif homol:
        slog.info('HOMOL MODE')
        # Swagger urlBase
        swaggerUrlBase = appConfig['swagger']['homol']
        level = 'homol'
        msgUpserver = 'Server Homol Starting'

    else:
        slog.info('PROD MODE')
        # Swagger urlBase
        swaggerUrlBase = appConfig['swagger']['prod']
        level = 'prod'
        # Configuracoes do app para PROD
        appConfigProd = configobj.ConfigObj('configProd.ini')
        appConfig.update(appConfigProd)
        msgUpserver = 'Server Production Starting'

    if debug:
        slog.info('DEBUG MODE ON')
    else:
        slog.info('INFO MODE ON')

    # Lista com as urls
    URLS = []

    # configs para o tornado
    settings = dict()

    # Urls do swagger - documentacao
    if (swagger):
        slog.info('Loading Swagger...')
        # Cria os json para o swagger
        os.system('rm -rf documentacao/json-generated')

        swaggerDir = {
            'yaml_dir': os.path.join(path, 'documentacao', 'yaml'),
            'json_dir': os.path.join(path, 'documentacao', 'json-generated'),
            'browser_dir': os.path.join(path, 'documentacao', 'browser')}

        yaml_to_json(
            swaggerDir['yaml_dir'],
            swaggerDir['json_dir'],
            '',
            '%s:%s' % (swaggerUrlBase, serverConfig['tornado']['port']), appConfig['statusCode'])
        slog.info('Swagger Load.')
        for sDir in os.listdir(swaggerDir['json_dir']):
            if os.path.isdir(os.path.join(swaggerDir['json_dir'], sDir)):
                URLS += [
                        (r'/apiDoc/%s(.*)' % (sDir),
                            tornado.web.StaticFileHandler, dict(path='%s/%s/swagger.json' % (swaggerDir['json_dir'], sDir)))]
        # atualiza a rota para o swagger
        URLS += [
            (r'/apiDoc/(.*)', tornado.web.StaticFileHandler, dict(path='%s/swagger.json' % (swaggerDir['json_dir']))),
            (r'/', tornado.web.RedirectHandler, dict(url='/documentacao/browser/index.html'))]

        # settings para o swagger
        settings.update({
            'static_path': swaggerDir['browser_dir'],
            'static_url_prefix': '/documentacao/browser/'}
        )

    # Caso o arquivo de conf nao tenha virgula no final dos campos
    # O configobj nao cria uma lista com apenas 1 item
    if type(appConfig['versions']['available']) is str:
        appConfig['versions']['available'] = [appConfig['versions']['available']]

    # Dicionario com os objetos dos wsdl
    wsdlClientes = dict()

    for provisionerVersion in appConfig['versions']['available']:
        # Loopa as operadoras do arquivo de config
        for iOperator in appConfig['operators']:

            # Caso o arquivo de conf nao tenha virgula no final dos campos
            # O configobj nao cria uma lista com apenas 1 item
            if type(appConfig['operators'][iOperator]['vendors']) is str:
                appConfig['operators'][iOperator]['vendors'] = [appConfig['operators'][iOperator]['vendors']]

            # Caso o vendor nao tenha alguma versao
            if provisionerVersion not in appConfig['operators'][iOperator]['vendors'].keys():
                continue

            # Loopa os vendors do arquivo de config
            for iVendor in appConfig['operators'][iOperator]['vendors'][provisionerVersion].keys():

                # level in appConfig['operators'][iOperator]['vendors'][provisionerVersion][iVendor].keys()
                # Pega as configuracoes de endpoint sendo homol, dev ou prod
                if (level == 'homol' or level == 'devel') and 'homol' in appConfig['operators'][iOperator]['vendors'][provisionerVersion][iVendor].keys():
                        appConfig['operators'][iOperator]['vendors'][provisionerVersion][iVendor] = \
                            appConfig['operators'][iOperator]['vendors'][provisionerVersion][iVendor]['homol']
                else:
                    appConfig['operators'][iOperator]['vendors'][provisionerVersion][iVendor] = \
                        appConfig['operators'][iOperator]['vendors'][provisionerVersion][iVendor]['prod']

                # Loopa os tipos de operacoes do arquivo de config
                subUrl = ""
                for iType in appConfig['vendors'][provisionerVersion][iVendor]:

                    # Load nos wsdl
                    if 'wsdl' in appConfig['operators'][iOperator]['vendors'][provisionerVersion][iVendor].keys():
                        urlRestBase = '/%s/vendors/%s/%s/wsdl/' % (path, provisionerVersion, iVendor)
                        urlWsdl = 'file:/%s%s' % (
                            urlRestBase,
                            appConfig['operators'][iOperator]['vendors'][provisionerVersion][iVendor]['urlWsdl'])

                        # Cria a estancia do soap
                        if 'cert' in appConfig['operators'][iOperator]['vendors'][provisionerVersion][iVendor].keys():
                            wsdlClientes[iOperator] = {iVendor: Client(
                                urlWsdl,
                                location=appConfig['operators'][iOperator]['vendors'][provisionerVersion][iVendor]['urlBase'],
                                headers={"Content-TYpe": "text/xml;charset=UTF-8", "SOAPAction": ""},
                                transport=RequestsTransport(cert='%s/certificado/%s' % (
                                    urlRestBase,
                                    appConfig['operators'][iOperator]['vendors'][provisionerVersion][iVendor]['cert'])),
                                    faults=False)}
                        else:
                            wsdlClientes[iOperator] = {iVendor: Client(urlWsdl, faults=False)}

                    if iType not in subUrl:
                        # Cria a url
                        vendorsClass = getattr(importlib.import_module(
                            'vendors.%s.%s' % (provisionerVersion, iVendor)), iVendor.title())

                        URLS.append((r'/%s/%s/%s/%s/([0-9A-Za-z@_\-.]+)?(/)?' % (provisionerVersion, iVendor, iOperator, iType), vendorsClass, dict(
                            provisionerVersion=provisionerVersion,
                            vendor=iVendor,
                            operator=iOperator,
                            typeVendor=iType,
                            subUrl=False,
                            appConfig=appConfig,
                            wsdlClientes=wsdlClientes,
                            utils=utils,
                            debug=debug,
                            level=level,
                            sess=sess)))

                        # Verifica se existe uma subUrl
                        if 'suburl' in appConfig['vendors'][provisionerVersion][iVendor][iType].keys():
                            subUrl = appConfig['vendors'][provisionerVersion][iVendor][iType]['suburl']['suburl']
                            if type(subUrl) is str:
                                subUrl = [subUrl]

                            # Cria a subUrl
                            for sub in subUrl:
                                vendorsClass = getattr(importlib.import_module(
                                    'vendors.%s.%s' % (provisionerVersion, iVendor)), iVendor.title())

                                URLS.append((r'/%s/%s/%s/%s/([0-9A-Za-z@_\-.]+)?/%s/([0-9A-Za-z@_\-.]+)?' % (
                                    provisionerVersion,
                                    iVendor,
                                    iOperator,
                                    iType,
                                    sub), vendorsClass, dict(
                                        provisionerVersion=provisionerVersion,
                                        vendor=iVendor,
                                        operator=iOperator,
                                        typeVendor=sub,
                                        subUrl=True,
                                        appConfig=appConfig,
                                        wsdlClientes=wsdlClientes,
                                        utils=utils,
                                        debug=debug,
                                        level=level,
                                        sess=sess)))
                        # Limpa a variavel caso outro vendor nao tenha e nao
                        # duplicar na url
                        iType = ""

    slog.info('%s - port:%s instances:%s' % (
        msgUpserver,
        serverConfig['tornado']['port'],
        serverConfig['tornado']['instances'] if not instances else instances))

    # Pega as urls validas para as versoes
    app = tornado.web.Application(URLS, **settings)
    server = tornado.httpserver.HTTPServer(app, xheaders=True)
    server.bind(int(serverConfig['tornado']['port']))
    server.start(int(serverConfig['tornado']['instances']) if not instances else instances)

    tornado.ioloop.IOLoop().instance().start()


# Chama a funcao principal
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="python3 main.py (-d OR -p OR -hm) [optionals] -s -debug -i 100")
    parser.add_argument('-d', '--devel',
                        dest='devel',
                        default=False,
                        action='store_true',
                        help='Run server in develop mode')
    parser.add_argument('-hm', '--homol',
                        dest='homol',
                        default=False,
                        action='store_true',
                        help='Run server in homologation mode')
    parser.add_argument('-p', '--prod',
                        dest='prod',
                        default=False,
                        action='store_true',
                        help='Run server in production mode')
    parser.add_argument('-debug', '--debug',
                        dest='debug',
                        default=False,
                        action='store_true',
                        help='Enable debug mode')
    parser.add_argument('-s', '--swagger',
                        dest='swagger',
                        action='store_true',
                        default=False,
                        help='Load Swagger')
    parser.add_argument('-i', '--instances',
                        dest='instances',
                        action='store',
                        default=0,
                        type=int,
                        help='Number of instances')

    args = parser.parse_args()

    # Solicita novamente ao usuario como deve ser chamado o script e os parametros necessarios
    if (not args.devel and not args.prod and not args.homol) or (args.devel + args.homol + args.prod >= 2):
        parser.print_help()
        exit(0)

    try:
        main(args.devel, args.homol, args.prod, args.debug, args.swagger, args.instances)
    except Exception as e:
        print(e)
    # except KeyboardInterrupt:
    #     slog.info('stoping...')
    #     server.stop()
    #     tornado.ioloop.IOLoop().instance().stop()
    #     tornado.ioloop.IOLoop().instance().add_callback_from_signal(tornado.ioloop.IOLoop().instance().stop)
    #     tornado.ioloop.IOLoop().instance().add_callback(tornado.ioloop.IOLoop().instance().stop)
    #     tornado.ioloop.IOLoop().instance().add_callback(server.stop)
