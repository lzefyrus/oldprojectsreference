# -*- coding: utf-8 -*-
#
# FSVAS
#
import requests
import json
import re

# Classe de provisionaonamento
from provisioner.v2 import Provisioner


class Assistencia(Provisioner):

    def requestRest(self, method, urlRestBase):

        self.log.info('%s[REQUEST - %s in %s]' % (self.msgLog, method, urlRestBase))

        # methodo para verificar os campos obrigatorios do methodo do vendors
        self.utils.requiredFields(self, self.paramRequiredField, self.paramOptionalsField, self.myFields.keys())
        self.log.debug('%s[REQUEST FIELDS: %s]' % (self.msgLog, self.myFields))
        dados = json.dumps(self.myFields)
        header = {'content-type': 'application/json', 'user': self.loginRest, 'password': self.senhaRest}

        try:
            if method == 'POST':
                r = requests.post(urlRestBase, data=dados, headers=header, timeout=self.timeOut)
            elif method == 'DELETE':
                r = requests.delete(urlRestBase, params=dados, headers=header, timeout=self.timeOut)
            elif method == 'GET':
                r = requests.get(urlRestBase, params=dados, headers=header, timeout=self.timeOut)
            elif method == 'PUT':
                r = requests.put(urlRestBase, data=dados, headers=header, timeout=self.timeOut)

            self.log.debug('%s[%s] - %s' % (self.msgLog, r.status_code, r.text))

        except Exception as e:
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['vendorDbError']['code'],
                str(e))

        if r.status_code in [200, 201, 202]:
            return {'return': 'OK', 'data': {}, 'status': 200}
        else:
            # log final como info
            logLevel = 1

            try:
                request = json.loads(r.text)
                msg = ''
                if 'name' in request:
                    msg += request['name']
                if 'message' in request:
                    msg += ' - %s' % (request['message'])
                if 'description' in request:
                    msg += ' - %s' % (request['description'])
                message = msg
            except:
                message = self.appConfig['statusCode']['vendorError']['message']

            code = self.appConfig['statusCode']['vendorError']['code']

            if r.status_code == 725:
                logLevel = 2
                code = self.appConfig['statusCode']['saleAlready']['code']
                message = self.appConfig['statusCode']['saleAlready']['message']
            if r.status_code == 731:
                logLevel = 2
                code = self.appConfig['statusCode']['docsNotInformed']['code']
                message = self.appConfig['statusCode']['docsNotInformed']['message']
            if r.status_code == 726:
                logLevel = 2
                code = self.appConfig['statusCode']['saleNotFound']['code']
                message = self.appConfig['statusCode']['saleNotFound']['message']
            if r.status_code == 703:
                logLevel = 2
                code = self.appConfig['statusCode']['productNotFound']['code']
                message = self.appConfig['statusCode']['productNotFound']['message']
            if r.status_code == 736:
                logLevel = 2
                code = self.appConfig['statusCode']['CannotUnblockACanceledSale']['code']
                message = self.appConfig['statusCode']['CannotUnblockACanceledSale']['message']
            if r.status_code == 737:
                logLevel = 2
                code = self.appConfig['statusCode']['SaleAlreadyActive']['code']
                message = self.appConfig['statusCode']['SaleAlreadyActive']['message']

        raise self.utils.BaseExceptionError(
            code,
            message,
            r.status_code,
            r.text,
            logLevel)

    #
    # Funcao para incluir clientes
    # resquest de Retorno de erros
    # 412 Precondition Failed Campos obrigatórios não informados  {"message":"Informe o número de telefone ou documento","sucess":false}
    # 201 Created Criação de venda com sucesso    {"sucess":true}
    # 500 Internal Server Error   Erro interno no Backend {"message":"Erro ao salvar dados da venda: Venda já cadastrada","sucess":false}
    def postProvisioning(self):

        if self.mainId and re.match("^[A-Za-z0-9]*$", self.mainId):
            self.myFields['key'] = self.mainId
        else:
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyA']['code'],
                self.appConfig['statusCode']['invalidKeyA']['message'])

        if 'partner' not in self.myFields.keys():
            self.myFields['partner'] = self.operator

        return self.requestRest('PUT', '%screate' % (self.urlRestBase))

    #
    # Funcao para bloquear/desbloquear clientes
    # resquest de Retorno de erros
    # 412 Precondition Failed Campos obrigatórios não informados  {"message":" Informe a chave","sucess":false}
    # 202 Accepted    Bloqueio com sucesso    {"sucess":true}
    # 500 Internal Server Error   Erro interno no Backend {"message":"Erro ao salvar dados da venda: Venda já cadastrada","sucess":false}
    def putProvisioning(self):

        if self.mainId and re.match("^[A-Za-z0-9]*$", self.mainId):
            self.myFields['key'] = self.mainId
        else:
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyA']['code'],
                self.appConfig['statusCode']['invalidKeyA']['message'])

        self.myFields['partner'] = self.operator

        if 'enabled' in self.myFields and not int(self.myFields['enabled']):
            return self.requestRest('POST', '%sblock' % (self.urlRestBase))
        else:
            return self.requestRest('POST', '%sunblock' % (self.urlRestBase))

    #
    # Funcao para deletar clientes
    # resquest de Retorno de erros
    # 412 Precondition Failed Campos obrigatórios não informados  {"message":" Informe a chave","sucess":false}
    # 202 Accepted    Cancelamento com sucesso    {"sucess":true}
    # 500 Internal Server Error   Erro interno no Backend {"message":"Erro ao salvar dados da venda: Venda já cadastrada","sucess":false}
    def deleteProvisioning(self):

        if self.mainId and re.match("^[A-Za-z0-9]*$", self.mainId):
            self.myFields['key'] = self.mainId
        else:
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyA']['code'],
                self.appConfig['statusCode']['invalidKeyA']['message'])

        self.myFields['partner'] = self.operator

        return self.requestRest('POST', '%scancel' % (self.urlRestBase))

    def status(self):

        return self.requestRest('GET', '%s' % (self.appConfig['operators'][self.operator]['vendors'][self.provisionerVersion][self.vendor]['urlBaseTest']))
