from functools import wraps
import logging


# Logging handler
log = logging.getLogger(__name__)


def authenticate(func):
    """
    Authenticate decorator for Claro requests.
    """
    @wraps(func)
    def with_authentication(self, *args):
        user_id = self.get_argument('userId', None)
        pwd = self.get_argument('pwd', None)

        if None in (user_id, pwd):
            log.warning("Authentication failed! Missing auth parameters")
            return self.error({"message": "Authentication failed! Missing auth parameters"}, 401)

        claro_user = self.settings['config']['claro/v1/user']['value']
        claro_pass = self.settings['config']['claro/v1/password']['value']

        if claro_user != user_id or claro_pass != pwd:
            log.error("Could not authenticate such a combination: userId {0} and pwd {1}".format(user_id, pwd))
            return self.error({"message": "Could not authenticate! Wrong userId/pwd combination"}, 401)

        return func(self, *args)
    return with_authentication
