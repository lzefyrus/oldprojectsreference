# -*- encoding: utf-8 -*-

class UnreachableServerException(Exception):
    pass


class InvalidRequestException(Exception):
    pass


class InvalidConnection(Exception):
    pass


class LaNotFoundException(Exception):
    pass


class ProviderCodeNotFoundException(Exception):
    pass


class TpsErrorException(Exception):
    pass


class UnexpectedResponse(Exception):
    pass


class MethodNotImplemented(Exception):
    pass
