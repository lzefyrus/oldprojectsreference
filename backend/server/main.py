# -*- coding: utf-8 -*-

import argparse
import logging
from pprint import pprint

import configobj
import tornado.httpserver
import tornado.ioloop
from dynamo3 import DynamoDBConnection
from flywheel import Engine
from redis import Redis, ConnectionPool
from referral import ReferralHandler
from ses_mailer import Mail
from tornado.web import StaticFileHandler
from tornado_json.application import Application
from tornado_json.routes import get_routes
from tornadouvloop import TornadoUvloop

import admin
import box
import game
import prizes
import referral
import tips
import user
from face_auth import FacebookGraphLoginHandler
from utils import SessionBaseHandler

pool = ConnectionPool(max_connections=2,
                      host='session.sqippd.0001.use1.cache.amazonaws.com',
                      port=6379,
                      db=0)

redis = Redis(connection_pool=pool)


class HomeHandler(SessionBaseHandler):
    def get(self):
        self.finish({'success': True,
                     'user_id': self.session.get('id'),
                     'name': self.session.get('name'),
                     'token': self.session.getCookieOrToken()})


def main(pargs):
    global redis
    if pargs.production:
        serverConf = configobj.ConfigObj('production.ini')
    else:
        serverConf = configobj.ConfigObj('develop.ini')

    routes = [
        (r"/auth/login", FacebookGraphLoginHandler),
        (r"/", HomeHandler),
        (r"/referral/([^/]+)", ReferralHandler),
        (r"/r/([^/]+)", ReferralHandler),
        (r'/(favicon.ico)', StaticFileHandler, {"path": "./static/"}),
    ]

    for api in [game, tips, user, referral, prizes]:
        routes.extend(get_routes(api))

    if pargs.admin:
        routes.extend(get_routes(admin))
        routes.extend(get_routes(box))
        from encontact import UserDataHandler
        routes.extend([(r"/admin/encontact?/", UserDataHandler), ])

    pprint(routes, indent=4)

    mailer = Mail(aws_access_key_id=serverConf['ses']['acceskeyid'],
                  aws_secret_access_key=serverConf['ses']['secretacceskeyid'],
                  region=serverConf['ses']['region'],
                  sender=serverConf['ses']['sender'],
                  template=serverConf['ses']['templates'])

    if pargs.production:
        dyn = DynamoDBConnection.connect(region=serverConf['dynamo']['region'],
                                         access_key=serverConf['dynamo']['acceskeyid'],
                                         secret_key=serverConf['dynamo']['secretacceskeyid'])
        session_settings = dict(
            driver="redis",
            force_persistence=True,
            cache_driver=True,
            driver_settings=dict(
                host=serverConf['redis']['host'],
                port=int(serverConf['redis']['port']),
                db=int(serverConf['redis']['db']),
                max_connections=1024,
            ),
        )
        pool = ConnectionPool(max_connections=2,
                              host=serverConf['redis']['host'],
                              port=int(serverConf['redis']['port']),
                              db=int(serverConf['redis']['db']) + 1)

        pool2 = ConnectionPool(max_connections=2,
                               host=serverConf['redis']['host'],
                               port=int(serverConf['redis']['port']),
                               db=int(serverConf['redis']['db']))

    else:
        dyn = DynamoDBConnection.connect(region='sp-east', host='127.0.0.1', port=8000, is_secure=False,
                                         access_key='asdas', secret_key='123ads')
        session_settings = dict(
            driver="redis",
            force_persistence=True,
            cache_driver=True,
            driver_settings=dict(
                host='localhost',
                port=6379,
                db=0,
                max_connections=1024,
            ),
        )
        pool = ConnectionPool(max_connections=2,
                              host='localhost',
                              port=6379,
                              db=1)

        pool2 = ConnectionPool(max_connections=2,
                               host='localhost',
                               port=6379,
                               db=0)

    redis = Redis(connection_pool=pool)
    redis2 = Redis(connection_pool=pool2)
    engine = Engine(dynamo=dyn)
    log = logging.getLogger(__name__)
    a = logging.basicConfig(level=logging.INFO,
                            format='[ %(asctime)s ][ %(levelname)s ][ %(filename)20s:%(lineno)4s - %(funcName)20s() ] %(message)s',
                            datefmt='%m-%d %H:%M',
                            filename='log/nextgame.log',
                            filemode='a')

    log.addHandler(a)
    settings = {
        "debug": False,
        'xsrf_cookies': False,
        'serverConfig': serverConf,
        'instance': serverConf.get('instance'),
        'engine': engine,
        'facebook_api_key': serverConf['facebook']['key'],
        'facebook_secret': serverConf['facebook']['secret'],
        'session': session_settings,
        'template_path': serverConf['ses']['templates'],
        "login_url": "/auth/login/",
        "cookie_secret": 'sopadeletrinhas123',
        "mailer": mailer,
        "production": False
    }

    if (pargs.debug):
        # log.setLevel(logging.DEBUG)
        log.debug('DEBUGGING LOG')
        settings['debug'] = True

    app = Application(routes=routes,
                      settings=settings,
                      db_conn={'ping': redis, 'session': redis2})

    if pargs.provision:
        game.models.create_schemas(engine)
        tips.models.create_schemas(engine)
        referral.models.create_schemas(engine)

    if (pargs.production):
        print('Server Production Starting')
        server = tornado.httpserver.HTTPServer(app)
        server.bind(serverConf['tornado']['port'])
        server.start(int(serverConf['tornado']['instances']))
        tornado.ioloop.IOLoop.configure(TornadoUvloop)


    else:
        print('Server Develop Starting')
        app.listen(serverConf['tornado']['port'])
        tornado.ioloop.IOLoop.configure(TornadoUvloop)

    tornado.ioloop.IOLoop.current().start()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--admin', default=False, action='store_true')
    parser.add_argument('-p', '--production', default=False, action='store_true')
    parser.add_argument('-d', '--debug', default=False, action='store_true')
    parser.add_argument('-c', '--provision', default=False, action='store_true')

    args = parser.parse_args()
    main(args)
