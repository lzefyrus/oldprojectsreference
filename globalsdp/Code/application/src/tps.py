from functools import wraps
from application.src import databases
import time
import logging

# Redis session
redis = databases.Redis.get_instance("redis-tps")

# Logging handler
log = logging.getLogger(__name__)


def tps(tps_func):
    """
    TPS control decorator.
    :param tps_func: function which will execute its own implementation of 'available_tps'.
    """
    def wrap(func):
        @wraps(func)
        def wrapped_f(self, *args):

            headers = self.request.headers
            try:
                tunnel_key = headers['tunnel-key']
                tunnel_settings = self.application.settings['tunnel']
            except:
                log.error("Missing tunnel-key or tunnel-key cache.")
                return self.error({"message": "Could not find tunnel."})

            try:
                if not tps_func(redis, tunnel_key, tunnel_settings, self):
                    log.error("TPS not available for tunnel {0}".format(tunnel_key))
                    return self.error({"message": "There is no available TPS."})
            except Exception as e:
                message = "An error occurred while calculating TPS: {0}".format(e)
                log.error(message)
                return self.error({"message": message})

            return func(self, *args)
        return wrapped_f
    return wrap
