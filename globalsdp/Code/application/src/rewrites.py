########################################################
############## TORNADO_JSON ############################
########################################################
import pyclbr
import pkgutil
import importlib
from jsonschema import ValidationError
from tornado_json.exceptions import APIError
from tornado_json.requesthandlers import BaseHandler
from itertools import chain
from functools import reduce
from tornado_json.utils import extract_method, is_method
from types import FunctionType
from tornado.util import unicode_type
from tornado import escape
from tornado.escape import utf8
from lxml import etree
import tornado.web
from tornado_json.api_doc_gen import api_doc_gen
from tornado_json.constants import TORNADO_MAJOR


class Application(tornado.web.Application):
    """Entry-point for the app

    - Generate API documentation using provided routes
    - Initialize the application

    :type  routes: [(url, RequestHandler), ...]
    :param routes: List of routes for the app
    :type  settings: dict
    :param settings: Settings for the app
    :param  db_conn: Database connection --> changed to db
    """

    def __init__(self, routes, settings, db=None):
        # Generate API Documentation
        api_doc_gen(routes)

        # Unless compress_response was specifically set to False in
        # settings, enable it
        compress_response = "compress_response" if TORNADO_MAJOR >= 4 else "gzip"
        if compress_response not in settings:
            settings[compress_response] = True

        tornado.web.Application.__init__(
            self,
            routes,
            **settings
        )

        self.db = db


class SDPMixin(object):
    """Rewrites JSendMixin class from tornado_json.jsend.JSendMixin.
    The goal here is to change the response. Make it more flexible.
    """

    def success(self, data, status=200, headers={}):
        """When an API call is successful, the JSend object is used as a simple
        envelope for the results, using the data key.

        :type  data: A JSON-serializable object
        :param data: Acts as the wrapper for any data returned by the API
            call. If the call returns no data, data should be set to null.
        """
        self.set_status(status)
        self.set_headers(headers)
        self.write(data)
        self.finish()

    def fail(self, data, status=400, headers={}):
        """There was a problem with the data submitted, or some pre-condition
        of the API call wasn't satisfied.

        :type  data: A JSON-serializable object
        :param data: Provides the wrapper for the details of why the request
            failed. If the reasons for failure correspond to POST values,
            the response object's keys SHOULD correspond to those POST values.
        """
        self.set_status(status)
        self.set_headers(headers)
        self.write(data)
        self.finish()

    def error(self, data, status=400, headers={}):
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
        self.set_status(status)
        self.set_headers(headers)
        self.write(data)
        self.finish()


class APIHandler(BaseHandler, SDPMixin):
    """Rewrites APIHandler class from tornado_json.requesthandlers.APIHandler.
    The only change is that APIHandler now inherits from BaseHandler and SDPMixin, and not from
    BaseHandler and JSendMixin as default.
    """

    def initialize(self):
        """
        - Set Content-type for JSON
        """
        self.set_header("Content-Type", "application/json")

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
        exception = kwargs["exc_info"][1]
        if any(isinstance(exception, c) for c in [APIError, ValidationError]):
            # ValidationError is always due to a malformed request
            if isinstance(exception, ValidationError):
                self.set_status(400)
            self.fail(get_exc_message(exception))
        else:
            self.error(
                message=self._reason,
                data=get_exc_message(exception) if self.settings.get("debug")
                else None,
                code=status_code
            )

    def write(self, chunk):
        """Writes the given chunk to the output buffer.

        To write the output to the network, use the flush() method below.

        If the given chunk is a dictionary, we write it as JSON and set
        the Content-Type of the response to be ``application/json``.
        (if you want to send JSON as a different ``Content-Type``, call
        set_header *after* calling write()).

        Note that lists are not converted to JSON because of a potential
        cross-site security vulnerability.  All JSON output should be
        wrapped in a dictionary.  More details at
        http://haacked.com/archive/2009/06/25/json-hijacking.aspx/ and
        https://github.com/facebook/tornado/issues/1009
        """
        if self._finished:
            raise RuntimeError("Cannot write() after finish()")
        if not isinstance(chunk, (bytes, unicode_type, dict)):
            message = "write() only accepts bytes, unicode, and dict objects"
            if isinstance(chunk, list):
                message += ". Lists not accepted for security reasons; see http://www.tornadoweb.org/en/stable/web.html#tornado.web.RequestHandler.write"
            raise TypeError(message)
        if isinstance(chunk, dict):
            chunk = escape.json_encode(chunk)
            self.set_header("Content-Type", "application/json; charset=UTF-8")
        elif isinstance(chunk, str) and chunk.startswith('<?xml'):
            self.set_header("Content-Type", "application/xml; charset=UTF-8")
        else:
            try:
                etree.XML(chunk)
                self.set_header("Content-Type", "application/xml; charset=UTF-8")
            except:
                self.set_header("Content-Type", "text/plain; charset=UTF-8")

        chunk = utf8(chunk)
        self._write_buffer.append(chunk)

    def set_headers(self, headers):
        """
        Sets headers in batch.

        :type  headers: dict
        :param headers: A dict containing all response headers.
        """
        if not isinstance(headers, dict):
            raise Exception("headers parameter must be a dict")

        for key, value in headers.items():
            self.set_header(key, value)


# Feature which imports all SOAP routes (Classes that extend SoapHandler)
def get_soap_routes(package):
    """
    This will walk ``package`` and generates routes from any and all
    ``APIHandler`` and ``ViewHandler`` subclasses it finds. If you need to
    customize or remove any routes, you can do so to the list of
    returned routes that this generates.

    :type  package: package
    :param package: The package containing RequestHandlers to generate
        routes from
    :returns: List of routes for all submodules of ``package``
    :rtype: [(url, RequestHandler), ... ]
    """
    return list(chain(*[get_soap_module_routes(modname) for modname in
                        gen_soap_submodule_names(package)]))


def gen_soap_submodule_names(package):
    """Walk package and yield names of all submodules

    :type  package: package
    :param package: The package to get submodule names of
    :returns: Iterator that yields names of all submodules of ``package``
    :rtype: Iterator that yields ``str``
    """
    for importer, modname, ispkg in pkgutil.walk_packages(
            path=package.__path__,
            prefix=package.__name__ + '.',
            onerror=lambda x: None):
        yield modname


def get_soap_module_routes(module_name, custom_routes=None, exclusions=None):
    """Create and return routes for module_name

    Routes are (url, RequestHandler) tuples

    :returns: list of routes for ``module_name`` with respect to ``exclusions``
        and ``custom_routes``. Returned routes are with URLs formatted such
        that they are forward-slash-separated by module/class level
        and end with the lowercase name of the RequestHandler (it will also
        remove 'handler' from the end of the name of the handler).
        For __example__, a requesthandler with the name
        ``helloworld.api.HelloWorldHandler`` would be assigned the url
        ``/api/helloworld``.
        Additionally, if a method has extra arguments aside from ``self`` in
        its signature, routes with URL patterns will be generated to
        match ``r"(?P<{}>[a-zA-Z0-9_]+)".format(argname)`` for each
        argument. The aforementioned regex will match ONLY values
        with alphanumeric+underscore characters.
    :rtype: [(url, RequestHandler), ... ]
    :type  module_name: str
    :param module_name: Name of the module to get routes for
    :type  custom_routes: [(str, RequestHandler), ... ]
    :param custom_routes: List of routes that have custom URLs and therefore
        should be automagically generated
    :type  exclusions: [str, str, ...]
    :param exclusions: List of RequestHandler names that routes should not be
        generated for
    """

    def has_method(module, cls_name, method_name):
        return all([
            method_name in vars(getattr(module, cls_name)),
            is_method(reduce(getattr, [module, cls_name, method_name]))
        ])

    def yield_args(module, cls_name, method_name):
        """Get signature of ``module.cls_name.method_name``

        Confession: This function doesn't actually ``yield`` the arguments,
            just returns a list. Trust me, it's better that way.

        :returns: List of arg names from method_name except ``self``
        :rtype: list
        """
        wrapped_method = reduce(getattr, [module, cls_name, method_name])
        method = extract_method(wrapped_method)
        argspec_args = getattr(method, "__argspec_args",
                               inspect.getargspec(method).args)

        return [a for a in argspec_args if a not in ["self"]]

    def generate_auto_route(module, module_name, cls_name, method_name, url_name):
        """Generate URL for auto_route

        :rtype: str
        :returns: Constructed URL based on given arguments
        """

        def get_handler_name():
            """Get handler identifier for URL

            For the special case where ``url_name`` is
            ``__self__``, the handler is named a lowercase
            value of its own name with 'handler' removed
            from the ending if give; otherwise, we
            simply use the provided ``url_name``
            """
            if url_name == "__self__":
                if cls_name.lower().endswith('handler'):
                    return cls_name.lower().replace('handler', '', 1)
                return cls_name.lower()
            else:
                return url_name

        def get_arg_route():
            """Get remainder of URL determined by method argspec

            :returns: Remainder of URL which matches `\w+` regex
                with groups named by the method's argument spec.
                If there are no arguments given, returns ``""``.
            :rtype: str
            """
            if yield_args(module, cls_name, method_name):
                return "/{}/?$".format("/".join(
                    ["(?P<{}>[a-zA-Z0-9_]+)".format(argname) for argname
                     in yield_args(module, cls_name, method_name)]
                ))
            return r"/?"

        return "/{}/{}{}".format(
            "/".join(module_name.split(".")[1:]),
            get_handler_name(),
            get_arg_route()
        )

    if not custom_routes:
        custom_routes = []
    if not exclusions:
        exclusions = []

    module = importlib.import_module(module_name)
    custom_routes_s = [c.__name__ for r, c in custom_routes]
    rhs = pyclbr.readmodule(module_name)

    auto_routes = list(chain(*[
        list(set(chain(*[
            [
                (
                    generate_auto_route(
                        module, module_name, cls_name, method_name, url_name
                    ),
                    getattr(module, cls_name)
                ) for url_name in getattr(module, cls_name).__url_names__
                ] + [
                (
                    url,
                    getattr(module, cls_name)
                ) for url in getattr(module, cls_name).__urls__
                ]

            # Rewrite happens here: Search for any method within SoapHandler Class, not only for HTTP_METHODS as it normally does.
            for method_name in [x for x, y in (getattr(module, cls_name)).__dict__.items() if type(y) == FunctionType]
            if has_method(
                module, cls_name, method_name)
            ])))
        for cls_name, cls in rhs.items()
        if is_soap_handler_subclass(cls)
        and cls_name not in (custom_routes_s + exclusions)
        ]))

    routes = auto_routes + custom_routes
    return routes

# Now looking for any SoapHandler subclasses
def is_soap_handler_subclass(cls, classnames=("SoapHandler",)):
    """Determines if ``cls`` is indeed a subclass of ``classnames``

    This function should only be used with ``cls`` from ``pyclbr.readmodule``
    """
    if isinstance(cls, pyclbr.Class):
        return is_soap_handler_subclass(cls.super)
    elif isinstance(cls, list):
        return any(is_soap_handler_subclass(s) for s in cls)
    elif isinstance(cls, str):
        return cls in classnames
    else:
        raise TypeError(
            "Unexpected pyclbr.Class.super type `{}` for class `{}`".format(
                type(cls),
                cls
            )
        )


########################################################
############## TORNADO_WS ##############################
########################################################

from tornadows.soaphandler import SoapHandler
from tornado.options import options
import tornado.httpserver
from tornadows import wsdl as tornadowsdl
import inspect
from tornadows import xmltypes
from tornadows import complextypes
import tornado.web
from tornadows.soaphandler import soapfault

wsdl_path = None


def wsdl(*params, **kwparams):
    """ Decorator method for web services operators """

    def method(f):
        _input = None
        _output = None
        _inputArray = False
        _outputArray = False
        _args = None

        if len(kwparams):
            # Treating _params
            _params = kwparams['_params']

            # The rewrite happens here
            _args = kwparams['_args']

            # _params is a class
            if inspect.isclass(_params) and issubclass(_params, complextypes.ComplexType):
                _input = _params

            # _params is a list
            elif isinstance(_params, list):
                _input = {}
                i = 0
                for arg in _args:
                    _input[arg] = _params[i]
                    i += 1

            # other
            else:
                _input = {}
                for arg in _args:
                    _input[arg] = _params
                if isinstance(_params, xmltypes.Array):
                    _inputArray = True

            # Treating _returns
            _returns = kwparams['_returns']

            # _returns is an array
            if isinstance(_returns, xmltypes.Array):
                _output = _returns
                _outputArray = True

            # _returns is a list, a primitive or a complex type
            elif isinstance(_returns, list) or issubclass(_returns, xmltypes.PrimitiveType) or issubclass(_returns,
                                                                                                          complextypes.ComplexType):
                _output = _returns

            # other
            else:
                _output = _returns

        def operation(*args, **kwargs):
            return f(*args, **kwargs)

        # funcion name
        # The rewrite happens here
        operation.__name__ = kwparams['_name']

        # bool
        operation._is_operation = True

        # function parameters
        operation._args = _args

        # function parameters types
        operation._input = _input

        # function return type
        operation._output = _output

        # funcion name
        operation._operation = kwparams['_name']

        # boolean
        operation._inputArray = _inputArray

        # boolean
        operation._outputArray = _outputArray

        return operation

    return method


import xml.dom.minidom
from tornadows import soap

class SoapHandler(SoapHandler, SDPMixin):
    """ Rewrites Tornado-WS SoapHandler.
    """
    __url_names__ = ["__self__"]

    def get(self):
        """ GET method is executed when the WSDL link is called.
        """

        # Defines the HOST i.e. address = 'localhost'
        if hasattr(options, 'wsdl_hostname') and type(options.wsdl_hostname) is str:
            address = options.wsdl_hostname
        else:
            address = getattr(self, 'targetns_address',
                              tornado.httpserver.socket.gethostbyname(tornado.httpserver.socket.gethostname()))

        # Defines the PORT i.e. port = '8887'
        port = 80
        if len(self.request.headers['Host'].split(':')) >= 2:
            port = self.request.headers['Host'].split(':')[1]

        # Defines the NAMESERVICE i.e. wsdl_nameservice = 'tim/v1/recharge'
        wsdl_nameservice = self.request.uri[1:].replace('?wsdl', '').replace('?WSDL', '')
        wsdl_input = None
        wsdl_output = None
        wsdl_operation = None
        wsdl_args = None
        wsdl_methods = []

        # Iterates over all methods of the current Handler
        for operations in dir(self):
            operation = getattr(self, operations)

            if callable(operation) and hasattr(operation, '_input') and hasattr(operation, '_output') and hasattr(
                    operation, '_operation') \
                    and hasattr(operation, '_args') and hasattr(operation, '_is_operation'):
                wsdl_input = getattr(operation, '_input')
                wsdl_output = getattr(operation, '_output')
                wsdl_operation = getattr(operation, '_operation')
                wsdl_args = getattr(operation, '_args')
                wsdl_data = {'args': wsdl_args,
                             'input': ('params', wsdl_input),
                             'output': ('returns', wsdl_output),
                             'operation': wsdl_operation}
                wsdl_methods.append(wsdl_data)

        # Target Namespace
        wsdl_targetns = 'http://%s:%s/%s' % (address, port, wsdl_nameservice)
        wsdl_location = 'http://%s:%s/%s' % (address, port, wsdl_nameservice)

        # Content-Type
        self.set_header('Content-Type', 'application/xml; charset=UTF-8')

        # QueryString (?wsdl)
        query = self.request.query
        if query.upper() == 'WSDL':

            # Normally goes here
            if wsdl_path == None:

                # Makes the WSDL XML
                wsdlfile = tornadowsdl.Wsdl(nameservice=wsdl_nameservice,
                                            targetNamespace=wsdl_targetns,
                                            methods=wsdl_methods,
                                            location=wsdl_location)

                self.finish(wsdlfile.createWsdl().toxml())
            else:
                fd = open(str(wsdl_path), 'r')
                xmlWSDL = ''
                for line in fd:
                    xmlWSDL += line
                fd.close()
                self.finish(xmlWSDL)

    # @tornado.web.asynchronous
    def post(self):
        """ POST method is executed when SOAP services are called.
        """

        def done(response):
            soapmsg = response.getSoap().toxml()
            self.write(soapmsg)
            # self.finish()

        try:
            self._request = self._parseSoap(self.request.body)
            soapaction = self.request.headers['SOAPAction'].replace('"', '')
            self.set_header('Content-Type', 'text/xml')
            for operations in dir(self):
                operation = getattr(self, operations)
                method = ''
                if callable(operation) and hasattr(operation, '_is_operation'):
                    num_methods = self._countOperations()
                    if hasattr(operation, '_operation') \
                            and soapaction.endswith(getattr(operation, '_operation')) \
                            and num_methods > 1:
                        method = getattr(operation, '_operation')
                        self._executeOperation(operation, done, method=method)
                        break
                    elif num_methods == 1:
                        self._executeOperation(operation, done, method='')
                        break

        except Exception as detail:
            fault = soapfault('Error in web service : %s' % detail)
            self.set_status(500)
            self.write(fault.getSoap().toxml())

        finally:
            pass
            # self.finish()


class WebService(tornado.web.Application):
    """ A implementation of web services for tornado web server.

        import tornado.httpserver
        import tornado.ioloop
        from tornadows import webservices
        from tornadows import xmltypes
        from tornadows import soaphandler
        from tornadows.soaphandler import webservice

        class MyService(soaphandler.SoapHandler):
            @webservice(_params=[xmltypes.Integer, xmltypes.Integer],_returns=xmltypes.Integer)
            def sum(self, value1, value2):
                result = value1 + value2

                return result

        if __name__ == "__main__":
            app = webservices.WebService("MyService",MyService)
            ws_server = tornado.httpserver.HTTPServer(app)
            ws_server.listen(8080)
            tornado.ioloop.IOLoop.instance().start()

    """
    def __init__(self, services, settings, db=None, object=None, wsdl=None):
        """ Initializes the application for web services

            Instances of this class are callable and can be passed to
            HTTPServer of tornado to serve the web services.

            The constructor for this class takes the name for the web
            service (service), the class with the web service (object)
            and wsdl with the wsdl file path (if this exist).
         """
        if isinstance(services, list) and object is None:
            srvs = []
            for s in services:
                srv = s[0]
                obj = s[1]
                srvs.append((r"/"+str(srv), obj))
                srvs.append((r"/"+str(srv)+"/", obj))
            tornado.web.Application.__init__(self, srvs, **settings)
        else:
            self._service = services
            self._object = object
            self._services = [(r"/"+str(self._service), self._object),
                      (r"/"+str(self._service)+"/", self._object), ]
            tornado.web.Application.__init__(self, self._services, **settings)

        self.db = db
