# -*- coding: utf-8 -*-
#
# FSVAS
#
from urllib.parse import quote
import requests
import json
import re
import datetime

# Classe de provisionaonamento
from provisioner.v2 import Provisioner


class Anchorfree(Provisioner):

    def requestRest(self, method, urlRestBase):

        self.log.info('%s[REQUEST - %s in %s]' % (self.msgLog, method, urlRestBase))
        # Pega o access_token para usar a api
        data = dict(access_token=self.getToken())
        # remove o token do put
        data.update(self.myFields)
        # methodo para verificar os campos obrigatorios do methodo do vendors
        self.utils.requiredFields(self, self.paramRequiredField, self.paramOptionalsField, data.keys())

        self.log.debug('%s[REQUEST FIELDS: %s]' % (self.msgLog, self.myFields))
        try:
            if method == 'POST':
                r = requests.post(urlRestBase, data=data, timeout=self.timeOut)
            elif method == 'DELETE':
                r = requests.delete(urlRestBase, params=data, timeout=self.timeOut)
            elif method == 'GET':
                r = requests.get(urlRestBase, params=data, timeout=self.timeOut)
            elif method == 'PUT':
                r = requests.put(urlRestBase, timeout=self.timeOut)

            self.log.debug('%s[%s][%s]' % (self.msgLog, r.status_code, r.text))
        except Exception as e:
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['vendorDbError']['code'],
                str(e))

        code = ""
        message = self.appConfig['statusCode']['vendorError']['message']

        # log final como info
        logLevel = 2

        if r.status_code == 200:
            try:
                request = json.loads(r.text)
            except:
                request['result'] = ""

            if request['result'] != 'OK':
                if request['result'] == 'NOT_FOUND':
                    if self.typeVendor == 'licenses':
                        code = self.appConfig['statusCode']['licenseNotFound']['code']
                        message = self.appConfig['statusCode']['licenseNotFound']['message']
                    elif self.typeVendor == 'devices':
                        code = self.appConfig['statusCode']['deviceNotFound']['code']
                        message = self.appConfig['statusCode']['deviceNotFound']['message']

                elif request['result'] == 'USER_ALREADY_EXISTS':
                    code = self.appConfig['statusCode']['userAlreadyExiste']['code']
                    message = self.appConfig['statusCode']['userAlreadyExiste']['message']
                else:
                    message = request['result']
            else:
                # adiciona um return OK
                dictReturn = {'return': 'OK', 'data': {}}

                # pega o user_id do cadastro
                if 'user_id' in request:
                    dictReturn['data']['user_id'] = request['user_id']

                # pega as licensas
                if 'licenses' in request:
                    dictReturn['data']['licenses'] = request['licenses']

                # pega os devices
                if 'devices' in request:
                    dictReturn['data']['devices'] = request['devices']

                # pega os device
                if 'device' in request:
                    dictReturn['data']['device'] = request['device']

                # pega os session
                if 'sessions' in request:
                    dictReturn['data']['sessions'] = request['sessions']

                # pega os subscribers
                if 'subscribers' in request or 'subscriber' in request:
                    # Se nao encontrou o usuario, retorn um erro
                    if not request['subscribers']:
                        code = self.appConfig['statusCode']['userNotFound']['code']
                        message = self.appConfig['statusCode']['userNotFound']['message']
                    else:
                        dictReturn['data']['subscribers'] = request['subscribers']

                if not code:
                    return dictReturn

        raise self.utils.BaseExceptionError(
            code if code else self.appConfig['statusCode']['vendorError']['code'],
            message,
            r.status_code,
            r.text,
            logLevel)
    #
    # Funcao para listar um cliente pelo id
    # resquest de Retorno de sucesso
    # 200 - {id, name, bundle, active_devices, locale, carrier_id, condition, registration_time,connection_time}
    # GET
    # resquest de Retorno de erros
    # 400 - Bad request
    # 401 - unauthorized
    # 5xx - internal error
    ##
    # paramentros adicionais
    # Page number from 0 to N
    # size number page size

    def getProvisioning(self):

        if not self.mainId or not re.match("^[A-Za-z0-9]*$", self.mainId):
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyA']['code'],
                self.appConfig['statusCode']['invalidKeyA']['message'])

        return self.requestRest('GET', '%ssubscribers/extref/%s' % (self.urlRestBase, self.mainId))

    #
    # Funcao para incluir clientes
    # resquest de Retorno de sucesso
    # 200 - {id: 'user_id', 'status': xxx}
    # POST
    # resquest de Retorno de erros
    # 401 - Acesso negado
    # 400 - bad request - parametro invalido
    # 500 - erro generico
    def postProvisioning(self):

        if self.mainId and re.match("^[A-Za-z0-9]*$", self.mainId):
            self.myFields['extref'] = self.mainId
        else:
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyA']['code'],
                self.appConfig['statusCode']['invalidKeyA']['message'])

        return self.requestRest('POST', '%ssubscribers/' % (self.urlRestBase))

    # Funcao para atualizar pedidos de clientes
    # POST
    # resquest de Retorno de sucesso
    # 200 - {'status': xxx}
    # PUT
    # resquest de Retorno de erros
    # 401 - Acesso negado
    # 400 - bad request - parametro invalido
    # 500 - erro generico
    def putProvisioning(self):

        if not self.mainId or not re.match("^[A-Za-z0-9]*$", self.mainId):
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyA']['code'],
                self.appConfig['statusCode']['invalidKeyA']['message'])

        if 'enabled' in self.myFields:
            self.myFields['condition'] = '0' if self.myFields['enabled'] == '1' else '1'
            del self.myFields['enabled']

        getUser = self.requestRest('GET', '%ssubscribers/extref/%s' % (self.urlRestBase, self.mainId))

        if 'data' in getUser:
            # Transforma os valores em url
            params = ""
            for args in self.myFields:
                params += '&{}={}'.format(args, self.myFields[args])

            return self.requestRest(
                'PUT',
                '%ssubscribers/%s?access_token=%s%s' % (self.urlRestBase, getUser['data']['subscribers'][0]['id'], self.getToken(), params))
        else:
            return getUser

    # Funcao para deletar clientes
    # resquest de Retorno de sucesso
    # 200 {'status': xxx}
    # DELETE
    # resquest de Retorno de erros
    # 401 - Acesso negado
    # 400 - bad request - parametro invalido
    # 500 - erro generico
    def deleteProvisioning(self):

        if self.mainId and not re.match("^[A-Za-z0-9]*$", self.mainId):
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyA']['code'],
                self.appConfig['statusCode']['invalidKeyA']['message'])

        getUser = self.requestRest('GET', '%ssubscribers/extref/%s' % (self.urlRestBase, self.mainId))

        if 'data' in getUser:
            return self.requestRest('DELETE', '%ssubscribers/%s' % (self.urlRestBase, getUser['data']['subscribers'][0]['id']))
        else:
            return getUser

    #
    # Licenses
    #

    #
    # Funcao para listar todos os roles disponiveis
    # GET
    ##
    def getRoles(self):

        return self.requestRest('GET', '%slicenses' % (self.urlRestBase))

    #
    # Funcao para adicionar uma licensa ao usuario
    # resquest de Retorno de sucesso
    # 200 - {}
    # POST
    ##
    def postLicenses(self):

        return self.requestRest('POST', '%slicenses' % (self.urlRestBase))

    #
    # Funcao para adicionar uma licensa ao usuario
    # resquest de Retorno de sucesso
    # 200 - {}
    # PUT
    ##
    def putLicenses(self):

        if self.mainId and not re.match("^[0-9]*$", self.mainId):
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyD']['code'],
                self.appConfig['statusCode']['invalidKeyD']['message'])

        # Transforma os valores em url
        params = ""
        for args in self.myFields:
            params += '&{}={}'.format(args, quote(self.myFields[args]))

        return self.requestRest(
            'PUT',
            '%slicenses/%s?access_token=%s%s' % (self.urlRestBase, self.mainId, self.getToken(), params))

    #
    # DEVICES #
    #

    def getDevices(self):

        if not self.mainId or not re.match("^[A-Za-z0-9]*$", self.mainId):
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyA']['code'],
                self.appConfig['statusCode']['invalidKeyA']['message'])

        getUser = self.requestRest('GET', '%ssubscribers/extref/%s' % (self.urlRestBase, self.mainId))

        if 'data' in getUser:
            return self.requestRest(
                'GET',
                '%ssubscribers/%s/devices' % (self.urlRestBase, getUser['data']['subscribers'][0]['id']))
        else:
            return getUser

    def deleteDevices(self):

        if not self.mainId or not re.match("^[A-Za-z0-9]*$", self.mainId):
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyA']['code'],
                self.appConfig['statusCode']['invalidKeyA']['message'])

        getUser = self.requestRest('GET', '%ssubscribers/extref/%s' % (self.urlRestBase, self.mainId))

        if 'data' in getUser:
            return self.requestRest(
                'DELETE',
                '%ssubscribers/%s/devices/%s' % (self.urlRestBase, getUser['data']['subscribers'][0]['id'], self.myFields['device_id']))
        else:
            return getUser

    #
    # TOKEN #
    #
    def getToken(self):

        # Session para armazenar o token por 24 horas
        if ((self.operator not in self.sess.keys()) or (self.vendor not in self.sess[self.operator].keys()))\
           or (self.sess[self.operator][self.vendor]['expire_at'] <= datetime.datetime.now()):

            self.log.debug('%s Create new Token' % (self.msgLog))

            try:
                r = requests.post(
                    '%slogin' % self.urlRestBase,
                    data=dict(login=self.loginRest, password=self.senhaRest), timeout=self.timeOut)
                request = json.loads(r.text)
                if r.status_code == 200 or not r.text:
                    self.sess[self.operator][self.vendor] = {
                        'token': request['access_token'],
                        'expire_at': datetime.datetime.now() + datetime.timedelta(hours=23)}

                    return self.sess[self.operator][self.vendor]['token']
                else:
                    raise self.utils.BaseExceptionError(
                        self.appConfig['statusCode']['getToken']['code'],
                        self.appConfig['statusCode']['getToken']['message'],
                        r.status_code,
                        r.text)
            except Exception as e:
                raise self.utils.BaseExceptionError(
                    self.appConfig['statusCode']['vendorDbError']['code'],
                    str(e))

        else:
            self.log.debug('%s Use old Token - expire_at(%s) <= now(%s)' % (
                self.msgLog,
                self.sess[self.operator][self.vendor]['expire_at'].strftime("%Y-%m-%d %H:%M"),
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
            return self.sess[self.operator][self.vendor]['token']

    def status(self):

        return self.requestRest('GET', '%ssubscribers/extref/1' % (self.urlRestBase))
