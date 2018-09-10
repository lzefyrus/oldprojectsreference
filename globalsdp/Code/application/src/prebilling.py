from functools import wraps
import logging
from tornado.escape import json_decode
from application.src import databases
import application.settings as settings

# Logging handler
log = logging.getLogger(__name__)


def prebilling(partner, service, keys, product_field=None):
    """
    Decorator which avoids duplicated charge requests
    :param partner: partner name (ex: vivo, tim, oi)
    :param service: service class instance which will execute 'save' method after finishing prebilling
    :param keys: array containing request parameter names which will form prebilling key on Redis
    :param product_field: request parameter name that represents the product. Used for periodicity cases only.
     If None, prebilling process will work based on request id. Request Id keys will endure forever on Redis.
    """
    def wrap(func):
        @wraps(func)
        def wrapped_f(self, *args):

            def finish_billing(self, service):
                service.save(self.application.settings, json_decode(self.request.body), 0)

            # Getting body
            body = json_decode(self.request.body)
            
            # Logging
            log_hash = settings.LOG_HASHES[partner]["billing"]

            try:
                redis = databases.Redis.get_instance("redis-prebilling")
            except Exception as e:
                finish_billing(self, service)

                log.error("Could not send Billing request to partner {0}. "
                          "Error: {1}. "
                          "Operation Hash: {2}."
                          .format(partner, e, log_hash))
                return self.error({"success": 0, "message": "Could not make double-check (pre-billing). Request aborted."}, 500)

            try:
                key = ''
                for k in keys:
                    key += '{0}:'.format(body[k])
                key = key.rstrip(':')

                if redis.get(key):
                    finish_billing(self, service)

                    reason = "Request Id {} already exists.".format(key) if product_field is None \
                        else "Product already charged for this period"
                    message = "Could not bill: duplicated operation. Reason: {0}. Operation Hash: {1}. "\
                        .format(reason, log_hash)
                    log.error(message)
                    return self.error({"success": 0, "message": reason})

                if not product_field:
                    redis.set(key, 0)
                else:
                    prebilling = self.application.settings["prebilling"][partner]
                    product = body[str(product_field)]
                    periodicity = prebilling[str(product)]
                    redis.setex(key, 0, periodicity)

            except KeyError as ke:
                finish_billing(self, service)

                log.error("Could not find product {0} for partner {1} inside prebilling settings. "
                          "Error: {2}. "
                          "Operation Hash: {3}."
                          .format(body[product_field], partner, ke, log_hash))
                return self.error({"success": 0, "message": "Could not make double-check (pre-billing). Request aborted."}, 500)

            except Exception as e:
                finish_billing(self, service)

                log.error("Could not make double-check (pre-billing). Request aborted. "
                          "Error: {0}. "
                          "Operation Hash: {1}."
                          .format(e, log_hash))
                return self.error({"success": 0, "message": "Could not make double-check (pre-billing). Request aborted."}, 500)

            return func(self, *args)
        return wrapped_f
    return wrap
