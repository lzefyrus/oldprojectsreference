# -*- coding: utf-8 -*-
#
# FSVAS
#

import os
from xml.dom import minidom
import re
from jinja2 import Environment, FileSystemLoader

# Classe de provisionaonamento
from provisioner.v2 import Provisioner


class Mcafee(Provisioner):

    def prepare(self):
        super(Mcafee, self).prepare()

        # Caminho real dos arquivos
        path, fileName = os.path.split(os.path.realpath(__file__))
        templateLoader = FileSystemLoader(searchpath='%s/wsdl/' % (path))
        templateEnv = Environment(loader=templateLoader)
        self.template = templateEnv.get_template('mcafee.xml')

    def requestRest(self, paramsXml):

        # Funcoes do WSDL
        self.wsdlClientes = self.wsdlClientes[self.operator][self.vendor]
        self.log.info('%s[REQUEST - WSDL %s SOAP]' % (self.msgLog, self.urlWsdl))
        self.log.debug('%s[REQUEST XML: %s' % (self.msgLog, paramsXml))

        # methodo para verificar os campos obrigatorios do methodo do vendors
        self.utils.requiredFields(self, self.paramRequiredField, self.paramOptionalsField, self.myFields.keys())

        self.log.debug('%s[REQUEST FIELDS: %s]' % (self.msgLog, self.myFields))
        message = ""
        try:
            status, result = self.wsdlClientes.service.ProcessRequestWS(paramsXml)
            self.log.debug('%s[%s] - %s' % (self.msgLog, status, result))

        except Exception as e:
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['vendorError']['code'],
                str(e))

        code = self.appConfig['statusCode']['vendorDbError']['code']
        message = self.appConfig['statusCode']['vendorDbError']['message']
        logLevel = 1

        if status == 200:
            # Pega o resultado em xml e transforma em json
            xmlparse = minidom.parseString(result)
            returnCode = xmlparse.getElementsByTagName('RETURNCODE')[0]
            returnMsg = xmlparse.getElementsByTagName('RETURNDESC')[0]

            if returnCode.firstChild.data not in ['1000', '5001', '5002']:
                message = returnMsg.firstChild.data
                if returnCode.firstChild.data == '10000':
                    code = self.appConfig['statusCode']['userNotFound']['code']
                    message = self.appConfig['statusCode']['userNotFound']['message']
                    logLevel = 2
            else:
                # adiciona um return OK
                dictReturn = {'return': 'OK', 'data': {}}

                if returnCode.firstChild.data in ['5001', '5002']:
                    dictReturn['data']['warning'] = returnMsg.firstChild.data

                if xmlparse.getElementsByTagName('ORDER'):
                    data = xmlparse.getElementsByTagName('ORDER')

                    # pega o status caso seja um get
                    if 'PARTNERREF' in data[0].attributes:
                        dictReturn['data']['partnerref'] = data[0].attributes['PARTNERREF'].value
                    if 'REF' in data[0].attributes:
                        dictReturn['data']['ref'] = data[0].attributes['REF'].value
                    if xmlparse.getElementsByTagName('PRODUCTDOWNLOADURL'):
                        urlDownload = xmlparse.getElementsByTagName('PRODUCTDOWNLOADURL')[0]
                        dictReturn['data']['urlDownload'] = urlDownload.firstChild.data

                if xmlparse.getElementsByTagName('PRODUCTKEY'):
                    for item in xmlparse.getElementsByTagName('PRODUCTKEY'):
                        dictReturn['data']['productkey'] = item.firstChild.data

                return dictReturn

        raise self.utils.BaseExceptionError(
            code,
            message,
            status,
            result,
            logLevel)

    #
    # Funcao para incluir clientes
    # resquest de Retorno de sucesso
    # 200
    # POST
    #
    def postProvisioning(self):

        if self.mainId and re.match("^[A-Za-z0-9]*$", self.mainId):
            self.myFields['id'] = self.mainId
        else:
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyA']['code'],
                self.appConfig['statusCode']['invalidKeyA']['message'])

        self.myFields['requesttype'] = 'New'
        self.myFields['action'] = 'PD'
        self.myFields['qty_item'] = 'QTY="1"'
        self.myFields['license_size'] = 'LIC_QTY="%s"' % self.myFields['license_size']

        return self.requestRest(self.template.render(**self.myFields))

    #
    # Funcao para ataulizar um cliente
    # resquest de Retorno de sucesso
    # 200
    # GET
    #
    def putProvisioning(self):

        if self.mainId and re.match("^[A-Za-z0-9]*$", self.mainId):
            self.myFields['id'] = self.mainId
        else:
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyA']['code'],
                self.appConfig['statusCode']['invalidKeyA']['message'])

        self.myFields['requesttype'] = 'UPDATE'
        self.myFields['action'] = 'UD'
        self.myFields['qty_item'] = 'QTY="1"'
        self.myFields['license_size'] = 'LIC_QTY="%s"' % self.myFields['license_size']

        return self.requestRest(self.template.render(**self.myFields))

    #
    # Funcao para desativar um cliente
    # resquest de Retorno de sucesso
    # 200
    # GET
    #
    def deleteProvisioning(self):

        if self.mainId and re.match("^[A-Za-z0-9]*$", self.mainId):
            self.myFields['id'] = self.mainId
        else:
            raise self.utils.BaseExceptionError(
                self.appConfig['statusCode']['invalidKeyA']['code'],
                self.appConfig['statusCode']['invalidKeyA']['message'])

        self.myFields['requesttype'] = 'UPDATE'
        self.myFields['action'] = 'CN'

        return self.requestRest(self.template.render(**self.myFields))
