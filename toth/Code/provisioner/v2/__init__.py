# -*- coding: utf-8 -*-
#
# FSVAS
#

import logging

# Tornado
import tornado.ioloop
import tornado.web
import tornado.escape
from tornado import escape
from tornado import httputil
import time
import chardet
#import auth


#@auth.httpauth
class Provisioner(tornado.web.RequestHandler):

    def initialize(self, **kwargs):
        for var in kwargs:
            setattr(self, var, kwargs[var])

    def write_error(self, status_code, **kwargs):
        """ Funcao para gerar os errors """

        writeReturn = dict(status=int(status_code), reason=kwargs['_reason'])
        if 'status_vendor' in kwargs.keys() and kwargs['status_vendor']:
            writeReturn['status_vendor'] = kwargs['status_vendor']
        if 'reason_vendor' in kwargs.keys() and kwargs['reason_vendor']:
            writeReturn['reason_vendor'] = kwargs['reason_vendor']
        self.clear()
        self.set_status(status_code)
        self.finish(writeReturn)

    # Prepare - possui as criticas do Provisionador
    def prepare(self):
        # Atualiza o log
        self.slog = self.utils.setup_logger(
            'tornado_oauthlib',
            logging.DEBUG if self.debug else logging.INFO,
            True if self.level == 'devel' else None)
        # Cria o log por operadora
        self.log = self.utils.setup_logger(
            self.operator,
            logging.DEBUG if self.debug else logging.INFO,
            True if self.level == 'devel' else None)

        # Cria um para o log
        self.idLog = str(time.time()).replace('.', '')

        # conteudo do log em caso de erro
        self.msgLog = '[%s][%s][%s][%s]' % (
            self.request.path.split('/')[-1],
            self.operator,
            self.vendor,
            self.idLog)

        if 'Auth' in self.request.headers.keys():
            self.msgLog = '%s[%s - %s]' % (self.msgLog, self.request.headers['Auth']['login'], self.request.headers['Auth']['operator'])

        # pega as exceptions customizadas
        try:
            # pega as configurcoes apenas da operadora
            self.operatorConf = self.appConfig['operators'][self.operator]

            # cria uma sessao para cada operadora
            if self.operator not in self.sess.keys():
                self.sess[self.operator] = dict()

            # Cria a variavel de fields
            self.myFields = dict()

            # pega o methodo do conf
            # vendors/vendedor/tipodeacao/methodo
            self.methods = self.appConfig['vendors'][self.provisionerVersion][self.vendor][self.typeVendor]

            # Se nao existir o metodo para o tipo do vendor, erro
            if self.request.method.lower() not in self.methods:
                self.msgLogAttr = '[%s][%s][%s][%s]' % (
                    self.request.method,
                    self.request.uri,
                    self.request.remote_ip,
                    self.request.arguments)

                # logo de inicio da requisicao
                self.log.info('===INIT %s%s' % (self.msgLog, self.msgLogAttr))

                raise self.utils.BaseExceptionError(
                    self.appConfig['statusCode']['methodNotFound']['code'],
                    '%s %s' % (self.appConfig['statusCode']['methodNotFound']['message'], self.request.method.lower()))
            else:
                # Pega todas as funcoes desse methodo
                methods = self.methods[self.request.method.lower()]

                # pega os campos required da funcao
                self.getRequiredFields = methods

                # pega os campos required da funcao
                self.paramRequiredField = methods[methods.keys()[0]]
                self.paramOptionalsField = methods[methods.keys()[1]]

                # Chama o methodo pegando o nome dele no arquivo de conf
                # O methodo precisa estar nesse arquivo com o mesmo nome
                self.method = methods.keys()[0]

                self.msgLogAttr = '[%s][%s][%s][%s][%s]' % (
                    self.request.method,
                    self.request.uri,
                    self.request.remote_ip,
                    self.method,
                    self.request.arguments)

            # logo de inicio da requisicao
            self.log.info('===INIT %s%s' % (self.msgLog, self.msgLogAttr))

            # Os parametros vem como byte
            for args in self.request.arguments:
                char = chardet.detect(self.request.arguments[args][0])

                if ('encoding' in char and char['encoding']) and 'ISO' in char['encoding']:
                    self.myFields[args] = self.request.arguments[args][0].decode(char['encoding'])
                else:
                    self.myFields[args] = self.request.arguments[args][0].decode()

            self.log.info('%s[FIELDS: %s]' % (self.msgLog, self.myFields))

            # Importa o provisionador pela versao
            if self.provisionerVersion not in self.appConfig['versions']['available']:
                raise self.utils.BaseExceptionError(
                    self.appConfig['statusCode']['importError']['code'],
                    self.appConfig['statusCode']['provisionerVersion']['message'])

            # Verifica se vendor tem conf no ini
            if self.vendor not in self.appConfig['vendors'][self.provisionerVersion]:
                raise self.utils.BaseExceptionError(
                    self.appConfig['statusCode']['vendorIniError']['code'],
                    self.appConfig['statusCode']['vendorIniError']['message'])

            # Url base do rest do vendor
            if 'urlBase' in self.appConfig['operators'][self.operator]['vendors'][self.provisionerVersion][self.vendor].keys():
                self.urlRestBase = \
                    self.appConfig['operators'][self.operator]['vendors'][self.provisionerVersion][self.vendor]['urlBase']

            # Timeout para o request nos vendors
            if 'timeOut' in self.appConfig['operators'][self.operator]['vendors'][self.provisionerVersion][self.vendor].keys():
                self.timeOut = \
                    int(self.appConfig['operators'][self.operator]['vendors'][self.provisionerVersion][self.vendor]['timeOut'])

            # Login do rest do vendor
            if 'loginRest' in self.appConfig['operators'][self.operator]['vendors'][self.provisionerVersion][self.vendor]:
                self.loginRest, self.senhaRest = tuple(
                    self.appConfig['operators'][self.operator]['vendors'][self.provisionerVersion][self.vendor]['loginRest'])

            # Nome do arquivo wsdl para log
            if 'urlWsdl' in self.appConfig['operators'][self.operator]['vendors'][self.provisionerVersion][self.vendor]:
                self.urlWsdl = self.appConfig['operators'][self.operator]['vendors'][self.provisionerVersion][self.vendor]['urlWsdl']

        except self.utils.BaseExceptionError as e:
            if e.realCodeException and e.realErrorException:
                msgLogException = '%s[%s] - [%s]\r\n%s\r\n' % (self.msgLog, e.realCodeException, e.realErrorException, self.msgLogAttr)
            else:
                msgLogException = '%s[%s] - [%s]\r\n%s\r\n' % (self.msgLog, e.codeException, e.errorException, self.msgLogAttr)

            if e.logLevel == 1:
                self.slog.error(msgLogException)
            elif e.logLevel == 2:
                self.slog.info(msgLogException)
            else:
                self.slog.debug(msgLogException)

            # Log para a operadora
            self.log.error('%s[%s] - [%s]\r\n%s' % (self.msgLog, e.realCodeException, e.realErrorException, self.msgLogAttr))
            self.log.error('%s[%s] - [%s]\r\n%s' % (self.msgLog, e.codeException, e.errorException, self.msgLogAttr))

            self.send_error(e.codeException, _reason=e.errorException)
            self.log.info('===FINISH %s%s\r\n' % (self.msgLog, self.msgLogAttr))

        except Exception as e:
            if hasattr(self, 'log'):
                self.log.error('%s - [%s %s]\r\n%s\r\n' % (self.msgLog, type(e), str(e), self.msgLogAttr))
            self.slog.error('%s - [%s %s]\r\n%s\r\n' % (self.msgLog, type(e), str(e), self.msgLogAttr))
            self.send_error(self.appConfig['statusCode']['genericError']['code'], _reason='%s %s' % (type(e), str(e)))
            self.log.info('===FINISH %s%s\r\n' % (self.msgLog, self.msgLogAttr))

    def set_status(self, status_code, reason=None):
        """Sets the status code for our response.

        :arg int status_code: Response status code. If ``reason`` is ``None``,
            it must be present in `httplib.responses <http.client.responses>`.
        :arg string reason: Human-readable reason phrase describing the status
            code. If ``None``, it will be filled in from
            `httplib.responses <http.client.responses>`.
        """
        # Indice em INT
        status_code = int(status_code)

        confs = httputil.responses
        for key in self.appConfig['statusCode']:
            confs[int(self.appConfig['statusCode'][key]['code'])] = self.appConfig['statusCode'][key]['message']

        self._status_code = status_code
        if reason is not None:
            self._reason = escape.native_str(reason)
        else:
            try:
                self._reason = confs[status_code]
            except KeyError:
                raise ValueError('unknown status code %d', status_code)

    def get(self, mainId, subMainId=None):
        try:
            # Pega os Id principais
            self.mainId = mainId
            # Pega os Id principais
            self.subMainId = subMainId
            # Metodo para pegar a real funcao no config
            self.clear()
            self.finish(getattr(self, self.method)())

        except self.utils.BaseExceptionError as e:
            if e.realCodeException and e.realErrorException:
                msgLogException = '%s[%s] - [%s]\r\n%s\r\n' % (self.msgLog, e.realCodeException, e.realErrorException, self.msgLogAttr)
            else:
                msgLogException = '%s[%s] - [%s]\r\n%s\r\n' % (self.msgLog, e.codeException, e.errorException, self.msgLogAttr)

            if e.logLevel == 1:
                self.slog.error(msgLogException)
            elif e.logLevel == 2:
                self.slog.info(msgLogException)
            else:
                self.slog.debug(msgLogException)

            # Log para a operadora
            self.log.error('%s[%s] - [%s]\r\n%s' % (self.msgLog, e.realCodeException, e.realErrorException, self.msgLogAttr))
            self.log.error('%s[%s] - [%s]\r\n%s' % (self.msgLog, e.codeException, e.errorException, self.msgLogAttr))
            self.send_error(e.codeException, _reason=e.errorException, reason_vendor=e.realErrorException, status_vendor=e.realCodeException)
        except Exception as e:
            if hasattr(self, 'log'):
                self.log.error('%s - [%s %s]\r\n%s\r\n' % (self.msgLog, type(e), str(e), self.msgLogAttr))
            self.slog.error('%s - [%s %s]\r\n%s\r\n' % (self.msgLog, type(e), str(e), self.msgLogAttr))
            self.send_error(
                self.appConfig['statusCode']['genericError']['code'],
                _reason='%s %s' % (type(e), str(e)))

        # Loga no log da operadora o final da chamada
        self.log.info('===FINISH %s%s\r\n' % (self.msgLog, self.msgLogAttr))

    def post(self, mainId, subMainId=None):
        try:
            # Pega os Id principais
            self.mainId = mainId
            # Pega os Id principais
            self.subMainId = subMainId
            # Metodo para pegar a real funcao no config
            self.clear()
            self.finish(getattr(self, self.method)())

        except self.utils.BaseExceptionError as e:
            if e.realCodeException and e.realErrorException:
                msgLogException = '%s[%s] - [%s]\r\n%s\r\n' % (self.msgLog, e.realCodeException, e.realErrorException, self.msgLogAttr)
            else:
                msgLogException = '%s[%s] - [%s]\r\n%s\r\n' % (self.msgLog, e.codeException, e.errorException, self.msgLogAttr)

            if e.logLevel == 1:
                self.slog.error(msgLogException)
            elif e.logLevel == 2:
                self.slog.info(msgLogException)
            else:
                self.slog.debug(msgLogException)

            # Log para a operadora
            self.log.error('%s[%s] - [%s]\r\n%s' % (self.msgLog, e.realCodeException, e.realErrorException, self.msgLogAttr))
            self.log.error('%s[%s] - [%s]\r\n%s' % (self.msgLog, e.codeException, e.errorException, self.msgLogAttr))
            self.send_error(e.codeException, _reason=e.errorException, reason_vendor=e.realErrorException, status_vendor=e.realCodeException)
        except Exception as e:
            if hasattr(self, 'log'):
                self.log.error('%s - [%s %s]\r\n%s\r\n' % (self.msgLog, type(e), str(e), self.msgLogAttr))
            self.slog.error('%s - [%s %s]\r\n%s\r\n' % (self.msgLog, type(e), str(e), self.msgLogAttr))
            self.send_error(
                self.appConfig['statusCode']['genericError']['code'],
                _reason='%s %s' % (type(e), str(e)))

        # Loga no log da operadora o final da chamada
        self.log.info('===FINISH %s%s\r\n' % (self.msgLog, self.msgLogAttr))

    def put(self, mainId, subMainId=None):
        try:
            # Pega os Id principais
            self.mainId = mainId
            # Pega os Id principais
            self.subMainId = subMainId
            # Metodo para pegar a real funcao no config
            self.clear()
            self.finish(getattr(self, self.method)())

        except self.utils.BaseExceptionError as e:
            if e.realCodeException and e.realErrorException:
                msgLogException = '%s[%s] - [%s]\r\n%s\r\n' % (self.msgLog, e.realCodeException, e.realErrorException, self.msgLogAttr)
            else:
                msgLogException = '%s[%s] - [%s]\r\n%s\r\n' % (self.msgLog, e.codeException, e.errorException, self.msgLogAttr)

            if e.logLevel == 1:
                self.slog.error(msgLogException)
            elif e.logLevel == 2:
                self.slog.info(msgLogException)
            else:
                self.slog.debug(msgLogException)

            # Log para a operadora
            self.log.error('%s[%s] - [%s]\r\n%s' % (self.msgLog, e.realCodeException, e.realErrorException, self.msgLogAttr))
            self.log.error('%s[%s] - [%s]\r\n%s' % (self.msgLog, e.codeException, e.errorException, self.msgLogAttr))
            self.send_error(e.codeException, _reason=e.errorException, reason_vendor=e.realErrorException, status_vendor=e.realCodeException)
        except Exception as e:
            if hasattr(self, 'log'):
                self.log.error('%s - [%s %s]\r\n%s\r\n' % (self.msgLog, type(e), str(e), self.msgLogAttr))
            self.slog.error('%s - [%s %s]\r\n%s\r\n' % (self.msgLog, type(e), str(e), self.msgLogAttr))
            self.send_error(
                self.appConfig['statusCode']['genericError']['code'],
                _reason='%s %s' % (type(e), str(e)))

        # Loga no log da operadora o final da chamada
        self.log.info('===FINISH %s%s\r\n' % (self.msgLog, self.msgLogAttr))

    def delete(self, mainId, subMainId=None):
        try:
            # Pega os Id principais
            self.mainId = mainId
            # Pega os Id principais
            self.subMainId = subMainId
            # Metodo para pegar a real funcao no config
            self.clear()
            self.finish(getattr(self, self.method)())

        except self.utils.BaseExceptionError as e:
            if e.realCodeException and e.realErrorException:
                msgLogException = '%s[%s] - [%s]\r\n%s\r\n' % (self.msgLog, e.realCodeException, e.realErrorException, self.msgLogAttr)
            else:
                msgLogException = '%s[%s] - [%s]\r\n%s\r\n' % (self.msgLog, e.codeException, e.errorException, self.msgLogAttr)

            if e.logLevel == 1:
                self.slog.error(msgLogException)
            elif e.logLevel == 2:
                self.slog.info(msgLogException)
            else:
                self.slog.debug(msgLogException)

            # Log para a operadora
            self.log.error('%s[%s] - [%s]\r\n%s' % (self.msgLog, e.realCodeException, e.realErrorException, self.msgLogAttr))
            self.log.error('%s[%s] - [%s]\r\n%s' % (self.msgLog, e.codeException, e.errorException, self.msgLogAttr))
            self.send_error(e.codeException, _reason=e.errorException, reason_vendor=e.realErrorException, status_vendor=e.realCodeException)
        except Exception as e:
            if hasattr(self, 'log'):
                self.log.error('%s - [%s %s]\r\n%s\r\n' % (self.msgLog, type(e), str(e), self.msgLogAttr))
            self.slog.error('%s - [%s %s]\r\n%s\r\n' % (self.msgLog, type(e), str(e), self.msgLogAttr))
            self.send_error(
                self.appConfig['statusCode']['genericError']['code'],
                _reason='%s %s' % (type(e), str(e)))

        # Loga no log da operadora o final da chamada
        self.log.info('===FINISH %s%s\r\n' % (self.msgLog, self.msgLogAttr))
