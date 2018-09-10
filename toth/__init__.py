# -*- coding: utf-8 -*-
#
# FSVAS
#
import importlib
import requests
from requests.auth import HTTPBasicAuth
import json
import tornado.escape
import re


class Funambol():
    #
    # Classe funambol
    #

    def __init__(self, mainSelf):
        # Import do utils pela versao do toth
        self.utils = importlib.import_module('utils%s' % (mainSelf.appConfig['versions']['utils']))
        # pega o self principal e joga na classe atual
        self.mainSelf = mainSelf

        # Pega os campos required do methodo do vendors
        if self.mainSelf.vendor not in self.mainSelf.appConfig['vendors'][self.mainSelf.tothVersion]:
            raise self.utils.BaseExceptionError(401, msg='Vendors Field Not Found ini')

        # Url base do rest do vendors
        self.urlRestBase = self.mainSelf.appConfig['operators'][self.mainSelf.operator]['vendors'][self.mainSelf.tothVersion][self.mainSelf.vendor]['urlBase']
        self.loginRest, self.senhaRest = tuple(
            self.mainSelf.appConfig['operators'][self.mainSelf.operator]['vendors'][self.mainSelf.tothVersion][self.mainSelf.vendor]['loginRest'])
        #

        for k, w in self.mainSelf.request.arguments.items():
            self.mainSelf.request.arguments[k] = w[0] if isinstance(w, list) else w

        # Cria a variavel de fields
        self.myFields = dict()

    #

    # - Funcao principal da anchorfree
    def main(self):
        # pega o methodo do conf
        # vendors/vendedor/tipodeacao/methodo
        methods = self.mainSelf.appConfig['vendors'][self.mainSelf.tothVersion][self.mainSelf.vendor][self.mainSelf.typeVendor]

        # Se nao existir o methodo para o tipo do vendor, erro
        if self.mainSelf.request.method.lower() not in methods:
            raise self.utils.BaseExceptionError(401, msg='No exist method %s to %s' %
                                                (self.mainSelf.request.method.lower(), self.mainSelf.typeVendor))

        # Pega todas as funcoes desse methodo
        methods = methods[self.mainSelf.request.method.lower()]

        # pega os campos required da funcao
        self.getRequiredFields = methods

        # Chama o methodo pegando o nome dele no arquivo de conf
        # O methodo precisa estar nesse arquivo com o mesmo nome
        return getattr(self, methods.keys()[0])()

    #

    # Funcao que faz o request de fato
    #
    def requestRest(self, **kwargs):

        # methodo para verificar os campos opcionais do methodo do vendors
        errorFields = self.utils.optionalsFields(
            self.myFields, kwargs['paramRequiredField'],
            kwargs['paramOptionalsField'],
            self.mainSelf.request.arguments.keys())

        if errorFields:
            raise self.utils.BaseExceptionError(401, msg='%s - this method do not accept field(s)%s' % (self.mainSelf.vendor, errorFields))

        # methodo para verificar os campos obrigatorios do methodo do vendors
        errorFields = self.utils.requiredFields(kwargs['params'], kwargs['paramRequiredField'], self.myFields.keys())
        if errorFields:
            raise self.utils.BaseExceptionError(401, msg='%s missing field%s' % (self.mainSelf.vendor, errorFields))

        print('CAMPOS')
        print(self.myFields)
        print('URL')
        print(kwargs['urlRestBase'])

        if kwargs['method'] == 'POST':
            if self.loginRest and self.senhaRest:
                r = requests.post(kwargs['urlRestBase'], data=kwargs['params'], auth=HTTPBasicAuth(self.loginRest, self.senhaRest))
            else:
                r = requests.post(kwargs['urlRestBase'], data=kwargs['params'])
        elif kwargs['method'] == 'DELETE':
            if self.loginRest and self.senhaRest:
                r = requests.delete(kwargs['urlRestBase'], params=kwargs['params'], auth=HTTPBasicAuth(self.loginRest, self.senhaRest))
            else:
                r = requests.delete(kwargs['urlRestBase'], params=kwargs['params'])
        elif kwargs['method'] == 'GET':
            if self.loginRest and self.senhaRest:
                r = requests.get(kwargs['urlRestBase'], params=kwargs['params'], auth=HTTPBasicAuth(self.loginRest, self.senhaRest))
            else:
                r = requests.get(kwargs['urlRestBase'], params=kwargs['params'])
        elif kwargs['method'] == 'PUT':
            if self.loginRest and self.senhaRest:
                r = requests.put(kwargs['urlRestBase'], data=kwargs['params'], auth=HTTPBasicAuth(self.loginRest, self.senhaRest))
            else:
                r = requests.put(kwargs['urlRestBase'], data=kwargs['params'])
        elif kwargs['method'] == 'LOGIN':
            r = requests.post(kwargs['urlRestBase'], data=kwargs['params'])

        print(r.status_code)
        print('RETORNO')
        print(r.__dict__)

        if r.status_code == 200:
            data = ""
            if r.text:
                print('aqui!!')
                request = json.loads(r.text)
                if 'error' in request:
                    raise self.utils.BaseExceptionError(401, msg=request['error']['message'])
                data = request['data']

            # adiciona um return OK
            dictReturn = {'return': 'OK', 'data': data}
            return dictReturn
        elif r.status_code == 404 or r.status_code == 403 or r.status_code == 400:
            error = json.loads(r.text)
            raise self.utils.BaseExceptionError(401, msg=error['error']['message'])
        else:
            raise self.utils.BaseExceptionError(401, msg='Conection with vendors db error. Code - %s' % r.status_code)

    #
    # Funcao para listar um cliente pelo id
    # GET
    ##
    def getProvisioning(self):
        print('=============FUNAMBOL - %s ==========' % (self.mainSelf.operator))
        print('getProvisioning')
        print('=============%s==========' % self.mainSelf.mainId)
        if re.match("^[A-Za-z0-9]*$", self.mainSelf.mainId):
            self.myFields['userid'] = self.mainSelf.mainId
        else:
            raise self.utils.BaseExceptionError(401, msg='Invalid Key [A-Za-z0-9]')

        return self.requestRest(
            method='GET',
            paramRequiredField=self.getRequiredFields['getProvisioning'],
            paramOptionalsField=self.getRequiredFields['optionals'],
            urlRestBase='%sprofile?action=get' % (self.urlRestBase),
            params=self.myFields)

    #
    # Funcao para incluir clientes
    # resquest de Retorno de sucesso
    # 200 - {}
    # POST
    #
    def postProvisioning(self):
        print('=============FUNAMBOL==========')
        print('postProvisioning')
        if self.mainSelf.mainId and re.match("^[A-Za-z0-9]*$", self.mainSelf.mainId):
            self.myFields['userid'] = self.mainSelf.mainId
        else:
            raise self.utils.BaseExceptionError(401, msg='Invalid Key [A-Za-z0-9]')

        # retira o id por parametro
        if 'userid' in self.mainSelf.request.arguments:
            del self.mainSelf.request.arguments['userid']

        # Pega os parametros via argumentos
        # Os argumentos vao como b[], a api da funambol nao aceita
        # transformando tudo em str

        print(self.mainSelf.request.arguments)
        for args in self.mainSelf.request.arguments:
            self.myFields[args] = self.mainSelf.request.arguments[args].decode()
        print(self.myFields)

        # parametros especificos para funambol
        params = tornado.escape.json_encode(dict(data=dict(user=dict(generic=self.myFields))))

        return self.requestRest(
            method='POST',
            paramRequiredField=self.getRequiredFields['postProvisioning'],
            paramOptionalsField=self.getRequiredFields['optionals'],
            urlRestBase='%sprofile/generic?action=add' % (self.urlRestBase), params=params)

    #
    # Funcao para atualizar um cliente
    # resquest de Retorno de sucesso
    # 200 - {}
    # PUT
    #
    def putProvisioning(self):
        print('=============FUNAMBOL==========')
        print('putProvisioning')
        print('=============%s==========' % self.mainSelf.mainId)

        if re.match("^[A-Za-z0-9]*$", self.mainSelf.mainId):
            self.myFields['userid'] = self.mainSelf.mainId
        else:
            raise self.utils.BaseExceptionError(401, msg='Invalid Key [A-Za-z0-9]')

        # retira o id por parametro
        if 'userid' in self.mainSelf.request.arguments:
            del self.mainSelf.request.arguments['userid']

        if 'enabled' in self.mainSelf.request.arguments and self.mainSelf.request.arguments['enabled'].decode() == '1':
            self.mainSelf.request.arguments['active'] = b'true'
            del self.mainSelf.request.arguments['enabled']
        elif 'enabled' in self.mainSelf.request.arguments and self.mainSelf.request.arguments['enabled'].decode() == '0':
            self.mainSelf.request.arguments['active'] = b'false'
            del self.mainSelf.request.arguments['enabled']

        # Pega os parametros via argumentos
        # Os argumentos vao como b[], a api da funambol nao aceita
        # transformando tudo em str
        for args in self.mainSelf.request.arguments:
            print(self.mainSelf.request.arguments[args])
            self.myFields[args] = self.mainSelf.request.arguments[args].decode()

        # parametros especificos para funambol
        params = tornado.escape.json_encode(dict(data=dict(user=dict(generic=self.myFields))))

        return self.requestRest(
            method='POST',
            paramRequiredField=self.getRequiredFields['putProvisioning'],
            paramOptionalsField=self.getRequiredFields['optionals'],
            urlRestBase='%sprofile/generic?action=update&userid=%s' % (self.urlRestBase, self.myFields['userid']), params=params)

    #
    # Funcao para deletar um cliente pelo id
    # resquest de Retorno de sucesso
    # 200 - {}
    # DELETE
    ##
    def deleteProvisioning(self):
        print('=============FUNAMBOL==========')
        print('deleteProvisioning')
        print('=============%s==========' % self.mainSelf.mainId)
        if re.match("^[A-Za-z0-9]*$", self.mainSelf.mainId):
            self.myFields['userid'] = self.mainSelf.mainId
        else:
            raise self.utils.BaseExceptionError(401, msg='Invalid Key [A-Za-z0-9]')

        return self.requestRest(
            method='POST',
            paramRequiredField=self.getRequiredFields['deleteProvisioning'],
            paramOptionalsField=self.getRequiredFields['optionals'],
            urlRestBase='%sprofile/generic?action=delete&userid=%s' % (self.urlRestBase, self.myFields['userid']), params=self.myFields)

    #
    # Licenses
    #

    #
    # Funcao para listar todos os roles de um usuario
    # resquest de Retorno de sucesso
    # 200 - {}
    # GET
    ##
    def getLicenses(self):
        print('=============FUNAMBOL - %s ==========' % self.mainSelf.operator)
        print('getLicenses')
        print('=============%s==========' % self.mainSelf.mainId)

        if not re.match("^[A-Za-z0-9]*$", self.mainSelf.mainId):
            raise self.utils.BaseExceptionError(401, msg='Invalid Key [A-Za-z0-9]')

        # retira o id por parametro
        if 'userid' in self.mainSelf.request.arguments:
            del self.mainSelf.request.arguments['userid']

        return self.requestRest(
            method='GET',
            paramRequiredField=self.getRequiredFields['getLicenses'],
            paramOptionalsField=self.getRequiredFields['optionals'],
            urlRestBase='%sprofile/role?action=get&userid=%s' % (self.urlRestBase, self.mainSelf.mainId), params=self.myFields)

    #
    # Funcao para adicionar uma licensa ao usuario
    # resquest de Retorno de sucesso
    # 200 - {}
    # POST
    ##
    def postLicenses(self):
        print('=============FUNAMBOL==========')
        print('postLicenses')
        print('=============%s==========' % self.mainSelf.mainId)
        if re.match("^[A-Za-z0-9]*$", self.mainSelf.mainId):
            self.myFields['userid'] = self.mainSelf.mainId
        else:
            raise self.utils.BaseExceptionError(401, msg='Invalid Key [A-Za-z0-9]')

        # retira o id por parametro
        if 'userid' in self.mainSelf.request.arguments:
            del self.mainSelf.request.arguments['userid']

        if 'name' in self.mainSelf.request.arguments:
            listRoles = list()
            listRoles.append(dict(name='sync_user'))
            full = dict()
            full['name'] = self.mainSelf.request.arguments['name'].decode('utf-8')
            self.myFields['name'] = full['name']
            if 'description' in self.mainSelf.request.arguments:
                full['description'] = self.mainSelf.request.arguments['description'].decode('utf-8')
                self.myFields['description'] = full['description']
            listRoles.append(full)
            del self.mainSelf.request.arguments['name']
        else:
            self.myFields['name'] = ''

        # parametros especificos para funambol
        params = tornado.escape.json_encode(dict(data=dict(roles=listRoles)))
        return self.requestRest(
            method='POST',
            paramRequiredField=self.getRequiredFields['postLicenses'],
            paramOptionalsField=self.getRequiredFields['optionals'],
            urlRestBase='%sprofile/role?action=save&userid=%s' % (self.urlRestBase, self.mainSelf.mainId), params=params)

    #
    # Funcao para atualizar uma licensa ao usuario
    # resquest de Retorno de sucesso
    # 200 - {}
    # POST
    ##
    def putLicenses(self):
        print('=============FUNAMBOL==========')
        print('putLicenses')
        print('=============%s==========' % self.mainSelf.mainId)
        if re.match("^[A-Za-z0-9]*$", self.mainSelf.mainId):
            self.myFields['userid'] = self.mainSelf.mainId
        else:
            raise self.utils.BaseExceptionError(401, msg='Invalid Key [A-Za-z0-9]')

        # retira o id por parametro
        if 'userid' in self.mainSelf.request.arguments:
            del self.mainSelf.request.arguments['userid']

        if 'name' in self.mainSelf.request.arguments:
            listRoles = list()
            listRoles.append(dict(name='sync_user'))

            full = dict()
            full['name'] = self.mainSelf.request.arguments['name'].decode('utf-8')
            self.myFields['name'] = full['name']
            if 'description' in self.mainSelf.request.arguments:
                full['description'] = self.mainSelf.request.arguments['description'].decode('utf-8')
                self.myFields['description'] = full['description']
            listRoles.append(full)
            del self.mainSelf.request.arguments['name']
        else:
            self.myFields['name'] = ''

        # parametros especificos para funambol
        params = tornado.escape.json_encode(dict(data=dict(roles=listRoles)))
        return self.requestRest(
            method='POST',
            paramRequiredField=self.getRequiredFields['postLicenses'],
            paramOptionalsField=self.getRequiredFields['optionals'],
            urlRestBase='%sprofile/role?action=save&userid=%s' % (self.urlRestBase, self.mainSelf.mainId), params=params)

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
        print('=============FUNAMBOL - %s ==========' % self.mainSelf.operator)
        print('postLogin')
        print('=======================')

        # Pega os parametros via argumentos
        # Os argumentos vao como b[], a api da funambol nao aceita
        # transformando tudo em str
        for args in self.mainSelf.request.arguments:
            self.myFields[args] = self.mainSelf.request.arguments[args].decode()

        return self.requestRest(
            method='LOGIN',
            paramRequiredField=self.getRequiredFields['postLogin'],
            paramOptionalsField=self.getRequiredFields['optionals'],
            urlRestBase='%slogin?action=login' % (self.urlRestBase), params=self.myFields)

    #
    # Funcao para adicionar uma licensa ao usuario
    # resquest de Retorno de sucesso
    # 200 - {}
    # POST
    ##
    def postLogout(self):
        print('=============FUNAMBOL==========')
        print('postLogout')
        print('=======================')

        # Pega os parametros via argumentos
        # Os argumentos vao como b[], a api da funambol nao aceita
        # transformando tudo em str
        for args in self.mainSelf.request.arguments:
            self.myFields[args] = self.mainSelf.request.arguments[args].decode()

        return self.requestRest(
            method='GET',
            paramRequiredField=self.getRequiredFields['postLogout'],
            paramOptionalsField=self.getRequiredFields['optionals'],
            urlRestBase='%slogin?action=logout' % (self.urlRestBase), params=self.myFields)

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
        print('=============FUNAMBOL - %s ==========' % self.mainSelf.operator)
        print('getQuota')
        print('=============%s==========' % self.mainSelf.mainId)

        if not re.match("^[A-Za-z0-9]*$", self.mainSelf.mainId):
            raise self.utils.BaseExceptionError(401, msg='Invalid Key [A-Za-z0-9]')

        # retira o id por parametro
        if 'userid' in self.mainSelf.request.arguments:
            del self.mainSelf.request.arguments['userid']

        # Pega os parametros via argumentos
        # Os argumentos vao como b[], a api da funambol nao aceita
        # transformando tudo em str
        for args in self.mainSelf.request.arguments:
            self.myFields[args] = self.mainSelf.request.arguments[args].decode()

        return self.requestRest(
            method='GET',
            paramRequiredField=self.getRequiredFields['getQuota'],
            paramOptionalsField=self.getRequiredFields['optionals'],
            urlRestBase='%smedia?action=get-storage-space&userid=%s' % (self.urlRestBase, self.mainSelf.mainId), params=self.myFields)
