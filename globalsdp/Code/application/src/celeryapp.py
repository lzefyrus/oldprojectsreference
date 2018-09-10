from celery import Celery, Task
from application import settings
from application.src import databases
import logging
import logging.config


class CeleryApp:
    # Static property
    instance = None

    @staticmethod
    def _get_tasks():
        """
        Finds all celery tasks inside integration modules.
        :return: list
        """
        partner_tasks = ["{0}.partner".format(module) for module in settings.CELERY_TASKS]
        backend_tasks = ["{0}.backend".format(module) for module in settings.CELERY_TASKS]
        schedule_tasks = [module[0].rsplit('.', 1)[0] for module in settings.CELERY_SCHEDULE_TASKS]
        return partner_tasks + backend_tasks + schedule_tasks + \
               ["application.src.request", "integrations.tim.v1.utils.etl", "application.src.services"]

    @staticmethod
    def _get_schedule_tasks():
        """
        Finds all celery schedule tasks.
        :return: dict
        """
        return {task[0]: {'task': task[0], 'schedule': task[1]} for task in settings.CELERY_SCHEDULE_TASKS}

    @classmethod
    def get_instance(cls):
        """
        Returns Celery instance (singleton).
        :return: Celery
        """
        if cls.instance:
            return cls.instance

        # Celery App
        cls.instance = Celery(
            'globalsdp',
            broker=settings.CELERY_BROKER,
            include=cls._get_tasks()
        )

        # Routes
        cls.instance.conf.CELERY_ACCEPT_CONTENT = settings.CELERY_ACCEPT_CONTENT
        cls.instance.conf.CELERY_ROUTES = settings.CELERY_ROUTES

        # Celery Beat - Periodic Tasks
        cls.instance.conf.CELERYBEAT_SCHEDULE = cls._get_schedule_tasks()
        cls.instance.conf.CELERY_TIMEZONE = settings.CELERY_TIMEZONE

        return cls.instance


class Configs(Task):
    abstract = True
    _pymysql = None
    _logger = None
    _redis = {"redis-tps": None, "redis-celery": None, "redis-prebilling": None}

    default_retry_delay = settings.CELERY_RETRY['default_retry_delay']
    max_retries = settings.CELERY_RETRY['max_retries']

    @property
    def pymysql(self):
        if self._pymysql is None:
            self._pymysql = databases.PyMySql.get_instance()
        return self._pymysql

    @property
    def log(self):
        if not self._logger:
            try:
                logging.config.dictConfig(settings.LOGGING)
                self._logger = logging.getLogger("celery")
            except:
                pass
        return self._logger

    def redis(self, connection_name):
        if self._redis[connection_name] is None:
            self._redis[connection_name] = databases.Redis.get_instance(connection_name)
        return self._redis[connection_name]

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        self.log.info("Returning Task descriptions. "
                      "Id: {0}. "
                      "Status: {1}. "
                      "Return: {2}. "
                      "Args: {3}. "
                      "Kwargs: {4}. "
                      "Info: {5}. ".format(task_id, status, retval, args, kwargs, einfo)
                      )
