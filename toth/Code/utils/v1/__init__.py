# -*- coding: utf-8 -*-
#
# FSVAS
#

import logging
import time


class BaseExceptionError(BaseException):

    def __init__(self, code, message, realCode=None, realMessage=None, logLevel=1):
        self.codeException = code
        self.logLevel = logLevel

        # logLevel
        # 1 - error
        # 2 - info
        # 3 - debug
        self.errorException = message

        # Captura o codigo e a msg que vem direto do vendor
        self.realCodeException = realCode
        self.realErrorException = realMessage


# Funcao generica para verificar os campos opcionais
def requiredFields(self, requiredFields, optionalsFields, myFields):

    errorFields = ""
    fullFields = list()

    # Caso o arquivo de conf nao tenha virgula no final dos campos
    # O configobj nao cria uma lista com apenas 1 item
    if myFields and type(myFields) is str:
        myFields = [myFields]

    # Verifica os campos obrigatorios
    if requiredFields and type(requiredFields) is str:
        requiredFields = [requiredFields]

    for rField in requiredFields:
        if rField not in myFields:
            errorFields += ' ' + rField

    if errorFields:
        raise BaseExceptionError(
            self.appConfig['statusCode']['requiredFields']['code'],
            '%s%s' % (self.appConfig['statusCode']['requiredFields']['message'], errorFields))

    # Verifica se tem campos ilegais
    if optionalsFields and type(optionalsFields) is str:
        optionalsFields = [optionalsFields]

    if optionalsFields:
        fullFields += optionalsFields
    if requiredFields:
        fullFields += requiredFields

    for rField in myFields:
        if rField not in fullFields:
            errorFields += ' ' + rField

    if errorFields:
        raise BaseExceptionError(
            self.appConfig['statusCode']['optionalFields']['code'],
            '%s%s' % (self.appConfig['statusCode']['optionalFields']['message'], errorFields))

    return True
#


def setup_logger(logger_name, level=logging.INFO, FormatDevel=True, formatter='[%(levelname)s][%(asctime)s]%(message)s'):
    """
    Multiple file log handler

    :param str logger_name: filename of the log
    :param str log_file: path for the log file
    :param int level: default logging level
    """

    logger_name = ('%s-%s' % (logger_name, time.strftime('%y%m%d')))
    l = logging.getLogger(logger_name)
    l.propagate = False
    if not l.handlers:
        if FormatDevel:
            formatter = '[%(levelname)s][%(asctime)s][{%(pathname)s:%(funcName)s:%(lineno)d}][%(message)s]'
        formatter = logging.Formatter(formatter)

        fileHandler = logging.FileHandler('log/%s.log' % (logger_name), mode='a')
        fileHandler.setFormatter(formatter)

        streamHandler = logging.StreamHandler()

        streamHandler.setFormatter(formatter)
        l.addHandler(streamHandler)

        l.setLevel(level)
        l.addHandler(fileHandler)

    return l
#
