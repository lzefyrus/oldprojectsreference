# encode: utf-8

from django.core.management.base import BaseCommand
from domain.models import MedicalPrescription


class Command(BaseCommand):
    help = 'Updates prescriptions for Firebase updating'

    def add_arguments(self, parser):
        parser.add_argument('begin', type=int)
        parser.add_argument('end', type=int)

    def handle(self, *args, **options):
        print(options)
        for pk in range(options['begin'], options['end']+1):
            try:
                prescription = MedicalPrescription.objects.get(pk=pk)
                prescription.save()
            except Exception as e:
                print("Error for prescription {0}. Error: {1}".format(pk, e))

        print("Done!")
