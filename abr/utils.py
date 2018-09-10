# -*- coding: utf-8 -*-

import models
import re
from uuid import uuid4
from sqlalchemy import or_
import configobj
import logging

class InvalidPhone(Exception):

    """ invalid formated phone Exception
    """
    pass


class PhoneNotFound(Exception):

    """ phone not found Exception
    """
    pass

def import_string(import_name, silent=False):
    """
    Imports an object based on a string.  This is useful if you want to
    use import paths as endpoints or something similar.  An import path can
    be specified either in dotted notation (``xml.sax.saxutils.escape``)
    or with a colon as object delimiter (``xml.sax.saxutils:escape``).
    If `silent` is True the return value will be `None` if the import fails.

    :param str import_name: the dotted name for the object to import.
    :param bool silent: if set to `True` import errors are ignored and `None` is returned instead.
    :return: imported object
    """

    import_name = str(import_name).replace(':', '.')
    try:
        try:
            __import__(import_name)
        except ImportError:
            if '.' not in import_name:
                raise
        else:
            return sys.modules[import_name]

        module_name, obj_name = import_name.rsplit('.', 1)
        try:
            module = __import__(module_name, None, None, [obj_name])
        except ImportError:
            # support importing modules not yet set up by the parent module
            # (or package for that matter)
            module = import_string(module_name)

        try:
            return getattr(module, obj_name)
        except AttributeError as e:
            raise ImportError(e)

    except ImportError as e:
        if not silent:
            raise


def setup_logger(logger_name, log_file, level=logging.INFO, formatter='[ %(levelname)s ] %(asctime)s - {%(pathname)s:%(funcName)s:%(lineno)d} - %(message)s'):
    """
    Multiple file log handler

    :param str logger_name: filename of the log
    :param str log_file: path for the log file
    :param int level: default logging level
    """
    l = logging.getLogger(logger_name)
    formatter = logging.Formatter(formatter, '%d-%m-%Y %H:%M:%S')
    fileHandler = logging.FileHandler(log_file, mode='a')
    fileHandler.setFormatter(formatter)
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)

    l.setLevel(level)
    l.addHandler(fileHandler)
    l.addHandler(streamHandler)

    return l


def translateImage(url_img):
    """
    parse the image name to operator name

    :param str url_img: url of the image
    :return: operator
    :rtype: record
    """

    if (len(url_img) <= 0):
        return None

    url_img_arr = url_img.split('/')
    img_name = url_img_arr[-1].lower()
    name = img_name.split('.')[0]

    try:
        operator = models.TranslateOperator.query.filter_by(name=name).first()

        if not operator:
            op = models.Operator(id=str(uuid4()), img_translate=img_name, name=name)
            oop = models.TranslateOperator(id=str(uuid4()), name=name, rn1=name, operator=op.id)
            models.db.session.add(op)
            models.db.session.add(oop)
            models.db.session.commit()
            return oop
        return operator
    except Exception:
        return 0


def translateArbOperator(lazy, op):
    """
    search for the rn1 operator in database and adds if not found

    :param dict lazy: rn1 and operator database record (data cache)
    :param str op: rn1 operator id
    :return: lazy and operator record
    :rtype: dict, record
    """
    if (len(str(op)) <= 0):
        raise Exception('NO OPERATOR NUMBER')
    if len(str(op)) < 5:
        op = '55%s' % int(op)

    try:
        if op in lazy.keys():
            return lazy, lazy[op].id

        to = models.TranslateOperator.query.filter_by(rn1=op).first()
        if not to:
            operator = models.Operator.query.filter_by(id='other').first()
            oop = models.TranslateOperator(id=str(uuid4()), name=op, rn1=op, operator='other')
            models.db.session.add(oop)
            models.db.session.commit()
            lazy[op] = operator
            return lazy, oop.id
        return lazy, to.id
    except Exception as e:
        return 0


def checkMobile(phone):
    """
    checks if a phone number is mobile or landline

    :param str phone: str phone number
    :return: is mobile or not 
    :rtype: bool
    """
    # todo check if is mobile from cnl table
    clearPhone = parsePhone(phone, True)

    sqlPhone = models.Cnl.query.filter(models.Cnl.initial_phone <= int(clearPhone['prefix']),
                                       models.Cnl.final_phone >= int(clearPhone['prefix']),
                                       models.Cnl.ddd == int(clearPhone['ddd'])).first()

    if not sqlPhone:
        sqlPhone = models.Cnl.query.filter(models.Cnl.initial_phone <= int(clearPhone['msisdn']),
                                           models.Cnl.final_phone >= int(clearPhone['msisdn']),
                                           models.Cnl.ddd == int(clearPhone['ddd'])).first()

    if sqlPhone:
        return True

    return False


def translateOperator(lazy, operator):
    """
    search for the operator in database and adds if not found

    :param dict lazy: operator and operator database record (data cache)
    :param str op: operator id
    :return: lazy and operator record
    :rtype: dict, record
    """
    if (len(operator) <= 0):
        return lazy, None

    op_arr = operator.split(' ')
    op_name = op_arr[0].lower()

    try:
        if op_name in lazy.keys():
            return lazy, lazy[op_name]

        to = models.TranslateOperator.query.filter(models.TranslateOperator.name == op_name).first()

        if not to:

            operator = models.Operator.query.filter_by(id='other').first()
            oop = models.TranslateOperator(id=str(uuid4()), name=op_name, rn1=op_name, operator='other')
            models.db.session.add(oop)
            models.db.session.commit()
            lazy[op_name] = oop
            return lazy, oop
        return lazy, to
    except Exception as e:
        print(e)
        return lazy, None


def parsePhone(phone, returnFull=False):
    """
    parsers and returns the prefix of the phone. If full is required returns dict with all steps and info

    :param str phone: phone number
    :param bool returnFull: does all or not`
    :return: phone info
    :rtype: dit
    """

    clearPhone = re.sub(r'\D', '', phone)
    phonelen = len(str(clearPhone))

    if phonelen > 13:
        raise InvalidPhone

    if clearPhone[0:2] == '55':
        clearPhone = clearPhone[2:]
        phonelen = len(clearPhone)

    if clearPhone[:1] == '0':
        clearPhone = clearPhone[1:]
        phonelen = len(clearPhone)

    if phonelen > 11 or phonelen < 10:
        raise InvalidPhone

    if returnFull:
        ddd = clearPhone[:2]
        msisdn = clearPhone[2:]
        prefix = msisdn[:5]
        if len(msisdn) == 8:
            prefix = msisdn[:4]

        return dict(ddd=ddd,
                    msisdn=msisdn,
                    prefix=prefix,
                    clearPhone=clearPhone)

    return dict(clearPhone)


def insertOperators():
    """
    insert the normatized operators from file
    """
    config = configobj.ConfigObj('config.ini')
    ope = config['operators']
    f = open(ope['file'], 'r', 1, 'UTF-8')
    lazyop = {}
    lazytop = {}
    for line in f.readlines():
        print(line)
        p = line.split(';')
        name = p[2].strip()
        if not p[1] in lazytop.keys():
            top = models.TranslateOperator.query.filter(
                or_(models.TranslateOperator.rn1 == p[1], models.TranslateOperator.name == line[0])).first()
            if not top:
                if not name in lazyop.keys():
                    print('### %s ###' % name)
                    op = models.Operator.query.filter_by(name=name).first()
                    if not op:
                        op = models.Operator(id=str(uuid4()), img_translate='{}.jpg'.format(name), name=name)
                        models.db.session.add(op)
                        models.db.session.commit()
                    lazyop[p[2]] = op
                    print(op)
                top = models.TranslateOperator(id=str(uuid4()),
                                               name=p[0],
                                               operator=op.id,
                                               rn1=p[1])
                print(top)
                models.db.session.add(top)
                models.db.session.commit()

            lazytop[p[1]] = top
