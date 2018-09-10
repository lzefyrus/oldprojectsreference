from tornado.httpserver import HTTPServer
from application import settings as app_settings
from application.src.rewrites import get_soap_routes, WebService
from application.src.models import Config, Tunnel
from application.src import databases
from application.src import utils
import tornado.httpserver
import tornado.ioloop
import logging
import logging.config
import sys


# Args
port = sys.argv[1]

if __name__ == '__main__':
    # Logs
    logging.config.dictConfig(app_settings.LOGGING)

    # Routes
    routes = []
    for module in app_settings.SOAP_MODULES:
        soap_routes = get_soap_routes(__import__(module))
        for route in soap_routes:
            path = route[0].lstrip('/')
            handler = route[1]
            routes += [(path, handler)]

    # DB
    db = databases.DB().get_instance()

    # App
    ws = WebService(routes, db=db, settings={
        'config':  utils.list2dict(db.query(Config).all()),
        'tunnel':  utils.list2dict(db.query(Tunnel).all()),
        'auth': utils.get_auth_map(db),
        'auth_la': utils.get_auth_la_map(db),
        'prebilling': utils.get_prebilling_map(db),
        }
    )
    application = tornado.httpserver.HTTPServer(ws)

    # Start tornado with multiple processes
    server = HTTPServer(application)
    server.bind(int(port))
    server.start(int(app_settings.TORNADO_SOCKETS))

    tornado.ioloop.IOLoop.instance().start()
