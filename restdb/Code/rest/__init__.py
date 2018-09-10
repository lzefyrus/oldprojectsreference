import logging

from tornado_json.requesthandlers import APIHandler
from jsonschema import ValidationError
from tornado_json.exceptions import APIError
from tornado_json.gen import coroutine

from rest.cached_pool import RedisPool
from rest import utils

slog = logging.getLogger('redisdb')


class RestDBAPIHandler(APIHandler):
    def initialize(self, db):
        app = self.application.settings
        slog.debug(app)
        self.redisdb = app.get('redis')
        if not db:
            db = gen_pools(app['config'], app['redis'], app['prddb'])
        self.db = db
        slog.debug(self.db)

    @coroutine
    def success(self, data, simple=False):
        """When an API call is successful, the JSend object is used as a simple
        envelope for the results, using the data key.

        :type  data: A JSON-serializable object
        :param data: Acts as the wrapper for any data returned by the API
            call. If the call returns no data, data should be set to null.
        """
        if not simple:
            self.write({'status': 'success', 'data': data})
        else:
            if type(data) in [dict, list]:
                self.write(data)
            else:
                self.write({'status': 'success', 'data': data})
        self.finish()

    @coroutine
    def fail(self, message, data=None, code=400):
        """An error occurred in processing the request, i.e. an exception was
        thrown.

        :type  data: A JSON-serializable object
        :param data: A generic container for any other information about the
            error, i.e. the conditions that caused the error,
            stack traces, etc.
        :type  message: A JSON-serializable object
        :param message: A meaningful, end-user-readable (or at the least
            log-worthy) message, explaining what went wrong
        :type  code: int
        :param code: A numeric code corresponding to the error, if applicable
        """
        result = {'status': 'fail', 'message': message}
        if data:
            result['data'] = data
        if code:
            result['code'] = code

        if not data:
            self.write_error(code, message=message)
        else:
            self.write_error(code, data=result)
            # self.finish()

    @coroutine
    def write_error(self, status_code, **kwargs):
        """Override of RequestHandler.write_error

        Calls ``error()`` or ``fail()`` from JSendMixin depending on which
        exception was raised with provided reason and status code.

        :type  status_code: int
        :param status_code: HTTP status code
        """

        def get_exc_message(exception):
            return exception.log_message if \
                hasattr(exception, "log_message") else str(exception)

        self.clear()
        self.set_status(status_code)

        # Any APIError exceptions raised will result in a JSend fail written
        # back with the log_message as data. Hence, log_message should NEVER
        # expose internals. Since log_message is proprietary to HTTPError
        # class exceptions, all exceptions without it will return their
        # __str__ representation.
        # All other exceptions result in a JSend error being written back,
        # with log_message only written if debug mode is enabled
        exception = kwargs.get("exc_info", [Exception(kwargs.get('message', self._reason)),
                                            Exception(kwargs.get('message', self._reason))])[1]
        if any(isinstance(exception, c) for c in [APIError, ValidationError]):
            # ValidationError is always due to a malformed request
            if isinstance(exception, ValidationError):
                self.set_status(400)
            self.error(get_exc_message(exception))
        else:
            self.error(
                message=kwargs.get('message', self._reason),
                data=kwargs.get('data', None),
                code=status_code
            )

    def error(self, message, data=None, code=500):
        """An error occurred in processing the request, i.e. an exception was
        thrown.

        :type  data: A JSON-serializable object
        :param data: A generic container for any other information about the
            error, i.e. the conditions that caused the error,
            stack traces, etc.
        :type  message: A JSON-serializable object
        :param message: A meaningful, end-user-readable (or at the least
            log-worthy) message, explaining what went wrong
        :type  code: int
        :param code: A numeric code corresponding to the error, if applicable
        """
        result = {'status': 'error', 'message': message}
        self.set_status(code, message)
        if data:
            result['data'] = data
        if code:
            result['code'] = code
        self.write(result)
        self.finish()


def gen_pools(config, robj, stype=False):
    dbs = {}
    ftype = 'production' if stype is True else 'homol'
    ddb = config['databases'][ftype]

    for db in ddb.items():
        dbs[db[0]] = RedisPool(dict(host=db[1]['host'],
                                    port=3306,
                                    user=db[1]['user'],
                                    passwd=db[1]['pass'],
                                    db=db[1]['db_name'],
                                    connect_timeout=60),
                               max_idle_connections=0,
                               max_open_connections=30,
                               max_recycle_sec=60,
                               redisobj=robj)
    return dbs
