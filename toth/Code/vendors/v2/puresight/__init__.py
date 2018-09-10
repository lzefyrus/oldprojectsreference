# -*- coding: utf-8 -*-
#
# FSVAS
#
import urllib3
from xml.dom import minidom
import re
import time

# Classe de provisionaonamento
from provisioner.v2 import Provisioner


class Puresight(Provisioner):

    def requestRest(self, urlRestBase):

        self.log.info('%s[REQUEST - GET in %s]' % (self.msgLog, urlRestBase))

        self.log.debug('%s[REQUEST FIELDS: %s]' % (self.msgLog, self.myFields))

        # Adiciona a chave de admin fora do log
        self.myFields['adminUser'] = self.loginRest
        self.myFields['adminPassword'] = self.senhaRest

        # methodo para verificar os campos obrigatorios do methodo do vendors
        self.utils.requiredFields(self, self.paramRequiredField, self.paramOptionalsField, self.myFields.keys())

        try:
            # Desabilitar warnings
            urllib3.disable_warnings()
            http = urllib3.PoolManager(retries=1, timeout=self.timeOut)

            # puresight eh sempre via GET
            r = http.request('GET', urlRestBase, fields=self.myFields)

            requestData = r.data.decode()
            r.close()

            self.log.debug('%s[%s] - %s' % (self.msgLog, r.status, requestData))

        except Exception as e:
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['vendorDbError']['code'],
                str(e))

        code = self.appConfig['statusCode']['vendorDbError']['code']
        message = self.appConfig['statusCode']['vendorDbError']['message']
        logLevel = 1

        if r.status == 200:
            # Pega o resultado em xml e transforma em json
            xmlparse = minidom.parseString(requestData)
            cgi = xmlparse.getElementsByTagName('CGI_MESSAGES')
            status = cgi[0].attributes['status']

            if status.value != 'SUCCEEDED':
                message = status.value
                if status.value == 'PS_INVALID_ACCOUNT' or status.value == 'PS_ACCOUNT_DOES_NOT_EXIST':
                    code = self.appConfig['statusCode']['userNotFound']['code']
                    message = self.appConfig['statusCode']['userNotFound']['message']
                    logLevel = 2
                if status.value == 'PS_ACCOUNT_ALREADY_EXISTS':
                    code = self.appConfig['statusCode']['userAlreadyExiste']['code']
                    message = self.appConfig['statusCode']['userAlreadyExiste']['message']
                    logLevel = 2
                if status.value == 'PS_ACCOUNT_SECONDARY_ALREADY_EXISTS':
                    code = self.appConfig['statusCode']['secondaryUserAlreadyExiste']['code']
                    message = self.appConfig['statusCode']['secondaryUserAlreadyExiste']['message']
                    logLevel = 2
                if status.value == 'PS_INVALID_PASSWORD_SIZE':
                    code = self.appConfig['statusCode']['invalidPasswordFormat']['code']
                    message = self.appConfig['statusCode']['invalidPasswordFormat']['message']
                    logLevel = 2
            else:
                # adiciona um return OK
                dictReturn = {'return': 'OK', 'data': {}}

                # Get fora do padrao
                if xmlparse.getElementsByTagName('DATA'):
                    tag = xmlparse.getElementsByTagName('DATA')

                    # pega o Id caso seja um cadastro
                    if 'accountId' in tag[0].attributes:
                        dictReturn['data']['accountId'] = tag[0].attributes['accountId'].value
                    # pega o account caso seja um cadastro
                    if 'account' in tag[0].attributes:
                        dictReturn['data']['account'] = tag[0].attributes['account'].value
                    # pega o password caso seja um cadastro
                    if 'password' in tag[0].attributes:
                        dictReturn['data']['password'] = tag[0].attributes['password'].value

                # Get fora do padrao
                if xmlparse.getElementsByTagName('UserStatusReport'):
                    data = xmlparse.getElementsByTagName('UserStatusReport')

                    # pega o status caso seja um get
                    if 'status' in data[0].attributes:
                        dictReturn['data']['status'] = data[0].attributes['status'].value
                    # pega o registrationAllowed caso seja um get
                    if 'registrationAllowed' in data[0].attributes:
                        dictReturn['data']['registrationAllowed'] = data[0].attributes['registrationAllowed'].value
                    # pega o registrationUsed caso seja um get
                    if 'registrationUsed' in data[0].attributes:
                        dictReturn['data']['registrationUsed'] = data[0].attributes['registrationUsed'].value
                    # pega o endActivationDate caso seja um get
                    if 'endActivationDate' in data[0].attributes:
                        dictReturn['data']['endActivationDate'] = data[0].attributes['endActivationDate'].value
                    # pega o autoRenew caso seja um get
                    if 'autoRenew' in data[0].attributes:
                        dictReturn['data']['autoRenew'] = data[0].attributes['autoRenew'].value
                    # pega o licenseType caso seja um get
                    if 'licenseType' in data[0].attributes:
                        dictReturn['data']['licenseType'] = data[0].attributes['licenseType'].value
                    # pega o accountType caso seja um get
                    if 'accountType' in data[0].attributes:
                        dictReturn['data']['accountType'] = data[0].attributes['accountType'].value
                    # pega o externalRef caso seja um get
                    if 'externalRef' in data[0].attributes:
                        dictReturn['data']['externalRef'] = data[0].attributes['externalRef'].value

                return dictReturn

        raise self.utils.BaseExceptionError(
            code,
            message,
            r.status,
            requestData,
            logLevel)

    #
    # Funcao para pegar os clientes
    # GET
    #
    def getProvisioning(self):

        if self.mainId and re.match("^[0-9A-Za-z@_\-.]*$", self.mainId):
            self.myFields['email'] = self.mainId
        else:
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyE']['code'],
                self.appConfig['statusCode']['invalidKeyE']['message'])

        return self.requestRest('%sUsersStatusReport.cgi' % (self.urlRestBase))

    #
    # Funcao para incluir clientes
    # resquest de Retorno de sucesso
    # 200 - <ROOT><CGI_MESSAGES status="SUCCEEDED"><DATA account="11993626470" accountId="3402"></DATA></CGI_MESSAGES></ROOT>
    # GET
    #
    def postProvisioning(self):

        if self.mainId and re.match("^[0-9A-Za-z@_\-.]*$", self.mainId):
            self.myFields['email'] = self.mainId
        else:
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyE']['code'],
                self.appConfig['statusCode']['invalidKeyE']['message'])

        # Sempre 'I'
        self.myFields['accountType'] = 'I'

        if 'lang' not in self.myFields.keys():
            self.myFields['lang'] = 'pt-BR'

        if 'autoRenew' not in self.myFields.keys():
            self.myFields['autoRenew'] = 1
            self.myFields['autoRenewMonths'] = 12
            self.myFields['autoRenewDays'] = 31

        return self.requestRest('%sCreateValidatedAccount.cgi' % (self.urlRestBase))

    #
    # Funcao para desativar um cliente
    # resquest de Retorno de sucesso
    # 200 - <ROOT><CGI_MESSAGES status="SUCCEEDED"><DATA ></DATA></CGI_MESSAGES></ROOT>
    # GET
    #
    def putProvisioning(self):

        if self.mainId and re.match("^[0-9A-Za-z@_\-.]*$", self.mainId):
            self.myFields['email'] = self.mainId
        else:
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyE']['code'],
                self.appConfig['statusCode']['invalidKeyE']['message'])

        if 'clear' not in self.myFields.keys():
            self.myFields['clear'] = 1

        dictReturn = None
        if 'password' in self.myFields.keys():
            self.myFields['accountPass'] = self.myFields['password']
            del self.myFields['password']
            dictReturn = self.requestRest('%sSetAccountPassword.cgi' % (self.urlRestBase))

        # Troca do tamanho da licenca do usuario
        if 'registrationCounter' in self.myFields.keys():
            self.myFields['showRegistrationAllowed'] = 1
            getUser = self.requestRest('%sUsersStatusReport.cgi' % (self.urlRestBase))

            if 'data' in getUser:
                licenseSize = int(getUser['data']['registrationAllowed']) - int(self.myFields['registrationCounter'])
                if licenseSize == 0:
                    dictReturn = {'return': 'OK', 'data': {}}
                else:
                    if licenseSize > 0:
                        self.myFields['decrease'] = 1
                        self.myFields['registrationCounter'] = licenseSize
                    elif licenseSize < 0:
                        self.myFields['decrease'] = 0
                        self.myFields['registrationCounter'] = abs(licenseSize)

                    dictReturn = self.requestRest('%sAddRegistrationToAccount.cgi' % (self.urlRestBase))
            del self.myFields['registrationCounter']

        # abilita o usuario
        if 'enabled' in self.myFields.keys() and self.myFields['enabled'] == '1':
            del self.myFields['enabled']

            if 'activationPeriodMonths' not in self.myFields.keys():
                self.myFields['activationPeriodMonths'] = 12

            if 'activationPeriodDays' not in self.myFields.keys():
                self.myFields['activationPeriodDays'] = 31

            if 'autoRenew' not in self.myFields.keys():
                self.myFields['autoRenew'] = 1
                self.myFields['autoRenewMonths'] = 12
                self.myFields['autoRenewDays'] = 31

            dictReturn = self.requestRest('%sActivateAccount.cgi' % (self.urlRestBase))
        # desabilita o usuario
        elif 'enabled' in self.myFields.keys() and self.myFields['enabled'] == '0':
            del self.myFields['enabled']
            self.myFields['endActivationDate'] = time.strftime('%Y-%m-%d')
            dictReturn = self.requestRest('%sDeactivateAccount.cgi' % (self.urlRestBase))
        # troca o email primario(KEY)
        elif 'newEmail' in self.myFields.keys():
            dictReturn = self.requestRest('%sChangeAccountEmail.cgi' % (self.urlRestBase))
        # troca o email secundario(tambem usado para logar)
        elif 'newEmailSecondary' in self.myFields.keys():
            dictReturn = self.requestRest('%sChangeAccountEmail.cgi' % (self.urlRestBase))

        if dictReturn:
            return dictReturn
        else:
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['missingFields']['code'],
                self.appConfig['statusCode']['missingFields']['message'])

    #
    # Funcao para desativar um cliente
    # resquest de Retorno de sucesso
    # 200 - <ROOT><CGI_MESSAGES status="SUCCEEDED"><DATA ></DATA></CGI_MESSAGES></ROOT>
    # GET
    #
    def deleteProvisioning(self):

        if self.mainId and re.match("^[0-9A-Za-z@_\-.]*$", self.mainId):
            self.myFields['email'] = self.mainId
        else:
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyE']['code'],
                self.appConfig['statusCode']['invalidKeyE']['message'])

        if 'endActivationDate' not in self.myFields:
            self.myFields['endActivationDate'] = time.strftime('%Y-%m-%d')

        return self.requestRest('%sDeactivateAccount.cgi' % (self.urlRestBase))

    # https://hero.puresight.com/src/Manage/ProductAdmin/DeleteAccount.cgi?adminUser=FAST-jh87tFFrD&adminPassword=ghEEw3218&email=marco@fs.com
    # Funcao para incluir uma licensa ah um clientes
    # resquest de Retorno de sucesso
    # 200 - <ROOT><CGI_MESSAGES status="SUCCEEDED"><DATA ></DATA></CGI_MESSAGES></ROOT>
    # GET
    #
    def postLicenses(self):

        if self.mainId and re.match("^[0-9A-Za-z@_\-.]*$", self.mainId):
            self.myFields['email'] = self.mainId
        else:
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyE']['code'],
                self.appConfig['statusCode']['invalidKeyE']['message'])

        # Pega as informacoes do usuario
        self.myFields['showRegistrationAllowed'] = 1
        getUser = self.requestRest('%sUsersStatusReport.cgi' % (self.urlRestBase))

        if not self.myFields['registrationCounter'].isdigit():
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidFields']['code'],
                self.appConfig['statusCode']['invalidFields']['message'])

        if 'data' in getUser:
            licenseSize = int(getUser['data']['registrationAllowed']) - int(self.myFields['registrationCounter'])
            if licenseSize > 0:
                self.myFields['decrease'] = 1
                self.myFields['registrationCounter'] = licenseSize
            elif licenseSize < 0:
                self.myFields['decrease'] = 0
                self.myFields['registrationCounter'] = abs(licenseSize)
            else:
                return {'return': 'OK', 'data': {}}

            return self.requestRest('%sAddRegistrationToAccount.cgi' % (self.urlRestBase))
        else:
            return getUser

    def status(self):

        self.myFields['email'] = '1'
        return self.requestRest('%sUsersStatusReport.cgi' % (self.urlRestBase))
