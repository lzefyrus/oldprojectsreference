# encoding: utf-8


class UnrecorverableFirebaseError(Exception):
    pass


class UnavailableFirebaseServiceError(Exception):

    def __init__(self):
        self.message = "Firebase Cloud Messaging service is not available. Try again later."


class InvalidRequestError(Exception):

    def __init__(self, errors):
        self.message = "Request has been sent with errors"
        self.errors = errors
