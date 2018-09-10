# -*- coding: utf-8 -*-
#
# FSVAS
#
import urllib3
import json
import re

# Classe de provisionaonamento
from provisioner.v2 import Provisioner


class Fsecure(Provisioner):

    def requestRest(self, method, urlRestBase, myFields=None):

        # Se passou algum campo via parametro altera os valores
        if myFields:
            data = myFields
        else:
            data = self.myFields

        self.log.info('%s[REQUEST - %s in %s]' % (self.msgLog, method, urlRestBase))

        # methodo para verificar os campos obrigatorios do methodo do vendors
        self.utils.requiredFields(self, self.paramRequiredField, self.paramOptionalsField, data.keys())
        self.log.debug('%s[REQUEST FIELDS: %s]' % (self.msgLog, data))
        try:
            # Desabilitar warnings
            urllib3.disable_warnings()
            http = urllib3.PoolManager(retries=1, timeout=self.timeOut)

            if 'fs' in data:
                del data['fs']

            r = http.request(
                method,
                urlRestBase,
                fields=data,
                headers=urllib3.util.make_headers(basic_auth='%s:%s' % (self.loginRest, self.senhaRest)))
            requestData = r.data.decode()
            r.close()
            self.log.debug('%s[%s] - %s' % (self.msgLog, r.status, requestData))

        except Exception as e:
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['vendorDbError']['code'],
                str(e))

        data = ''
        message = self.appConfig['statusCode']['vendorError']['message']
        code = self.appConfig['statusCode']['vendorDbError']['code']
        logLevel = 1

        try:
            request = json.loads(requestData)
        except:
            request = ""

        if request:
            data = request['data']
            if 'error' in request and request['error']:
                # Loop para conseguir recuperar o erro da versao 2.0 e 3.0
                if 'message' not in request['error']:
                    for msg in request['error']:
                        message = request['error'][msg]
                else:
                    message = request['error']['message']
                if ('code' in request['error'].keys() and 'does_not_exist' in request['error']['code']) or ('does_not_exist' in request['error'].keys()):
                    if 'Customer' in request['error']['message']:
                        code = self.appConfig['statusCode']['userNotFound']['code']
                        message = self.appConfig['statusCode']['userNotFound']['message']
                    elif 'Product' in request['error']['message']:
                        code = self.appConfig['statusCode']['licenseNotFound']['code']
                        message = self.appConfig['statusCode']['licenseNotFound']['message']

                    logLevel = 2

                if ('code' in request['error'].keys() and 'already_exists' in request['error']['code']) or ('already_exists' in request['error'].keys()):
                    code = self.appConfig['statusCode']['userAlreadyExiste']['code']
                    message = self.appConfig['statusCode']['userAlreadyExiste']['message']
                    logLevel = 2

        if r.status == 200:
            return {'return': 'OK', 'data': data}
        elif r.status == 400:
            code = self.appConfig['statusCode']['badRequest']['code']
            logLevel = 2

        raise self.utils.BaseExceptionError(
            code,
            message,
            r.status,
            requestData,
            logLevel)

    #
    # CUSTOMER #
    #

    #
    # Funcao para listar um cliente pelo id
    # GET
    # resquest de Retorno de erros
    # 400 - Bad request
    # 401 - unauthorized
    # 5xx - internal error
    ##

    def getProvisioning(self):

        if self.mainId and re.match("^[A-Za-z0-9@_\-.]*$", self.mainId):
            self.myFields['extref'] = self.mainId
        else:
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyE']['code'],
                self.appConfig['statusCode']['invalidKeyE']['message'])

        return self.requestRest('GET', '%sget_customer' % (self.urlRestBase))

    #
    # Funcao para incluir customers
    # POST
    # resquest de Retorno de erros
    # 401 - Acesso negado
    # 400 - bad request - parametro invalido
    # 500 - erro generico
    #
    def postProvisioning(self):

        if self.mainId and re.match("^[A-Za-z0-9@_\-.]*$", self.mainId):
            self.myFields['extref'] = self.mainId
        else:
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyE']['code'],
                self.appConfig['statusCode']['invalidKeyE']['message'])

        # dados pre definidos
        if 'send_email' not in self.myFields:
            self.myFields['send_email'] = 0

        if 'last_name' not in self.myFields.keys():
            self.myFields['last_name'] = self.mainId

        return self.requestRest('POST', '%screate_customer' % (self.urlRestBase))

    # Funcao para atualizar pedidos de clientes
    # PUT
    # resquest de Retorno de erros
    # 401 - Acesso negado
    # 400 - bad request - parametro invalido
    # 500 - erro generico
    ##
    def putProvisioning(self):

        if self.mainId and re.match("^[A-Za-z0-9@_\-.]*$", self.mainId):
            self.myFields['extref'] = self.mainId
        else:
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyE']['code'],
                self.appConfig['statusCode']['invalidKeyE']['message'])

        # Necessario algum campo para o update
        if len(self.myFields) <= 1:
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['missingFields']['code'],
                self.appConfig['statusCode']['missingFields']['message'])

        enabled = ""
        response = ""

        if 'enabled' in self.myFields:
            enabled = str(self.myFields['enabled'])
            del self.myFields['enabled']

        # Se enabled = 1 ativa primeiro
        if enabled == '1':
            self.log.debug('%s[Enabled] %s' % (self.msgLog, self.mainId))
            response = self.requestRest('POST', '%sresume_customer' % (self.urlRestBase), dict(extref=self.mainId))

        if len(self.myFields) > 1:
            self.log.debug('%s[Update] %s' % (self.msgLog, self.mainId))
            response = self.requestRest('POST', '%supdate_customer' % (self.urlRestBase))

        # codigo para tentar acertar o bug da fsecure de deletar o uuid do cliente
        if response and\
                ('customer' in response['data'].keys() and ('oneid_uuid' not in response['data']['customer'].keys() or not response['data']['customer']['oneid_uuid'])):
            self.log.error('%s[Erro de uuid] %s' % (self.msgLog, self.mainId))
            response = self.requestRest('POST', '%sname_customer' % (self.urlRestBase), dict(
                extref=self.mainId,
                username=self.mainId,
                email_addr='%s@invalid.com' % (self.mainId),
                first_name=self.mainId,
                last_name=self.mainId,
                send_email=0))

        if enabled == '0':
            self.log.debug('%s[Disabled] %s' % (self.msgLog, self.mainId))
            response = self.requestRest('POST', '%ssuspend_customer' % (self.urlRestBase), dict(extref=self.mainId))

        return response

    # Funcao de suspender o customer
    # GET
    # resquest de Retorno de erros
    # 400 - Bad request
    # 401 - unauthorized
    # 5xx - internal error
    ##
    def deleteProvisioning(self):

        if self.mainId and re.match("^[A-Za-z0-9@_\-.]*$", self.mainId):
            self.myFields['extref'] = self.mainId
        else:
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyE']['code'],
                self.appConfig['statusCode']['invalidKeyE']['message'])

        return self.requestRest('POST', '%ssuspend_customer' % (self.urlRestBase))

    #
    # Funcao para atribuir informacoes ao customer
    # POST
    # resquest de Retorno de erros
    # 401 - Acesso negado
    # 400 - bad request - parametro invalido
    # 500 - erro generico

    def postName(self):

        if self.mainId and re.match("^[A-Za-z0-9@_\-.]*$", self.mainId):
            self.myFields['extref'] = self.mainId
        else:
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyE']['code'],
                self.appConfig['statusCode']['invalidKeyE']['message'])

        # dados pre definidos
        if 'send_email' not in self.myFields:
            self.myFields['send_email'] = 0

        return self.requestRest('POST', '%sname_customer' % (self.urlRestBase))

    #
    # User
    #

    def postUser(self):

        if self.mainId and re.match("^[A-Za-z0-9@_\-.]*$", self.mainId):
            self.myFields['extref'] = self.mainId
        else:
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyE']['code'],
                self.appConfig['statusCode']['invalidKeyE']['message'])

        # dados pre definidos
        if 'locale' not in self.myFields:
            self.myFields['locale'] = 'pt-br'

        return self.requestRest('POST', '%screate_user' % (self.urlRestBase))

    # Funcao de vincular um customer a um usuario
    # Separei os methodos pois cada funcao tem seus erros separados
    # PUT
    # resquest de Retorno de erros
    # 400 - Bad request
    # 401 - unauthorized
    # 5xx - internal error
    ##

    def putUser(self):

        if self.mainId and re.match("^[A-Za-z0-9@_\-.]*$", self.mainId):
            self.myFields['customer_extref'] = self.mainId
        else:
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyE']['code'],
                self.appConfig['statusCode']['invalidKeyE']['message'])

        # dados pre definidos
        if 'send_email' not in self.myFields:
            self.myFields['send_email'] = 0
        if 'send_sms' not in self.myFields:
            self.myFields['send_sms'] = 0

        return self.requestRest('POST', '%sadd_user_to_customer' % (self.urlRestBase))

    # Funcao de desvincular um customer de um usuario
    # DELETE
    # resquest de Retorno de erros
    # 400 - Bad request
    # 401 - unauthorized
    # 5xx - internal error
    ##

    def deleteUser(self):

        if self.mainId and re.match("^[A-Za-z0-9@_\-.]*$", self.mainId):
            self.myFields['customer_extref'] = self.mainId
        else:
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyE']['code'],
                self.appConfig['statusCode']['invalidKeyE']['message'])

        return self.requestRest('POST', '%sremove_user_from_customer' % (self.urlRestBase))
    #
    # Licenses
    #

    #
    # Funcao para recuperar a lista de licencas disponiveis
    # GET
    # resquest de Retorno de erros
    #

    def getRoles(self):

        return self.requestRest('GET', '%sget_product_list' % (self.urlRestBase))

    #
    # Funcao para adicionar uma licensa a um customer
    # POST
    # resquest de Retorno de erros
    # 404 - Not Found
    # 403 - Forbidden
    # 401 - unauthorized
    ##
    def postLicenses(self):

        if self.mainId and re.match("^[A-Za-z0-9@_\-.]*$", self.mainId):
            self.myFields['extref'] = self.mainId
        else:
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyE']['code'],
                self.appConfig['statusCode']['invalidKeyE']['message'])

        return self.requestRest('POST', '%sprovision_license' % (self.urlRestBase))

    #
    # Funcao para remover uma licensa de um customer
    # DELETE
    # resquest de Retorno de erros
    # 404 - Not Found
    # 403 - Forbidden
    # 401 - unauthorized
    # 400 - bad request
    ##
    def deleteLicenses(self):

        if self.mainId and re.match("^[A-Za-z0-9@_\-.]*$", self.mainId):
            self.myFields['extref'] = self.mainId

        else:
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyE']['code'],
                self.appConfig['statusCode']['invalidKeyE']['message'])

        if 'license_uuid' not in self.myFields.keys():
            self.log.debug('%s[Resume cliente] %s' % (self.msgLog, self.myFields['extref']))
            self.requestRest('POST', '%sresume_customer' % (self.urlRestBase), dict(extref=self.myFields['extref']))
            self.log.debug('%s[Update license_size = 0] %s' % (self.msgLog, self.myFields['extref']))
            self.requestRest('POST', '%supdate_customer' % (self.urlRestBase), dict(extref=self.myFields['extref'], license_size=0, force_downgrade=1))
            self.log.debug('%s[Disable user] %s' % (self.msgLog, self.myFields['extref']))
            return self.requestRest('POST', '%ssuspend_customer' % (self.urlRestBase), dict(extref=self.myFields['extref']))

        else:
            self.log.debug('%s[Remove one license] %s' % (self.msgLog, self.mainId))
            return self.requestRest('POST', '%sterminate_license' % (self.urlRestBase))

    #
    # Funcao para atribuir alterar um extref de um cliente
    # POST
    # resquest de Retorno de erros
    # 401 - Acesso negado
    # 400 - bad request - parametro invalido
    # 500 - erro generico

    def postChangeExtref(self):

        if self.mainId and re.match("^[A-Za-z0-9@_\-.]*$", self.mainId):
            self.myFields['extref'] = self.mainId
        else:
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyE']['code'],
                self.appConfig['statusCode']['invalidKeyE']['message'])

        return self.requestRest('POST', '%srename_customer_extref' % (self.urlRestBase))

    def status(self):

        self.myFields['extref'] = '1'
        return self.requestRest('GET', '%sget_customer' % (self.urlRestBase))
