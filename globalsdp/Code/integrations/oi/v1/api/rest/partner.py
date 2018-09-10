from application.src.rewrites import APIHandler
from integrations.oi.v1.services import partner as PartnerService
from integrations.oi.v1.validators.partner import validate_mo
from application.src.request import request
from datetime import datetime
import application.settings as settings
import uuid
import logging
import requests


partner_name = 'oi'
api_version = 'v1'

# Logging handler
log = logging.getLogger(__name__)
LOG_HASH = settings.LOG_HASHES[partner_name]


class MoHandler(APIHandler):
    __urls__ = [r"/{0}/{1}/mo".format(partner_name, api_version),
                r"/{0}/{1}/mo/".format(partner_name, api_version)]

    # MO Hash Code for log identification
    MO_HASH = LOG_HASH["mo"]

    @request
    @validate_mo
    def get(self):
        # Getting arguments
        from_ = self.get_argument('from', None, strip=True)
        to = self.get_argument('to', None, strip=True)
        text = self.get_argument('text', None, strip=True)
        mo_id = str(uuid.uuid4().hex)
        mo_date = str(datetime.now())
        try:
            # Getting configs
            configs = PartnerService.get_configs(self.settings)

            # Send async request to Sorte7
            PartnerService.send_mo.apply_async(
                args=[configs, from_, to, text, mo_id, mo_date],
                queue=settings.CELERY_ROUTES['oi.v1.partner.send_mo_async']['queue'],
                serializer=settings.CELERY_SERIALIZATION
            )
            log.info("MO Request successfully received: "
                     "From: {0}. "
                     "To: {1}. "
                     "Text: {2}. "
                     "MO Id: {3}. "
                     .format(from_, to, text, mo_id).replace('\n',' '))

            return self.success({"status": "OK", "message": "MO '{0}' successfully received: {1} to {2}."
                                .format(text, from_, to)})
        except Exception as e:
            log.error("Internal Server Error: {0}. "
                      "From: {1}. "
                      "To: {2}. "
                      "Text: {3}. "
                      "MO Id: {4}. "
                      "Operation Hash: {5}."
                      .format(e, from_, to, text, mo_id, self.MO_HASH).replace('\n',' '))
            return self.error({"status": "NOK", "message": "Could not send request. Internal error."}, 500)
