from functools import wraps
import logging
from application.src.celeryapp import CeleryApp, Configs
from application.src import utils
from datetime import datetime
from celery.exceptions import MaxRetriesExceededError
import application.settings as settings

# Logging handler
log = logging.getLogger(__name__)

# Celery App
celery = CeleryApp.get_instance()


def request(func):
    """
    Save Incoming Requests to Database.
    """
    @wraps(func)
    def with_requests(self, *args):
        try:
            url = str(self.request.uri)
            header = str(utils.get_headers(self.request.headers))
            body = str(self.request.body.decode("utf-8"))
            date = datetime.now()
            # request_async.delay(url, header, body, date)
            request_async.apply_async(
                args=[url, header, body, date],
                queue=settings.CELERY_ROUTES['application.request']['queue'],
                serializer=settings.CELERY_SERIALIZATION
            )
            #TODO log de sucesso
        except Exception as e:
            log.error(e)

        return func(self, *args)
    return with_requests


@celery.task(base=Configs, name="application.request")
def request_async(url, header, body, date):
    """
    Saves request asynchronously.
    This feature uses pymysql due to performance.
    :param url:
    :param header:
    :param body:
    :param date:
    :return:
    """
    try:
        with request_async.pymysql.cursor() as cursor:
            insert = "INSERT INTO request (url, header, body, created_at, etl) VALUES (%s, %s, %s, %s,%s)"
            values = (url, header, body, date, 1)
            cursor.execute(insert, values)
    except Exception as e:
        log.error('Error on saving incoming request: {0}'.format(e))
        try:
            request_async.retry()
        except MaxRetriesExceededError:
            request_async.apply_async(args=[url, header, body, date], queue='application.request.error')
