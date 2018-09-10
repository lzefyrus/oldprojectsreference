# encode: utf-8

from django.core.management.base import BaseCommand
from domain.tasks import send_kpis_per_day_report


class Command(BaseCommand):
    help = 'Sends KPIs (since 15th July 2017) report by email'

    def handle(self, *args, **options):
        send_kpis_per_day_report()
