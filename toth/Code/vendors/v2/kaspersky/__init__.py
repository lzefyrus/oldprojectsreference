# -*- coding: utf-8 -*-
#
# FSVAS
#
import re
import datetime
from uuid import uuid4
import time

# Classe de provisionaonamento
from provisioner.v2 import Provisioner


class Kaspersky(Provisioner):

    def prepare(self):
        super(Kaspersky, self).prepare()
        # Funcoes do WSDL
        self.wsdlClientes = self.wsdlClientes[self.operator][self.vendor]
        self.objRequest = self.wsdlClientes.factory.create('SubscriptionRequestItemCollection')

    def requestRest(self):

        self.log.info('%s[REQUEST - WSDL %s SOAP in %s]' % (self.msgLog, self.urlWsdl, self.urlRestBase))

        # methodo para verificar os campos obrigatorios do methodo do vendors
        self.utils.requiredFields(self, self.paramRequiredField, self.paramOptionalsField, self.myFields.keys())

        self.log.debug('%s[REQUEST FIELDS: %s]' % (self.msgLog, self.myFields))

        # Login e senha para o wsdl
        token = self.wsdlClientes.factory.create('AccessInfo')
        token.UserName = self.loginRest
        token.Password = self.senhaRest
        self.wsdlClientes.set_options(soapheaders=token)
        try:
            timeStamp = datetime.datetime.now() - datetime.timedelta(hours=3)
            status, result = self.wsdlClientes.service.SubscriptionRequest(timeStamp, str(uuid4()), self.objRequest)
            self.log.debug('%s[%s] - %s' % (self.msgLog, status, result))

        except Exception as e:
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['vendorDbError']['code'],
                str(e))

        code = self.appConfig['statusCode']['vendorError']['code']
        message = self.appConfig['statusCode']['vendorError']['message']
        logLevel = 2

        resultError = dict(Timestamp=result['Timestamp'].strftime('%Y-%m-%d %H:%M:%S'), TransactionId=result['TransactionId'])
        if status == 200:
            if 'TransactionError' in result:
                message = result['TransactionError']['_ErrorMessage']
                logLevel = 1
                resultError['TransactionError'] = result['TransactionError']
            elif 'SubscriptionError' in result:

                for key, error in result['SubscriptionError']:
                    # resultError[key] = error[0].key
                    resultError[key] = error[0]
                    message = error[0]._ErrorMessage
                    codeErro = error[0]._ErrorCode

                # User not Found
                if codeErro == 5:
                    logLevel = 2
                    code = self.appConfig['statusCode']['userNotFound']['code']
                    message = self.appConfig['statusCode']['userNotFound']['message']
            else:
                # adiciona um return OK
                dictReturn = {'return': 'OK', 'data': {
                    'Timestamp': result['Timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                    'TransactionId': result['TransactionId']}}

                for key, sucess in result['SubscriptionResponse']:
                    if hasattr(sucess[0], '_SubscriberId'):
                        dictReturn['data']['SubscriberId'] = sucess[0]._SubscriberId
                    if hasattr(sucess[0], '_UnitId'):
                        dictReturn['data']['UnitId'] = sucess[0]._UnitId
                    if hasattr(sucess[0], '_ActivationCode'):
                        dictReturn['data']['ActivationCode'] = sucess[0]._ActivationCode

                # GetInfo, fora do padrao
                if 'GetInfo' in result['SubscriptionResponse']:
                    for key, sucess in result['SubscriptionResponse']:
                        if hasattr(sucess, '_SubscriberId'):
                            dictReturn['data']['SubscriberId'] = sucess._SubscriberId
                        if hasattr(sucess, '_UnitId'):
                            dictReturn['data']['UnitId'] = sucess._UnitId
                        if hasattr(sucess['Subscription'][0], '_Status'):
                            dictReturn['data']['Status'] = sucess['Subscription'][0]._Status
                        if hasattr(sucess['Subscription'][0], '_EndTime'):
                            dictReturn['data']['EndTime'] = sucess['Subscription'][0]._EndTime.strftime('%Y-%m-%d %H:%M:%S')\
                             if type(sucess['Subscription'][0]._EndTime) == 'datetime.datetime' else sucess['Subscription'][0]._EndTime
                        if hasattr(sucess['Subscription'][0], '_StartTime'):
                            dictReturn['data']['StartTime'] = sucess['Subscription'][0]._StartTime.strftime('%Y-%m-%d %H:%M:%S')
                        if hasattr(sucess['Subscription'][0], '_StatusChangeTime'):
                            dictReturn['data']['StatusChangeTime'] = sucess['Subscription'][0]._StatusChangeTime.strftime('%Y-%m-%d %H:%M:%S')
                        if hasattr(sucess['Subscription'][0], '_ActivationCode'):
                            dictReturn['data']['ActivationCode'] = sucess['Subscription'][0]._ActivationCode
                        if hasattr(sucess['Subscription'][0], '_LicenseCount'):
                            dictReturn['data']['LicenseCount'] = sucess['Subscription'][0]._LicenseCount
                        if hasattr(sucess['Subscription'][0], '_ProductId'):
                            dictReturn['data']['ProductId'] = sucess['Subscription'][0]._ProductId

                return dictReturn

        raise self.utils.BaseExceptionError(
            code,
            message,
            status,
            str(resultError),
            logLevel)

    #
    # Funcao para incluir clientes
    # resquest de Retorno de sucesso
    # 200
    # POST
    #
    def getProvisioning(self):

        if not self.mainId or not re.match("^[A-Za-z0-9]*$", self.mainId):
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyA']['code'],
                self.appConfig['statusCode']['invalidKeyA']['message'])

        objGetInfo = self.wsdlClientes.factory.create('SubscriptionRequestItemCollection.GetInfo')

        objGetInfo._UnitId = str(time.time()).split('.')[0]
        objGetInfo._SubscriberId = self.mainId

        self.objRequest.GetInfo = [objGetInfo]

        return self.requestRest()

    #
    # Funcao para incluir clientes
    # resquest de Retorno de sucesso
    # 200
    # POST
    #
    def postProvisioning(self):

        if not self.mainId or not re.match("^[A-Za-z0-9]*$", self.mainId):
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyA']['code'],
                self.appConfig['statusCode']['invalidKeyA']['message'])

        startTime = datetime.datetime.now() - datetime.timedelta(hours=3)

        objActivate = self.wsdlClientes.factory.create('SubscriptionRequestItemCollection.Activate')

        objActivate._UnitId = str(time.time()).split('.')[0]
        objActivate._SubscriberId = self.mainId
        objActivate._StartTime = startTime  # startTime.strftime('%Y-%m-%d\T%H:%M:%S')
        objActivate._EndTime = 'indefinite'
        objActivate._LicenseCount = 1 if 'LicenseCount' not in self.myFields.keys() else int(self.myFields['LicenseCount'])
        objActivate._ProductId = self.myFields['ProductId'] if 'ProductId' in self.myFields.keys() else ''

        self.objRequest.Activate = [objActivate]

        return self.requestRest()

    #
    # Funcao para ataulizar um cliente
    # resquest de Retorno de sucesso
    # 200
    # GET
    #
    def putProvisioning(self):

        if not self.mainId or not re.match("^[A-Za-z0-9]*$", self.mainId):
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyA']['code'],
                self.appConfig['statusCode']['invalidKeyA']['message'])

        if 'typeChange' in self.myFields and self.myFields['typeChange'] in ['1', '2', '3', '4']:

            # Update de licencas
            if self.myFields['typeChange'] == '1':

                # Primeiro envia um Hard Cancel
                objDelete = self.wsdlClientes.factory.create('SubscriptionRequestItemCollection.HardCancel')
                objDelete._UnitId = str(time.time()).split('.')[1]
                objDelete._SubscriberId = self.mainId
                endTime = datetime.datetime.now() - datetime.timedelta(hours=3)
                objDelete._EndTime = endTime
                self.objRequest.HardCancel = [objDelete]

                objUpdate = self.wsdlClientes.factory.create('SubscriptionRequestItemCollection.Activate')
                startTime = datetime.datetime.now() - datetime.timedelta(hours=3)
                objUpdate._UnitId = str(time.time()).split('.')[0]
                objUpdate._SubscriberId = self.mainId
                objUpdate._StartTime = startTime  # startTime.strftime('%Y-%m-%d\T%H:%M:%S')
                objUpdate._EndTime = 'indefinite'
                objUpdate._LicenseCount = 1 if 'LicenseCount' not in self.myFields.keys() else int(self.myFields['LicenseCount'])
                objUpdate._ProductId = self.myFields['ProductId'] if 'ProductId' in self.myFields.keys() else ''
                self.objRequest.Activate = [objUpdate]

            # Update de Renew
            elif self.myFields['typeChange'] == '2':
                objUpdate = self.wsdlClientes.factory.create('SubscriptionRequestItemCollection.Renew')
                objUpdate._UnitId = str(time.time()).split('.')[0]
                objUpdate._SubscriberId = self.mainId
                endTime = datetime.datetime.now() - datetime.timedelta(hours=3)
                objUpdate._EndTime = endTime
                self.objRequest.Renew = [objUpdate]
            # Update de Pause
            elif self.myFields['typeChange'] == '3':
                objUpdate = self.wsdlClientes.factory.create('SubscriptionRequestItemCollection.Pause')
                objUpdate._UnitId = str(time.time()).split('.')[0]
                objUpdate._SubscriberId = self.mainId
                pauseTime = datetime.datetime.now() - datetime.timedelta(hours=3)
                objUpdate._PauseTime = pauseTime
                self.objRequest.Pause = [objUpdate]
            # Update de Resume
            elif self.myFields['typeChange'] == '4':
                objUpdate = self.wsdlClientes.factory.create('SubscriptionRequestItemCollection.Resume')
                objUpdate._UnitId = str(time.time()).split('.')[0]
                objUpdate._SubscriberId = self.mainId
                self.objRequest.Resume = [objUpdate]
        else:
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['badRequest']['code'],
                'Invalid typeChange field [1, 2, 3 or 4]')

        return self.requestRest()

    #
    # Funcao para desativar um cliente
    # resquest de Retorno de sucesso
    # 200
    # GET
    #
    def deleteProvisioning(self):

        if not self.mainId or not re.match("^[A-Za-z0-9]*$", self.mainId):
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyA']['code'],
                self.appConfig['statusCode']['invalidKeyA']['message'])

        if 'typeCancel' in self.myFields and self.myFields['typeCancel'] in ['1', '2']:

            if self.myFields['typeCancel'] == '1':
                objDelete = self.wsdlClientes.factory.create('SubscriptionRequestItemCollection.SoftCancel')

                objDelete._UnitId = str(time.time()).split('.')[0]
                objDelete._SubscriberId = self.mainId
                endTime = datetime.datetime.now() - datetime.timedelta(hours=3)
                objDelete._EndTime = endTime
                self.objRequest.SoftCancel = [objDelete]
            else:
                objDelete = self.wsdlClientes.factory.create('SubscriptionRequestItemCollection.HardCancel')
                objDelete._UnitId = str(time.time()).split('.')[0]
                objDelete._SubscriberId = self.mainId
                endTime = datetime.datetime.now() - datetime.timedelta(hours=3)
                objDelete._EndTime = endTime
                self.objRequest.HardCancel = [objDelete]

        else:
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['badRequest']['code'],
                'Invalid typeCancel field [1 or 2]')

        return self.requestRest()

    def status(self):

        objGetInfo = self.wsdlClientes.factory.create('SubscriptionRequestItemCollection.GetInfo')

        objGetInfo._UnitId = str(time.time()).split('.')[0]
        objGetInfo._SubscriberId = '1'

        self.objRequest.GetInfo = [objGetInfo]

        return self.requestRest()
