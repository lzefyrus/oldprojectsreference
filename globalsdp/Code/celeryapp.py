from __future__ import absolute_import
from application.src.celeryapp import CeleryApp

"""
    Use the following command in order to get Celery started:
    $ celery -A celeryapp:celery_app beat -l info -c 5
"""


# Celery App
celery_app = CeleryApp.get_instance()

# Starts Celery
celery_app.start()
