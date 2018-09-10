# encoding: utf-8

from django.apps import AppConfig


class DomainConfig(AppConfig):
    name = 'domain'

    def ready(self):
        import domain.signals.send_notification # noga
        import domain.signals.update_firebase_db # noga
        import domain.signals.update_prescription # noga
        import domain.signals.update_prescription_piece # noga
        import domain.signals.update_scheduled_exam # noga
