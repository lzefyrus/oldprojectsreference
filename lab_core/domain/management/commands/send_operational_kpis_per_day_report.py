# encode: utf-8

from django.core.management.base import BaseCommand
from domain.tasks import send_operational_kpis_report

class Command(BaseCommand):
    help = 'Sends OPERATIONAL KPIs (since 15th July 2017) report by email'

    def handle(self, *args, **options):
        send_operational_kpis_report()
