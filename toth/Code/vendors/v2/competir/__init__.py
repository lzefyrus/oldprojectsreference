# -*- coding: utf-8 -*-
#
# FSVAS
#
import requests
import json
import re
import datetime

# Classe de provisionaonamento
from provisioner.v2 import Provisioner


class Competir(Provisioner):

    def requestRest(self, method, urlRestBase):

        self.log.info('%s[REQUEST - %s in %s]' % (self.msgLog, method, urlRestBase))

        # methodo para verificar os campos obrigatorios do methodo do vendors
        self.utils.requiredFields(self, self.paramRequiredField, self.paramOptionalsField, self.myFields.keys())
        self.log.debug('%s[REQUEST FIELDS: %s]' % (self.msgLog, self.myFields))
        try:
            if method == 'POST':
                r = requests.post(urlRestBase, data=self.myFields, headers=self.getHeaders(), timeout=self.timeOut)
            elif method == 'DELETE':
                r = requests.delete(urlRestBase, params=self.myFields, headers=self.getHeaders(), timeout=self.timeOut)
            elif method == 'GET':
                r = requests.get(urlRestBase, params=self.myFields, headers=self.getHeaders(), timeout=self.timeOut)
            elif method == 'PUT':
                r = requests.put(urlRestBase, data=self.myFields, headers=self.getHeaders(), timeout=self.timeOut)

            self.log.debug('%s[%s] - %s' % (self.msgLog, r.status_code, r.text))

        except Exception as e:
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['vendorDbError']['code'],
                str(e))

        try:
            response = json.loads(r.text)
        except:
            response = ""

        erroMsg = dict()
        if type(response) == dict and 'Message' in response.keys():
            erroMsg['Message'] = response['Message']
        else:
            erroMsg['Message'] = self.appConfig['statusCode']['vendorDbError']['message']

        if type(response) == dict and 'ExceptionMessage' in response.keys():
            erroMsg['ExceptionMessage'] = response['ExceptionMessage']
        else:
            erroMsg['ExceptionMessage'] = ""

        if r.status_code == 200:
            return {'return': 'OK', 'data': response}
        elif r.status_code == 500:
            code = self.appConfig['statusCode']['userAlreadyExiste']['code']
            message = '%s, %s' % (erroMsg['Message'], erroMsg['ExceptionMessage'])
            logLevel = 2
        elif r.status_code == 401:
            code = self.appConfig['statusCode']['unauthorized']['code']
            message = erroMsg['Message']
            logLevel = 2
        elif r.status_code == 404:
            code = self.appConfig['statusCode']['userNotFound']['code']
            message = self.appConfig['statusCode']['userNotFound']['message']
            logLevel = 2
        elif r.status_code == 400:
            code = self.appConfig['statusCode']['badRequest']['code']
            message = self.appConfig['statusCode']['badRequest']['message']
            logLevel = 2
        else:
            code = self.appConfig['statusCode']['vendorDbError']['code']
            message = self.appConfig['statusCode']['vendorDbError']['message']
            logLevel = 1

        raise self.utils.BaseExceptionError(
            code,
            message,
            r.status_code,
            '%s %s' % (erroMsg['Message'], erroMsg['ExceptionMessage']),
            logLevel)
    #
    # Funcao para listar um cliente pelo id
    # resquest de Retorno de sucesso
    # 200 -
    # GET
    ##

    def getProvisioning(self):

        if self.mainId and re.match("^[A-Za-z0-9@.-]*$", self.mainId):
            self.myFields['fsvas_userid'] = self.mainId
        else:
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyB']['code'],
                self.appConfig['statusCode']['invalidKeyB']['message'])

        return self.requestRest('GET', '%sget/%s' % (self.urlRestBase, self.mainId))

    #
    # Funcao para incluir clientes
    # resquest de Retorno de sucesso
    # 200 - {}
    # POST
    #
    def postProvisioning(self):

        if self.mainId and re.match("^[A-Za-z0-9@.-]*$", self.mainId):
            self.myFields['fsvas_userid'] = self.mainId
        else:
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyB']['code'],
                self.appConfig['statusCode']['invalidKeyB']['message'])

        return self.requestRest('POST', '%screate' % (self.urlRestBase))

    #
    # Funcao para atualizar um cliente
    # resquest de Retorno de sucesso
    # 200 - {}
    # PUT
    #
    def putProvisioning(self):

        if self.mainId and re.match("^[A-Za-z0-9@.-]*$", self.mainId):
            self.myFields['fsvas_userid'] = self.mainId
        else:
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyB']['code'],
                self.appConfig['statusCode']['invalidKeyB']['message'])

        if 'fsvas_status' in self.myFields.keys() and self.myFields['fsvas_status'] in [1, '1']:
            self.myFields['fsvas_status'] = True
        elif 'fsvas_status' in self.myFields.keys() and self.myFields['fsvas_status'] in [0, '0']:
            self.myFields['fsvas_status'] = False

        return self.requestRest('POST', '%supdate' % (self.urlRestBase))

    #
    # Funcao para deletar um cliente pelo id
    # resquest de Retorno de sucesso
    # 200 - {}
    # DELETE
    ##
    def deleteProvisioning(self):

        if self.mainId and re.match("^[A-Za-z0-9@.-]*$", self.mainId):
            self.myFields['fsvas_userid'] = self.mainId
        else:
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyB']['code'],
                self.appConfig['statusCode']['invalidKeyB']['message'])

        return self.requestRest('POST', '%sdowngrade' % (self.urlRestBase))

    #
    # TOKEN #
    #
    def getHeaders(self):

        # Session para armazenar o token por 24 horas
        if ((self.operator not in self.sess.keys()) or (self.vendor not in self.sess[self.operator].keys()))\
           or (self.sess[self.operator][self.vendor]['expire_at'] <= datetime.datetime.now()):

            self.log.debug('%s Create new Token' % (self.msgLog))

            params = dict(client_id=self.appConfig['operators'][self.operator]['vendors'][self.provisionerVersion][self.vendor]['publicKeyAula365'],
                          client_secret=self.appConfig['operators'][self.operator]['vendors'][self.provisionerVersion][self.vendor]['secretKeyAula365'],
                          scope=self.appConfig['operators'][self.operator]['vendors'][self.provisionerVersion][self.vendor]['scopeAula365'])

            try:
                r = requests.post('%stoken' % self.urlRestBase, data=params, timeout=self.timeOut)
                if r.status_code == 200 or not r.text:
                    request = json.loads(r.text)
                    self.sess[self.operator][self.vendor] = {
                        'token': request['Key'],
                        'expire_at': datetime.datetime.now() + datetime.timedelta(hours=23)}
                    return {'Authorization': request['Key']}
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
            return {'Authorization': self.sess[self.operator][self.vendor]['token']}

    def status(self):

        self.myFields['fsvas_userid'] = '1'
        return self.requestRest('GET', '%sget/%s' % (self.urlRestBase, '1'))
