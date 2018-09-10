#!/usr/bin/env python
# coding=utf-8

import base64
import hashlib
import logging
from datetime import datetime

from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto import Random
import redis


class DoesNotExist(BaseException):
    """
        Exception convention for register not found
    """
    pass


class RedisNoConnException(Exception):
    pass


class Canceled(BaseException):
    """
        Exception convention for register not found
    """
    pass


slog = logging.getLogger('tornado_oauthlib')
alog = logging.getLogger('access')


class crypt():
    """
        Class used for encryption and decryption of passwords used by login process.
        salts and passwords are stored in config ini and are unique for each mobile operator
    """

    def __init__(self, salt, password):
        """
        Class Initialization

            :param str salt: hash salt
            :param str password: hash password
        """
        self.salt = salt
        self.password = password
        self.blocksize = 16
        full = salt + password
        self.hashstr = SHA256.new(full)
        self.pad = lambda s: s + (self.blocksize - len(s) % self.blocksize) * '\0'

    def encrypt(self, enckey):
        """
        encrypt given data allways retruning a new string

            :param bytes enckey: given string to encryption
            :return: encoded parameter
            :rtype: str
        """
        iv = Random.new().read(self.blocksize)
        cipher = AES.new(self.hashstr.digest(), AES.MODE_CBC, iv)
        enc = cipher.encrypt(self.pad(enckey + hashlib.md5(enckey.encode()).hexdigest()))
        full = base64.encodebytes(iv)[:22] + base64.encodebytes(enc)[:-1]
        return full.decode()

    def decrypt(self, deckey):
        """
        decrypts the variable to plain password

            :param bytes deckey: variable to be decrypted
            :return: plain password
            :rtype: str
        """
        t = '%s%s' % (deckey[:22], '==')
        iv = base64.decodebytes(t.encode())
        enc = deckey[22:] + '==\n'
        enc = base64.decodebytes(enc.encode())
        cipher = AES.new(self.hashstr.digest(), AES.MODE_CBC, iv)
        dec = cipher.decrypt(enc).rstrip(b'\0')
        passw = dec[:-32]
        md = dec[-32:]
        if hashlib.md5(passw).hexdigest() != md.decode():
            raise ValueError
        return passw

    def check(self, key1, key2):
        """
        Verifies if encrypted key1 maches the unencrypted key2

            :param bytes key1: encrypted key to be checked against
            :param str key2: unencrypted key
            :return: True if keys match else False
            :rtype: bool
        """
        try:
            return self.decrypt(key1) == key2.encode()
        except ValueError or AttributeError:
            return False


def setup_logger(logger_name, log_file, level=logging.INFO,
                 formatter='[ %(levelname)s ] %(asctime)s - {%(pathname)s:%(funcName)s:%(lineno)d} - %(message)s'):
    """
    Multiple file log handler

    :param str logger_name: filename of the log
    :param str log_file: path for the log file
    :param int level: default logging level
    """
    l = logging.getLogger(logger_name)
    formatter = logging.Formatter(formatter, '%d-%M-%Y %H:%M:%S')
    fileHandler = logging.FileHandler(log_file, mode='a')
    fileHandler.setFormatter(formatter)
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)

    l.setLevel(level)
    l.addHandler(fileHandler)
    l.addHandler(streamHandler)

    return l


def json_formats(data):
    d = {}

    if data is None:
        return data

    if type(data) is tuple:
        d = []
        for w in data:
            d.append(set_jdata(w))
    else:
        for k, w in data.items():
            d[k] = w
            if type(w) is datetime:
                d[k] = w.isoformat()
            elif w is None:
                d[k] = ''
    return d


def set_jdata(w):
    if type(w) is datetime:
        return w.isoformat()
    elif w is None:
        return ''
    return w


def get_db(context, db):
    if db in [None, '', {}, [], False]:
        gen_pool()

def msisdn89(msisdn):
    lenm = len(str(msisdn))
    if lenm == 11:
        return "{}{}".format(msisdn[:2],
                             msisdn[3:])
    if lenm == 9:
        return msisdn[1:]

    if lenm == 10:
        return "{}9{}".format(msisdn[:2],
                             msisdn[2:])
    if lenm == 8:
        return '9' + msisdn


def connectRedis(config):
    """
    We cannot assume that connection will succeed, as such we use a ping()
    method in the redis client library to validate ability to contact redis.
    RedisNoConnException is raised if we fail to ping.
    :return: redis.StrictRedis Connection Object
    """
    try:
        redis.StrictRedis(host=config['redis'].get('host', None),
                          port=config['redis'].get('port', None),
                          password=config['redis'].get('password', None)).ping()
    except redis.ConnectionError as e:
        raise RedisNoConnException("Failed to create connection to redis",
                                   (config['redis'].get('host', None),
                                    config['redis'].get('port', None)))

    return redis.StrictRedis(host=config['redis'].get('host', None),
                             port=config['redis'].get('port', None),
                             password=config['redis'].get('password', None),
                             db=config['redis'].get('db', 1))


if __name__ == "__main__":
    cc = crypt(b'!kQm*fF3pXe1Kbm%9', b'FSVAS::McL@d::2014')
    cd = crypt(b'FSVAS::McL@d::2014', b'!kQm*fF3pXe1Kbm%9')
    passw = 'fsvastest'
    dec = '7sNiQj0kkNXiReeaFclTnwHR9TjbQn/HP4L0X/kcWB7A8+KPORi/Rs7xpUIVTJO8IdKn0c6WqbatbeLKYw2EKK'
    enc = cc.encrypt(passw)
    print(enc)
    print(cc.decrypt(enc))
    print(cc.decrypt(dec))
    print(cc.check(dec, passw))
