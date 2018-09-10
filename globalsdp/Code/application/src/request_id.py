from functools import wraps
import logging
import application.settings as settings
from application.src import databases
from application.src import utils

# Logging handler
log = logging.getLogger(__name__)


def request_id(get_request_uid_func, log_hash=""):
    """
    Creates request_uid inside Redis if it does not exist. It avoids duplicate requests.
    """
    def wrap(func):
        @wraps(func)
        def wrapped_f(self, *args):
            try:
                redis = databases.Redis.get_instance("redis-request-id")
            except Exception as e:
                log.error("Could not send request to partner. Failed to check or create request id. "
                          "Error: {0}. "
                          "Requested URL: {1}. "
                          "Operation Hash: {2}. "
                          .format(e, self.request.uri, log_hash))
                return self.error({"success": 0, "message": "Failed to check or create request id. Request aborted."}, 500)
    
            try:
                uid = get_request_uid_func(self)
                if not uid:
                    log.error("Could not send request to partner. Failed to check or create request id. "
                              "Error: request id is mandatory. "
                              "Requested URL: {0}. "
                              "Operation Hash: {1}. ".format(self.request.uri, log_hash))
                    return self.error({"success": 0,
                                       "message": "Request aborted: request id is mandatory."}, 400)
                request_uid = redis.get(uid)
                request_uid = utils.decode(request_uid) if request_uid else None
                if request_uid == '0':
                    log.error("Could not send request: duplicated operation for request id {0}. "
                              "Requested URL: {1}. "
                              "Operation Hash: {2}. "
                              .format(uid, self.request.uri, log_hash))
                    return self.error({"success": 0,
                                       "message": "Could not send request: duplicated operation for request id {0}. "
                                       .format(uid)
                                       }, 400)
                if request_uid == '1':
                    log.error("Could not send request: operation already successful by request id {0}. "
                              "Requested URL: {1}. "
                              "Operation Hash: {2}. "
                              .format(uid, self.request.uri, log_hash))
                    return self.error(
                        {
                            "success": 0,
                            "message": "Could not send request: operation already successful by request id {0}. "
                            .format(uid)
                        }, 403)

                log.info("Request Id key created with value 0 for uid: {0}. "
                         "Requested URL: {1}. ".format(uid, self.request.uri, log_hash))
                redis.setex(uid, 0, settings.REQUEST_ID_PERIODICITY)
    
            except Exception as e:
                log.error("Could not check or create request id. Request aborted. "
                          "Error: {0}. "
                          "Requested URL: {1}. "
                          "Operation Hash: {2}. ".format(e,  self.request.uri, log_hash))
                return self.error({"success": 0, "message": "Could not check or create request id. Request aborted."}, 500)

            return func(self, *args)
        return wrapped_f
    return wrap
