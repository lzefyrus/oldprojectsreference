import logging
from application.src.rewrites import APIHandler

# Log
log = logging.getLogger(__name__)

# Settings
partner_name = 'tim/fit'
api_version = 'v1/mock'


class BillingHandler(APIHandler):
    __urls__ = [r"/{0}/{1}/billing".format(partner_name, api_version),
                r"/{0}/{1}/billing/".format(partner_name, api_version)]

    def post(self):

        UNKNOWN_ERROR = False
        BUSINESS_ERROR = False

        if UNKNOWN_ERROR:
            return self.set_status(400)

        if not BUSINESS_ERROR:
            xml = '<?xml version="1.0" encoding="UTF-8"?>' \
            '<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:m0="http://xml.apache.org/xml-soap">' \
                '<SOAP-ENV:Body>' \
                    '<ns1:executeResponse soapenv:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:ns1="urn:cmg.stdapp.webservices.generalplugin">' \
                        '<executeReturn href="#id0"/>' \
                    '</ns1:executeResponse>' \
                    '<multiRef id="id0" soapenc:root="0" soapenv:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xsi:type="ns2:Map" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/" xmlns:ns2="http://xml.apache.org/xml-soap">' \
                        '<item>' \
                            '<key>SOAP_resultCode</key>' \
                            '<value>0</value>' \
                        '</item>' \
                        '<item>' \
                            '<key>ReservationID</key>' \
                            '<value></value>' \
                        '</item>' \
                        '<item>' \
                            '<key>SOAP_sessionID</key>' \
                            '<value>999</value>' \
                        '</item>' \
                        '<item>' \
                            '<key>Account_Type</key>' \
                            '<value>0</value>' \
                        '</item>' \
                    '</multiRef>' \
                '</SOAP-ENV:Body>' \
            '</SOAP-ENV:Envelope>'
            return self.success(xml)

        xml = '<?xml version="1.0" encoding="UTF-8"?>' \
            '<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:m0="http://xml.apache.org/xml-soap">' \
                '<SOAP-ENV:Body>' \
                    '<ns1:executeResponse soapenv:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:ns1="urn:cmg.stdapp.webservices.generalplugin">' \
                        '<executeReturn href="#id0"/>' \
                    '</ns1:executeResponse>' \
                    '<multiRef id="id0" soapenc:root="0" soapenv:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xsi:type="ns2:Map" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/" xmlns:ns2="http://xml.apache.org/xml-soap">' \
                        '<item>' \
                            '<key>SOAP_resultCode</key>' \
                            '<value>6</value>' \
                        '</item>' \
                    '</multiRef>' \
                '</SOAP-ENV:Body>' \
            '</SOAP-ENV:Envelope>'
        return self.success(xml)
