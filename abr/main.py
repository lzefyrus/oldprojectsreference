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

from tornado import escape, web
import configobj

from crate.client import sqlalchemy
import utils
# Sqlalchemy imports
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# App imports
import models
from models import Phone, Operator, TranslateOperator, Ddd, Cnl


# import oauth2 as provider

alog = None
slog = None
redisdb = None
dtime = '%d/%m/%Y %H:%M:%S'


def main(debug=False, tj=False):
    """
    main loop for tornado server
    sets all needed information for running

    :param bool debug: run server in debug or production     modes
    """
    config = configobj.ConfigObj('config.ini')
    global slog, alog, redisdb

    engine = create_engine('{}{}:{}'.format(config['crate']['protocol'],
                                               config['crate']['host'],
                                               config['crate']['port']))
    # models.init_db(engine)
    connection = scoped_session(sessionmaker(bind=engine))
    models.init_db(engine)
    urls = [
        (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": "./static"}),
        (r"/favicon.ico", tornado.web.StaticFileHandler, {"path": "./static/"}),
        (r"/favicon", tornado.web.StaticFileHandler, {"path": "./static/"}),
        (r"/", MainHandler),
        (r"/search/([^/]+)", SearchHandler)
    ]

    base_dir = os.path.dirname(__file__)
    app = tornado.web.Application(urls,
                                  cookie_secret="sopadeletrinhas123",
                                  **{"login_url": "/login",
                                     "logout_url": "/logout",
                                     "debug": False,
                                     "compress_response": True,
                                     'template_path': os.path.join(base_dir, "templates"),
                                     'static_path': os.path.join(base_dir, "static"),
                                     "xsrf_cookies": False,
                                     }
                                  )
    app.db = connection

    loglevel = [logging.INFO, logging.DEBUG]

    slog = utils.setup_logger('tornado_oauthlib', './log/oauthdebug.log', loglevel[debug])
    alog = utils.setup_logger('access_log', './log/access.log', logging.INFO, '%(asctime)s|%(message)s')

    if not debug:
        # server configuration for production
        print("Server Production Starting")

        server = HTTPServer(app)
        server.bind(int(config['tornado']['port']))
        server.start(int(config['tornado']['sockets']))
        main_loop = tornado.ioloop.IOLoop.instance()
        main_loop.start()

    else:
        # server configuration for develop
        print("Server Develop Starting")
        app.settings['debug'] = True
        app.listen(int(config['tornado']['port']))
        main_loop = tornado.ioloop.IOLoop.instance()
        IOLoop.instance().start()

# noinspection PyAbstractClass,PyAttributeOutsideInit
class BaseHandler(tornado.web.RequestHandler):

    """
    Base handler for all requests implementing session and databases initialization
    """
    @property
    def db(self):
        return self.application.db

    # def initialize(self, db):
    #     """
    #     class initialization and database setup
    #     """
    #     self.db = db

# noinspection PyAbstractClass
class SearchHandler(BaseHandler):

    """
    Token Authorization functions
    """

    # noinspection PyUnusedLocal,PyUnusedLocal
    def get(self, phone):
        """
        get phone data
        """

        try:
            clearPhone = utils.parsePhone(phone, True)

            sqlPhone = self.find_phone(clearPhone)

            nine = check_nine(clearPhone['msisdn'])

            if not sqlPhone and nine is not False:
                clearPhone = utils.parsePhone('%s%s' % (clearPhone['ddd'], nine), True)
                sqlPhone = self.find_phone(clearPhone)

            slog.debug(clearPhone)

            if not sqlPhone:
                raise utils.PhoneNotFound

            return self.write(self.parseReturn(sqlPhone, clearPhone, True))
            # return self.write(sqlPhone)

        except utils.PhoneNotFound:
            self.set_status(404)
            return self.write({'error':'phone not found'})
        except utils.InvalidPhone:
            self.set_status(401)
            return self.write({'error':'Invalid Phone'})
        except Exception as e:
            return self.send_error(status_code=500, reason=e)


    def find_phone(self, clearPhone):
        """
        do se search of the parsed phone number in the database initially on PHONE table to ckeck for portabitily
        and then on CNL table
        """
        # TODO enrich the information if direct phone found with CNL info
        sqlPhone = self.db.query(Phone).filter_by(id=clearPhone['clearPhone']).first()
        if not sqlPhone:
            sqlPhone = self.db.query(Cnl).filter(models.Cnl.initial_phone <= int(clearPhone['prefix']),
                                               models.Cnl.final_phone >= int(clearPhone['prefix']),
                                               models.Cnl.ddd == int(clearPhone['ddd'])).first()

            if not sqlPhone:
                sqlPhone = self.db.query(Cnl).filter(models.Cnl.initial_phone <= int(clearPhone['msisdn']),
                                                   models.Cnl.final_phone >= int(clearPhone['msisdn']),
                                                   models.Cnl.ddd == int(clearPhone['ddd'])).first()
        slog.debug(sqlPhone)
        return sqlPhone

    def parseReturn(self, sqlPhone, clearPhone, seventeen=False):
        """
        format input data for json response

        :param sqlachemy sqlPhone: retsultset
        :param dict clearPhone: parsed phone
        :param bool seventeen: 9 digit check
        :return: json response
        :rtype: dict
        """

        base = dict(operadora=sqlPhone.operator,
                    telefone=clearPhone['clearPhone'],
                    dataInicio='',
                    dataPortabilidade='',
                    portado=True,
                    mobile=sqlPhone.is_mobile,
                    provincia='')

        top = self.db.query(TranslateOperator).filter_by(id=sqlPhone.operator).first()
        if top:
            logging.debug(top.operator)
            op = self.db.query(Operator).filter_by(id=top.operator).first()

        uf = self.db.query(Ddd).filter_by(id=int(clearPhone['ddd'])).first()

        if 'province' in sqlPhone.__dict__.keys():
            base['portado'] = False
            base['uf'] = sqlPhone.uf
            base['provincia'] = sqlPhone.province

            logging.debug(sqlPhone.operator)
            if top:
                if op:
                    base['operadora'] = op[0]
            if sqlPhone.is_mobile is True:
                if uf:
                    base['uf'] = uf.state.upper()
        else:
            base['dataPortabilidade'] = sqlPhone.activation_time.strftime(dtime)
            base['dataInicio'] = sqlPhone.start_time.strftime(dtime)
            logging.debug(sqlPhone.operator)
            if op:
                logging.debug(op.name)
                base['operadora'] = op.name
            if uf:
                base['uf'] = uf.state.upper()

        if seventeen:
            base['9digit'] = True

        return base


def check_nine(phone):
    """
    Check for 8 or 9 digits phone

    :param str phone: phone
    """
    if len(str(phone)) == 8:
        return '9' + str(phone)
    return False

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
        self.finish(b64encode(""))






if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="SSO - Single Sign ON")
    parser.add_argument("-d", "--debug",
                        dest="debug",
                        default=False,
                        action='store_true',
                        help="Run server in debug mode")
    parser.add_argument("-tj", "--tornado-json",
                        dest="tj",
                        default=False,
                        action='store_true',
                        help="Run oauth using tornado-json")
    args = parser.parse_args()

    main(args.debug, args.tj)
