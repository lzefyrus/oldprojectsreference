"""
Partner services
"""

from __future__ import absolute_import
from application.src.celeryapp import CeleryApp, Configs
from celery.exceptions import MaxRetriesExceededError
import logging
import requests


# Logging handler
log = logging.getLogger(__name__)

# Celery App
celery = CeleryApp.get_instance()


@celery.task(base=Configs, name="__example__.v1.partner.signature")
def signature(param1, param2):
    try:
        log.info("Sent signature to backend!")
    except:
        try:
            signature.retry()
        except MaxRetriesExceededError:
            signature.apply_async(args=[param1, param2], queue='__example__.v1.partner.signature.error')


@celery.task(base=Configs, name="__example__.v1.partner.mo")
def send_mo(param1, param2):
    try:
        log.info("Sent mo to backend!")
    except:
        try:
            send_mo.retry()
        except MaxRetriesExceededError:
            send_mo.apply_async(args=[param1, param2], queue='__example__.v1.partner.mo.error')
