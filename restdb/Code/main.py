# Skeleton for an OAuth 2 Web Application Server which is an OAuth
# provider configured for Authorization Code, Refresh Token grants and
# for dispensing Bearer Tokens.

# This example is meant to act as a supplement to the documentation,
# see http://oauthlib.readthedocs.org/en/latest/.

import os
import os.path
import logging
from base64 import b64encode
import argparse

from tornado.httpserver import HTTPServer
import tornado
from tornado.ioloop import IOLoop
import tornado.web
from tornado import escape
import configobj
from pycket.session import SessionMixin

from tj_utils import get_routes

# from cached_pool import RedisPool

from rest import utils
import rest

alog = None
slog = None

pool = {}


def main(debug=False, p=False):
    """
    main loop for tornado server
    sets all needed information for running

    :param bool debug: run server in debug or production modes
    """
    config = configobj.ConfigObj('config.ini')
    redisurl = config['redis']['host']
    redisport = config['redis']['port']
    redisdb = config['redis']['db']
    global slog, alog, pool

    urls = [
        (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": "./static"}),
        (r"/favicon.ico", tornado.web.StaticFileHandler, {"path": "./static/"}),
        (r"/favicon", tornado.web.StaticFileHandler, {"path": "./static/"}),
        (r"/", MainHandler),

    ]

    redis = utils.connectRedis(config)
    #redis = None
    # db = gen_pools(config, redis, p)
    db = []
    urls = urls + get_routes(rest, db)
    print([a[0] for a in urls])

    base_dir = os.path.dirname(__file__)
    app = tornado.web.Application(urls,
                                  cookie_secret="sopadeletrinhas123",
                                  **{"login_url": "/login",
                                     "logout_url": "/logout",
                                     "databases": {},
                                     "config": config,
                                     "redis": redis,
                                     "prddb": p,
                                     "debug": False,
                                     "compress_response": True,
                                     'template_path': os.path.join(base_dir, "templates"),
                                     'static_path': os.path.join(base_dir, "static"),
                                     "xsrf_cookies": False,
                                     'pycket': {
                                         'engine': 'redis',
                                         'storage': {
                                             'host': redisurl,
                                             'port': redisport,
                                             'db_sessions': redisdb,
                                             'db_notifications': int(redisdb) + 1,
                                             'max_connections': 2 ** 31,
                                         },
                                         'cookies': {
                                             'expires_days': 1,
                                         },
                                     }
                                     }
                                  )

    loglevel = [logging.INFO, logging.DEBUG]

    slog = utils.setup_logger('restdb', './log/restdb.log', loglevel[debug])
    alog = utils.setup_logger('access_log', './log/access.log', logging.INFO, '%(asctime)s|%(message)s')

    if not debug:
        # server configuration for production
        print("Server Production Starting")

        server = HTTPServer(app)
        server.bind(int(config['tornado']['port']))
        server.start(int(config['tornado']['sockets']))
        IOLoop.current().start()

    else:
        # server configuration for develop
        print("Server Develop Starting")
        app.settings['debug'] = True
        app.listen(int(config['tornado']['port']))
        IOLoop.instance().start()


# noinspection PyAbstractClass,PyAttributeOutsideInit
class BaseHandler(tornado.web.RequestHandler, SessionMixin):
    """
    Base handler for all requests implementing session and databases initialization
    """

    def write_error(self, status_code, **kwargs):
        """
        Error exit default writer return

        :param int status_code: status code of the error
        :param dict kwargs: reason of the error if set
        :return:
        """
        self.write("%s %d error." % (kwargs.get('_reason', 'Generic Error'), status_code))


class MainHandler(BaseHandler):
    """
    dummy return for logged testing
    """

    @tornado.web.authenticated
    def get(self):
        name = escape.xhtml_escape(str(self.current_user))
        self.write("Hello, " + name)


class FavIcon(BaseHandler):
    """
    favicon hack
    """

    def get(self):
        """
        get method
        :return: empty icon
        :rtype: base64 string
        """
        self.write(b64encode(""))

# def gen_pools(config, robj, stype=False):
#
#     dbs = {}
#     ftype = 'production' if stype is True else 'homol'
#     ddb = config['databases'][ftype]
#
#     for db in ddb.items():
#         dbs[db[0]] = RedisPool(
#             dict(host=db[1]['host'], port=3306, user=db[1]['user'], passwd=db[1]['pass'], db=db[1]['db_name'], connect_timeout=5),
#             max_idle_connections=1,
#             max_open_connections=20,
#             max_recycle_sec=3,
#             redisobj=robj)
#     return dbs


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="RESTDB - REST Database abstraction")
    parser.add_argument("-d", "--debug",
                        dest="debug",
                        default=False,
                        action='store_true',
                        help="Run server in debug mode")
    parser.add_argument("-p", "--production-database",
                        dest="p",
                        default=False,
                        action='store_true',
                        help="Usses production databases")
    args = parser.parse_args()

    main(args.debug, args.p)
