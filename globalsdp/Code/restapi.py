from tornado.httpserver import HTTPServer
from tornado_json.routes import get_routes
from application.src.rewrites import Application
from application.src.models import Config, Tunnel
from application.src import databases
from application.src import utils
import application.settings as settings
import tornado.ioloop
import logging
import logging.config
import sys


# Args
port = sys.argv[1]

# Initializing
if __name__ == "__main__":
    # Logs
    logging.config.dictConfig(settings.LOGGING)

    # Routes
    routes = []
    for module in settings.REST_MODULES:
        routes += get_routes(__import__(module))

    # DB
    db = databases.DB().get_instance()

    # App
    app = Application(routes, db=db, settings={
        'config':  utils.list2dict(db.query(Config).all()),
        'tunnel':  utils.get_tunnel_map(db),
        'auth': utils.get_auth_map(db),
        'auth_la': utils.get_auth_la_map(db),
        'prebilling': utils.get_prebilling_map(db),
        }
    )

    # Start tornado with multiple processes
    server = HTTPServer(app)
    server.bind(int(port))
    server.start(int(settings.TORNADO_SOCKETS))

    tornado.ioloop.IOLoop.instance().start()
