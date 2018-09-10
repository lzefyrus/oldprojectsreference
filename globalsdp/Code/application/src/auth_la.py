from functools import wraps
import logging

# Logging handler
log = logging.getLogger(__name__)


def authenticate_la(get_la_func, log_hash=""):
    """
    Decorator which authenticates user by LA.
    :param la: LA number.
    """
    def wrap(func):
        @wraps(func)
        def wrapped_f(self, *args):

            headers = self.request.headers
            user_key = headers['user-key']
            la = int(get_la_func(self))

            try:
                auth_la = self.application.settings["auth_la"][user_key]

                if la not in auth_la:
                    log.error("Error: Could not authenticate user {0} to LA {1}. "
                              "Operation Hash: {2}."
                              .format(user_key, la, log_hash))
                    return self.error({"success": 0, "message": "Could not authenticate user to LA."})

            except Exception as e:
                log.error("Error: Could not authenticate user {0} to LA {1}. "
                          "Exception: {2}. "
                          "Operation Hash: {3}."
                          .format(user_key, la, e, log_hash))
                return self.error({"success": 0, "message": "Internal error: Could not authenticate user to LA."}, 500)

            return func(self, *args)
        return wrapped_f
    return wrap
