from __future__ import absolute_import, unicode_literals

import os

from celery import Celery
from celery.schedules import crontab


# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lab_core.settings')

app = Celery('lab_core')

# Using a string here means the worker don't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    from domain.tasks import populate_firebase_week_schedulings_endpoint, populate_firebase_results_ac_endpoint, \
        populate_firebase_results_rdi_endpoint, expire_prescription_pieces, send_users_report, send_users_orders_report, \
        send_kpis_per_day_report, send_general_kpi

    sender.add_periodic_task(crontab(hour=3, minute=0), expire_prescription_pieces.s())
    sender.add_periodic_task(crontab(hour=3, minute=5), populate_firebase_week_schedulings_endpoint.s())
    sender.add_periodic_task(crontab(hour=3, minute=10), populate_firebase_results_ac_endpoint.s())
    sender.add_periodic_task(crontab(hour=3, minute=15), populate_firebase_results_rdi_endpoint.s())
    sender.add_periodic_task(crontab(hour=4, minute=0), send_users_report.s())
    sender.add_periodic_task(crontab(hour=4, minute=0), send_users_orders_report.s())
    sender.add_periodic_task(crontab(hour=4, minute=0), send_kpis_per_day_report.s())
    sender.add_periodic_task(crontab(hour=4, minute=0), send_general_kpi.s())



@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))

