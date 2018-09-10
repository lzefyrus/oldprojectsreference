# -*- coding: utf-8 -*-
#
# FSVAS
#
import requests
import json
import tornado.escape
import re

# Classe de provisionaonamento
from provisioner.v2 import Provisioner


class Funambol(Provisioner):

    def requestRest(self, method, urlRestBase, params):
        self.log.info('%s[REQUEST - %s in %s]' % (self.msgLog, method, urlRestBase))

        # methodo para verificar os campos obrigatorios do methodo do vendors
        self.utils.requiredFields(self, self.paramRequiredField, self.paramOptionalsField, self.myFields.keys())
        self.log.debug('%s[REQUEST FIELDS: %s]' % (self.msgLog, params))

        try:
            if self.loginRest and self.senhaRest:
                auth = requests.auth.HTTPBasicAuth(self.loginRest, self.senhaRest)

            if method == 'POST':
                    r = requests.post(urlRestBase, data=params, auth=auth, timeout=self.timeOut)
            elif method == 'DELETE':
                    r = requests.delete(urlRestBase, params=params, auth=auth, timeout=self.timeOut)
            elif method == 'GET':
                    r = requests.get(urlRestBase, params=params, auth=auth, timeout=self.timeOut)
            elif method == 'PUT':
                    r = requests.put(urlRestBase, data=params, auth=auth, timeout=self.timeOut)
            elif method == 'LOGIN':
                r = requests.post(urlRestBase, data=params, timeout=self.timeOut)

            self.log.debug('%s[%s][%s]' % (self.msgLog, r.status_code, r.text))

        except Exception as e:
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['vendorDbError']['code'],
                str(e))

        try:
            request = json.loads(r.text)
        except:
            request = ""

        message = self.appConfig['statusCode']['vendorDbError']['message']
        code = self.appConfig['statusCode']['vendorDbError']['code']
        # log final como error
        logLevel = 1

        if r.status_code == 200:
            logLevel = 2
            dictReturn = {'return': 'OK', 'data': ''}

            if 'data' in request:
                dictReturn['data'] = request['data']

            if 'error' in request:
                if request['error']['code'] == 'PRO-1101':
                    code = self.appConfig['statusCode']['userNotFound']['code']
                    message = self.appConfig['statusCode']['userNotFound']['message']

                elif request['error']['code'] == 'PRO-1104':
                    self.set_status(self.appConfig['statusCode']['deviceNotFound']['code'])
                    code = self.appConfig['statusCode']['deviceNotFound']['code']
                    message = self.appConfig['statusCode']['deviceNotFound']['message']

                elif request['error']['code'] == 'PRO-1113':
                    code = self.appConfig['statusCode']['userAlreadyExiste']['code']
                    message = self.appConfig['statusCode']['userAlreadyExiste']['message']

                elif request['error']['code'] == 'PRO-1000':
                    code = self.appConfig['statusCode']['licenseNotFound']['code']
                    message = self.appConfig['statusCode']['licenseNotFound']['message']
                else:
                    logLevel = 1
                    message = request['error']
            else:
                return dictReturn

        elif r.status_code == 403:
            code = self.appConfig['statusCode']['forbidden']['code']
            message = self.appConfig['statusCode']['forbidden']['message']
            logLevel = 2
        elif r.status_code == 404:
            code = self.appConfig['statusCode']['notFound']['code']
            message = request['error']['message']
            logLevel = 2
        elif r.status_code == 400:
            code = self.appConfig['statusCode']['badRequest']['code']
            message = request['error']['message']
            logLevel = 2
        elif method == 'LOGIN' and r.status_code == 401:
            code = self.appConfig['statusCode']['loginInvalid']['code']
            message = self.appConfig['statusCode']['loginInvalid']['message']
            logLevel = 2

        raise self.utils.BaseExceptionError(
            code,
            message,
            r.status_code,
            r.text,
            logLevel)

    #
    # Funcao para listar um cliente pelo id
    # GET
    ##
    def getProvisioning(self):

        if self.mainId and re.match("^[A-Za-z0-9@.-]*$", self.mainId):
            self.myFields['userid'] = self.mainId
        else:
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyB']['code'],
                self.appConfig['statusCode']['invalidKeyB']['message'])

        return self.requestRest('GET', '%sprofile?action=get' % (self.urlRestBase), self.myFields)

    #
    # Funcao para incluir clientes
    # resquest de Retorno de sucesso
    # 200 - {}
    # POST
    #
    def postProvisioning(self):

        if self.mainId and re.match("^[A-Za-z0-9@.-]*$", self.mainId):
            self.myFields['userid'] = self.mainId
        else:
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyB']['code'],
                self.appConfig['statusCode']['invalidKeyB']['message'])

        # parametros especificos para funambol
        paramsXml = tornado.escape.json_encode(dict(data=dict(user=dict(generic=self.myFields))))

        return self.requestRest('POST', '%sprofile/generic?action=add' % (self.urlRestBase), paramsXml)

    #
    # Funcao para atualizar um cliente
    # resquest de Retorno de sucesso
    # 200 - {}
    # PUT
    #
    def putProvisioning(self):

        if self.mainId and re.match("^[A-Za-z0-9@.-]*$", self.mainId):
            self.myFields['userid'] = self.mainId
        else:
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyB']['code'],
                self.appConfig['statusCode']['invalidKeyB']['message'],
                self.log)

        if 'enabled' in self.myFields and self.myFields['enabled'] == '1':
            self.myFields['active'] = 'true'
            del self.myFields['enabled']
        elif 'enabled' in self.myFields and self.myFields['enabled'] == '0':
            self.myFields['active'] = 'false'
            del self.myFields['enabled']

        # parametros especificos para funambol
        paramsXml = tornado.escape.json_encode(dict(data=dict(user=dict(generic=self.myFields))))
        return self.requestRest('POST', '%sprofile/generic?action=update&userid=%s' % (self.urlRestBase, self.myFields['userid']), paramsXml)

    #
    # Funcao para deletar um cliente pelo id
    # resquest de Retorno de sucesso
    # 200 - {}
    # DELETE
    ##
    def deleteProvisioning(self):

        if self.mainId and re.match("^[A-Za-z0-9@.-]*$", self.mainId):
            self.myFields['userid'] = self.mainId
        else:
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyB']['code'],
                self.appConfig['statusCode']['invalidKeyB']['message'])

        return self.requestRest(
            'POST',
            '%sprofile/generic?action=delete&userid=%s' % (self.urlRestBase, self.myFields['userid']), self.myFields)

    #
    # Licenses
    #

    #
    # Funcao para listar todos os roles disponiveis
    # GET
    ##
    def getRoles(self):

        return self.requestRest('GET', '%sprofile/role?action=roles' % (self.urlRestBase), self.myFields)

    #
    # Funcao para listar todos os roles de um usuario
    # resquest de Retorno de sucesso
    # 200 - {}
    # GET
    ##
    def getLicenses(self):

        if not self.mainId or not re.match("^[A-Za-z0-9@.-]*$", self.mainId):
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyB']['code'],
                self.appConfig['statusCode']['invalidKeyB']['message'])

        return self.requestRest('GET', '%sprofile/role?action=get&userid=%s' % (self.urlRestBase, self.mainId), self.myFields)

    #
    # Funcao para adicionar uma licensa ao usuario
    # resquest de Retorno de sucesso
    # 200 - {}
    # POST
    ##
    def postLicenses(self):

        if not self.mainId or not re.match("^[A-Za-z0-9@.-]*$", self.mainId):
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyB']['code'],
                self.appConfig['statusCode']['invalidKeyB']['message'])

        listRoles = [dict(name='sync_user')]
        if 'name' in self.myFields:
            full = dict()

            for index, name in enumerate(self.request.arguments['name'], start=0):
                full['name'] = name.decode('utf-8')
                if 'description' in self.request.arguments and int(index+1) <= len(self.request.arguments['description']):
                    full['description'] = self.request.arguments['description'][index].decode('utf-8')
                listRoles.append(full)
                full = dict()

        # parametros especificos para funambol
        paramsXml = tornado.escape.json_encode(dict(data=dict(roles=listRoles)))
        return self.requestRest('POST', '%sprofile/role?action=save&userid=%s' % (self.urlRestBase, self.mainId), paramsXml)

    #
    # Funcao para atualizar uma licensa ao usuario
    # resquest de Retorno de sucesso
    # 200 - {}
    # POST
    ##
    def putLicenses(self):

        if not self.mainId or not re.match("^[A-Za-z0-9@.-]*$", self.mainId):
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyB']['code'],
                self.appConfig['statusCode']['invalidKeyB']['message'])

        listRoles = [dict(name='sync_user')]
        if 'name' in self.myFields:
            full = dict(name=self.myFields['name'])
            if 'description' in self.myFields:
                full['description'] = self.myFields['description']
            listRoles.append(full)

        # parametros especificos para funambol
        paramsXml = tornado.escape.json_encode(dict(data=dict(roles=listRoles)))
        return self.requestRest('POST', '%sprofile/role?action=save&userid=%s' % (self.urlRestBase, self.mainId), paramsXml)

    #
    # Login
    #

    #
    # Funcao para listar todos os roles de um usuario
    # resquest de Retorno de sucesso
    # 200 - {}
    # GET
    ##
    def postLogin(self):

        return self.requestRest('LOGIN', '%slogin?action=login' % (self.urlRestBase), self.myFields)

    #
    # Funcao para adicionar uma licensa ao usuario
    # resquest de Retorno de sucesso
    # 200 - {}
    # POST
    ##
    def postLogout(self):

        return self.requestRest('GET', '%slogin?action=logout' % (self.urlRestBase), self.myFields)

    #
    # Quota
    #

    #
    # Funcao para listar todos os roles de um usuario
    # resquest de Retorno de sucesso
    # 200 - {}
    # GET
    ##
    def getQuota(self):

        if not self.mainId or not re.match("^[A-Za-z0-9@.-]*$", self.mainId):
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyB']['code'],
                self.appConfig['statusCode']['invalidKeyB']['message'])

        return self.requestRest(
            'GET',
            '%smedia?action=get-storage-space&userid=%s' % (self.urlRestBase, self.mainId), self.myFields)

    #
    # Search
    #

    #
    # Funcao para fazer uma busca
    # GET
    ##
    def getSearch(self):

        if not self.myFields:
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['missingFields']['code'],
                self.appConfig['statusCode']['missingFields']['message'])

        return self.requestRest('GET', '%sprofile?action=search' % (self.urlRestBase), self.myFields)

    #
    # Funcao para listar um cliente pelo id
    # GET
    ##
    def status(self):

        self.myFields['userid'] = '1'
        return self.requestRest('GET', '%sprofile?action=get' % (self.urlRestBase), self.myFields)

    #
    # Devices
    #

    def getDevices(self):

        if self.mainId and re.match("^[A-Za-z0-9@.-]*$", self.mainId):
            self.myFields['userid'] = self.mainId
        else:
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyB']['code'],
                self.appConfig['statusCode']['invalidKeyB']['message'])

        return self.requestRest('GET', '%sprofile/device?action=get' % (self.urlRestBase), self.myFields)

    def postDevices(self):

        if not self.mainId or not re.match("^[A-Za-z0-9@.-]*$", self.mainId):
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyB']['code'],
                self.appConfig['statusCode']['invalidKeyB']['message'])

        if 'modelid' not in self.myFields:
            self.myFields['modelid'] = 1
        if 'carrierid' not in self.myFields:
            self.myFields['carrierid'] = '10019'
        if 'countrya2' not in self.myFields:
            self.myFields['countrya2'] = 'US'
        if 'devicename' not in self.myFields:
            self.myFields['devicename'] = 'Celular'

        # parametros especificos para funambol
        paramsXml = tornado.escape.json_encode(dict(data=dict(user=dict(phone=self.myFields))))

        return self.requestRest('POST', '%sprofile/device?action=add&userid=%s' % (self.urlRestBase, self.mainId), paramsXml)

    def putDevices(self):

        if not self.mainId or not re.match("^[A-Za-z0-9@.-]*$", self.mainId):
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyB']['code'],
                self.appConfig['statusCode']['invalidKeyB']['message'])

        # parametros especificos para funambol
        paramsXml = tornado.escape.json_encode(dict(data=dict(user=dict(phone=self.myFields))))
        return self.requestRest(
            'POST',
            '%sprofile/device?action=update&deviceid=%s' % (
                self.urlRestBase,
                self.mainId),
            paramsXml)

    def deleteDevices(self):

        if not self.mainId or not re.match("^[A-Za-z0-9@.-]*$", self.mainId):
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyB']['code'],
                self.appConfig['statusCode']['invalidKeyB']['message'])

        if 'deviceid' not in self.myFields:
            deviceid = None
        else:
            deviceid = self.myFields['deviceid']

        return self.requestRest(
            'POST',
            '%sprofile/device?action=delete&userid=%s&deviceid=%s' % (
                self.urlRestBase,
                self.mainId,
                deviceid),
            self.myFields)

    #
    # Picture
    #

    #
    # Funcao para listar a quantidade de imagens de um usuario
    # resquest de Retorno de sucesso
    # 200 - {}
    # GET
    ##
    def getPictures(self):

        if not self.mainId or not re.match("^[A-Za-z0-9@.-]*$", self.mainId):
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyB']['code'],
                self.appConfig['statusCode']['invalidKeyB']['message'])

        return self.requestRest(
            'GET',
            '%smedia/picture?action=count&userid=%s' % (self.urlRestBase, self.mainId), self.myFields)

    #
    # Videos
    #

    #
    # Funcao para listar a quantidade de videos de um usuario
    # resquest de Retorno de sucesso
    # 200 - {}
    # GET
    ##
    def getVideos(self):

        if not self.mainId or not re.match("^[A-Za-z0-9@.-]*$", self.mainId):
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyB']['code'],
                self.appConfig['statusCode']['invalidKeyB']['message'])

        return self.requestRest(
            'GET',
            '%smedia/video?action=count&userid=%s' % (self.urlRestBase, self.mainId), self.myFields)

    #
    # Files
    #

    #
    # Funcao para listar a quantidade de arquivos de um usuario
    # resquest de Retorno de sucesso
    # 200 - {}
    # GET
    ##
    def getFiles(self):

        if not self.mainId or not re.match("^[A-Za-z0-9@.-]*$", self.mainId):
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyB']['code'],
                self.appConfig['statusCode']['invalidKeyB']['message'])

        return self.requestRest(
            'GET',
            '%smedia/file?action=count&userid=%s' % (self.urlRestBase, self.mainId), self.myFields)

    #
    # Audio
    #

    #
    # Funcao para listar a quantidade de audios de um usuario
    # resquest de Retorno de sucesso
    # 200 - {}
    # GET
    ##
    def getAudios(self):

        if not self.mainId or not re.match("^[A-Za-z0-9@.-]*$", self.mainId):
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyB']['code'],
                self.appConfig['statusCode']['invalidKeyB']['message'])

        return self.requestRest(
            'GET',
            '%smedia/audio?action=count&userid=%s' % (self.urlRestBase, self.mainId), self.myFields)

    #
    # Profile
    #

    #
    # Funcao para listar a a data da ultima atualizacao
    # resquest de Retorno de sucesso
    # 200 - {}
    # GET
    ##
    def getProfile(self):

        if not self.mainId or not re.match("^[A-Za-z0-9@.-]*$", self.mainId):
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyB']['code'],
                self.appConfig['statusCode']['invalidKeyB']['message'])

        return self.requestRest(
            'GET',
            '%sprofile?action=get-last-sync&userid=%s' % (self.urlRestBase, self.mainId), self.myFields)

    #
    # History
    #

    #
    #
    # GET
    ##
    def getHistory(self):

        if self.mainId and re.match("^[A-Za-z0-9@.-]*$", self.mainId):
            self.myFields['userid'] = self.mainId
        else:
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyB']['code'],
                self.appConfig['statusCode']['invalidKeyB']['message'])

        return self.requestRest('GET', '%sactivity?action=get' % (self.urlRestBase), self.myFields)
