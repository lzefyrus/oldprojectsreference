"""
    This file intends to simulate all Backend's API behaviours which will be accessed by the SDP.
"""
from application.src.rewrites import APIHandler

partner_name = 'oi'
api_version = 'v1'


class MockMoHandler(APIHandler):
    __urls__ = [r"/{0}-mock/backend/{1}/mo(?:/)".format(partner_name, api_version),
                r"/{0}-mock/backend/{1}/entertainment/mo(?:/)".format(partner_name, api_version),]

    def get(self):
        # Getting arguments
        from_ = self.get_argument('from', None, strip=True)
        to = self.get_argument('to', None, strip=True)
        text = self.get_argument('text', None, strip=True)
        mo_id = self.get_argument('mo_id', None, strip=True)
        date = self.get_argument('date', None, strip=True)

        return self.success({
            "success": "1",
            "message": "MO notification received. From: {0}, To: {1}, Text: {2}, Mo_id: {3}, Date:{4}".format(
                from_, to, text, mo_id, date
            )
        })

