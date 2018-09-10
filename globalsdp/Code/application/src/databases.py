import application.settings as settings
import application.src.exceptions as exceptions
from application.src import models
import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session
import logging
import pymysql

# Logging handler
log = logging.getLogger(__name__)


class RoutingSession(Session):

    def get_bind(self, mapper=None, clause=None):
        engines = DB.get_engines()

        if self._flushing:
            return engines['writer']
        else:
            return engines['reader']


class DB(object):
    """
    Database connection class.
    For further explanations read this: http://docs.sqlalchemy.org/en/rel_1_1/orm/session_transaction.html
    """
    # Static property
    instance = None
    engines = None

    @classmethod
    def get_instance(cls):
        """
        Returns DB instance (singleton).
        :param connection_name:
        :return: DBSession
        """
        if cls.instance:
            return cls.instance

        engines = cls.get_engines()
        models.DefaultBase.metadata.create_all(engines['reader'])
        models.DefaultBase.metadata.create_all(engines['writer'])
        session = sessionmaker(autocommit=True, class_=RoutingSession)
        ScopedSession = scoped_session(session)
        cls.instance = ScopedSession()

        return cls.instance

    @classmethod
    def get_engines(cls):
        if cls.engines:
            return cls.engines

        cls.engines = {
            'writer': create_engine(cls.get_engine(settings.DATABASES["mysql-writer"]), logging_name='writer'),
            'reader': create_engine(cls.get_engine(settings.DATABASES["mysql-reader"]), logging_name='reader'),
        }

        return cls.engines

    @staticmethod
    def get_engine(connection):
        return "mysql://{0}:{1}@{2}:{3}/{4}?charset={5}"\
            .format(connection['USER'], connection['PASSWORD'],
                    connection['HOST'], connection['PORT'],
                    connection['NAME'], connection['CHARSET'])


class PyMySql(object):
    # Static property
    instance = None

    @classmethod
    def get_instance(cls):
        """
        Returns DB instance (singleton).
        :return: pymysql.connect
        """
        if cls.instance:
            return cls.instance

        connection = settings.DATABASES["mysql-writer"]

        cls.instance = pymysql.connect(
            user=connection['USER'],
            password=connection['PASSWORD'],
            host=connection['HOST'],
            port=connection['PORT'],
            db=connection['NAME'],
            autocommit=True
        )

        return cls.instance


class Redis(object):
    """
    Redis connection class.
    """
    # Static property
    instance = {"redis-tps": None, "redis-celery": None, "redis-prebilling": None, "redis-request-id": None}

    @classmethod
    def get_instance(cls, connection_name):
        """
        Returns Redis instance (singleton).
        :param connection_name:
        :return: redis.Redis
        """
        try:
            cls.instance[connection_name]
        except KeyError:
            raise exceptions.InvalidConnection('Could not find redis connection named "{0}"'.format(connection_name))

        if cls.instance[connection_name]:
            return cls.instance[connection_name]

        connection = settings.DATABASES[connection_name]
        cls.instance[connection_name] = redis.Redis(
            host=connection['HOST'],
            port=connection['PORT'],
            password=connection['PASSWORD'],
            db=connection['DB'],
        )

        return cls.instance[connection_name]
