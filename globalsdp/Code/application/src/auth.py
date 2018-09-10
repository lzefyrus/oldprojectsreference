from functools import wraps
import application.settings as settings
import logging
import base64


# Logging handler
log = logging.getLogger(__name__)


def authenticate(func):
    """
    Authenticate decorator.
    """
    @wraps(func)
    def with_authentication(self, *args):
        headers = self.request.headers
        error_list = []
        try:
            user_key = headers['user-key']
        except KeyError:
            error_list.append('user-key')
        try:
            user_secret = headers['user-secret']
        except KeyError:
            error_list.append('user-secret')
        try:
            tunnel_key = headers['tunnel-key']
        except KeyError:
            error_list.append('tunnel-key')

        if error_list:
            log.error("Authentication failed! There are missing parameters: {0}".format(error_list))
            return self.error({"message": "Authentication failed! There are missing parameters: {0}"
                              .format(error_list)}, 401)

        if not is_authenticated(self.application.settings["auth"], user_key, user_secret, tunnel_key, self.__urls__[0]):
            log.warning("Authentication failed! Wrong user-key/user-secret combination or user-key not allowed for "
                        "this tunnel-key: {0}|{1}|{2}".format(user_key, user_secret, tunnel_key))
            return self.error({"message": "Could not authenticate"}, 401)

        return func(self, *args)
    return with_authentication


def is_authenticated(settings, user_key, user_secret, tunnel_key, tunnel_url):
    """
    Authenticates user by his key, secret and tunnel.
    :param settings:
    :param user_key:
    :param user_secret:
    :param tunnel_key:
    :param tunnel_url:
    :return: boolean
    """
    try:
        key = "{0}-{1}-{2}".format(user_key, user_secret, tunnel_key)
        return settings[key] == tunnel_url.replace('(?:/)?', '').rstrip('/')
    except KeyError:
        return False


def internal(func):
    """
    Internal URLs decorator.
    """
    @wraps(func)
    def with_authentication(self):
        headers = self.request.headers
        try:
            internal_secret = headers['internal-secret']
        except KeyError:
            log.error("Missing internal-secret! Unreachable internal method")
            return self.error({"message": "Could not find credential: internal-secret"}, 401)

        if not is_internal(internal_secret):
            log.warning("Wrong internal_secret! Unreachable internal method")
            return self.error({"message": "Could not authenticate"}, 401)

        return func(self)
    return with_authentication


def is_internal(internal_secret):
    """
    Matches internal-secret HTTP Header.
    :param internal_secret:
    :return: boolean
    """
    return internal_secret == settings.INTERNAL_SECRET


def basic_auth(auth_func=lambda *args, **kwargs: True, after_login_func=lambda *args, **kwargs: None, realm='Restricted'):
    def basic_auth_decorator(handler_class):
        def wrap_execute(handler_execute):
            def require_basic_auth(handler, kwargs):
                def create_auth_header():
                    handler.set_status(401)
                    handler.set_header('WWW-Authenticate', 'Basic realm=%s' % realm)
                    handler._transforms = []
                    handler.finish()

                auth_header = handler.request.headers.get('Authorization')

                if auth_header is None or not auth_header.startswith('Basic '):
                    create_auth_header()
                else:
                    auth_decoded = base64.decodestring(bytes(auth_header[6:], 'ascii'))
                    user, pwd = auth_decoded.decode('ascii').split(':', 2)

                    if auth_func(handler, user, pwd):
                        after_login_func(handler, kwargs, user, pwd)
                    else:
                        create_auth_header()

            def _execute(self, transforms, *args, **kwargs):
                require_basic_auth(self, kwargs)
                return handler_execute(self, transforms, *args, **kwargs)

            return _execute

        handler_class._execute = wrap_execute(handler_class._execute)
        return handler_class
    return basic_auth_decorator
