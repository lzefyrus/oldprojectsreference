# -*- coding: utf-8 -*-
from flask import Flask, jsonify, request, Response
from functools import wraps
import configobj
from flask.ext.sqlalchemy import SQLAlchemy
import utils
import models
import logging

app = Flask(__name__, static_folder='./Docs/src/_build/html/', static_url_path='')
logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
rootLogger = logging.getLogger()
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)


def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    try:
        if app.config['CONFIG']['bauth'][username]['pass'] == password:
            return True
    except Exception as e:
        rootLogger.info(e)

    return False


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'internal-lbi-abr-prod' not in request.host:
            auth = request.authorization
            if not auth or not check_auth(auth.username, auth.password):
                return authenticate()
        return f(*args, **kwargs)

    return decorated


def parseReturn(sqlPhone, clearPhone, seventeen=False):
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

    if 'province' in sqlPhone.__dict__.keys():
        base['portado'] = False
        base['uf'] = sqlPhone.uf
        base['provincia'] = sqlPhone.province
        top = models.TranslateOperator.query.filter_by(id=sqlPhone.operator_id).first()
        logging.debug(sqlPhone.operator_id)
        if top:
            logging.debug(top.operator)
            op = models.Operator.query.filter_by(id=top.operator).first()
            if op:
                base['operadora'] = op.name
        if sqlPhone.is_mobile is True:
            uf = models.Ddd.query.filter_by(id=int(clearPhone['ddd'])).first()
            if uf:
                base['uf'] = uf.state.upper()
    else:
        base['dataPortabilidade'] = sqlPhone.activation_time
        base['dataInicio'] = sqlPhone.start_time
        top = models.TranslateOperator.query.filter_by(id=sqlPhone.operator).first()
        logging.debug(sqlPhone.operator)
        if top:
            logging.debug(top.operator)
            op = models.Operator.query.filter_by(id=top.operator).first()
        uf = models.Ddd.query.filter_by(id=int(clearPhone['ddd'])).first()
        if op:
            logging.debug(op.name)
            base['operadora'] = op.name
        if uf:
            base['uf'] = uf.state.upper()

    if seventeen:
        base['9digit'] = True

    return base


@app.route('/doc')
def doc():
    if 'internal-lbi-abr-prod' in request.host:
        return app.send_static_file('index.html')
    return jsonify({'error': 'Unno'})


@app.route('/search/<string:phone>', methods=['GET'])
# @requires_auth
def get_tasks(phone):
    """
    endpont to search phones

    :param str phone: phone number
    :return: text/json data with phone information
    :rtype: str
    """
    try:
        clearPhone = utils.parsePhone(phone, True)
        rootLogger.debug(request.headers)
        sqlPhone = find_phone(clearPhone)

        nine = check_nine(clearPhone['msisdn'])

        if not sqlPhone and nine is not False:
            clearPhone = utils.parsePhone('%s%s' % (clearPhone['ddd'], nine), True)
            sqlPhone = find_phone(clearPhone)

        rootLogger.debug(clearPhone)

        if not sqlPhone:
            raise utils.PhoneNotFound

        return jsonify(parseReturn(sqlPhone, clearPhone, True))

    except utils.PhoneNotFound:
        return jsonify({'error': 'phone not found'})
    except utils.InvalidPhone:
        return jsonify({'error': 'invalid phone'})
    except Exception as e:
        return jsonify({'error': 'System Error %s ' % e})


@app.route('/operators', methods=['GET'])
def get_operators():
    """
    list all operators available in database

    :return: text/json of all operators
    :rtype: str

    """
    try:
        sqlOperators = models.TranslateOperator.query.all()
        return jsonify(sqlOperators)

    except Exception as e:
        return jsonify({'error': 'System Error %s ' % e})


@app.route('/searchp/<string:phone>', methods=['GET'])
# @requires_auth
def get_tasksp(phone):
    """
    endpont to search phones

    :param str phone: phone number
    :return: text/json data with phone information
    :rtype: str
    """
    try:
        clearPhone = utils.parsePhone(phone, True)

        sqlPhone = models.Phone.query.filter_by(id=clearPhone['clearPhone']).first()

        nine = check_nine(clearPhone['msisdn'])

        if not sqlPhone and nine is not False:
            clearPhone = utils.parsePhone('%s%s' % (clearPhone['ddd'], nine), True)
            sqlPhone = models.Phone.query.filter_by(id=clearPhone['clearPhone']).first()

        rootLogger.debug(clearPhone)

        if not sqlPhone:
            raise utils.PhoneNotFound

        return jsonify(parseReturn(sqlPhone, clearPhone, True))

    except utils.PhoneNotFound:
        return jsonify({'error': 'phone not found'})
    except utils.InvalidPhone:
        return jsonify({'error': 'invalid phone'})
    except Exception as e:
        return jsonify({'error': 'System Error %s ' % e})


def find_phone(clearPhone):
    """
    do se search of the parsed phone number in the database initially on PHONE table to ckeck for portabitily
    and then on CNL table
    """
    # TODO enrich the information if direct phone found with CNL info
    sqlPhone = models.Phone.query.filter_by(id=clearPhone['clearPhone']).first()

    if not sqlPhone:

        sqlPhone = models.CnlTmp.query.filter(models.CnlTmp.initial_phone <= int(clearPhone['prefix']),
                                              models.CnlTmp.final_phone >= int(clearPhone['prefix']),
                                              models.CnlTmp.ddd == int(clearPhone['ddd'])).first()

        if not sqlPhone:
            sqlPhone = models.CnlTmp.query.filter(models.CnlTmp.initial_phone <= int(clearPhone['msisdn']),
                                                  models.CnlTmp.final_phone >= int(clearPhone['msisdn']),
                                                  models.CnlTmp.ddd == int(clearPhone['ddd'])).first()

    return sqlPhone


def check_nine(phone):
    """
    Check for 8 or 9 digits phone

    :param str phone: phone
    """
    if len(str(phone)) == 8:
        return '9' + str(phone)
    if len(str(phone)) == 9:
        return str(phone)[1:]
    return False

app.debug = True

if __name__ == '__main__':
    fileHandler = logging.FileHandler("{0}/{1}.log".format('./log', 'debuglog'))
    fileHandler.setFormatter(logFormatter)
    rootLogger.addHandler(fileHandler)

    config = configobj.ConfigObj('config.ini')
    users = configobj.ConfigObj('users.ini')
    crateconf = config['crate']

    app.config['SQLALCHEMY_DATABASE_URI'] = '%s%s%s' % (crateconf['protocol'], crateconf['host'], crateconf['port'])
    app.config['CONFIG'] = users

    db = SQLAlchemy(app)
    app.run()
    app.debug(True)
