"""
Mock Server. It must be used for development purposes only.
i.e.: Homol and Prod calls partner's API directly.
"""

import tornado.ioloop
from application.src.rewrites import Application
from tornado_json.routes import get_routes
from application.src.models import Config, Tunnel
from application.src import databases
from application.src import utils
import application.settings as settings
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
    for module in settings.REST_MOCK_MODULES:
        routes += get_routes(__import__(module))

    # DB
    db = databases.DB.get_instance()

    # App
    app = Application(routes, db=db, settings={
        'config':  utils.list2dict(db.query(Config).all()),
        'tunnel':  utils.list2dict(db.query(Tunnel).all()),
        'auth': utils.get_auth_map(db),
        'auth_la': utils.get_auth_la_map(db),
        'prebilling': utils.get_prebilling_map(db),
        }
    )

    # Start tornado
    app.listen(port)
    tornado.ioloop.IOLoop.instance().start()
