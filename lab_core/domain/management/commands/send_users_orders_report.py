# encode: utf-8

from django.core.management.base import BaseCommand
from domain.tasks import send_users_orders_report


class Command(BaseCommand):
    help = 'Sends users orders for prescription/exams (since 15th July 2017) report by email'

    def handle(self, *args, **options):
        send_users_orders_report()
