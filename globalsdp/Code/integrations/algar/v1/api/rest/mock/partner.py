"""
    This file intends to simulate all Partner's API behaviours which will be accessed by the SDP.
"""
from application.src.rewrites import APIHandler
import logging

# Logging handler
log = logging.getLogger(__name__)

partner_name = 'algar'
api_version = 'v1'


class MockSignatureHandler(APIHandler):
    __urls__ = [r"/{0}-mock/{1}/signature".format(partner_name, api_version)]

    def post(self):
        return self.success("""
        <tangram_response company_id="7" service_id="364">
          <provisioning code="0">
            <channel_id>2</channel_id>
            <description code="0">Request received</description>
            <destination code="0"
                         description="Request received">
              3108889999
            </destination>
            <response_datetime>200810095834198</response_datetime>
          </provisioning>
        </tangram_response>""")


class MockCancellationHandler(APIHandler):
    __urls__ = [r"/{0}-mock/{1}/cancellation".format(partner_name, api_version)]

    def post(self):
        return self.success("""
        <tangram_response company_id="7" service_id="364">
          <provisioning code="0">
            <channel_id>2</channel_id>
            <description code="0">Request received</description>
            <destination code="0"
                         description="Request received">
              3108889999
            </destination>
            <response_datetime>200810095834198</response_datetime>
          </provisioning>
        </tangram_response>""")


class MockMtHandler(APIHandler):
    __urls__ = [r"/algar-mock/v1/mt"]

    def post(self):
        return self.success("""
        <tangram_response company_id="2" service_id="21">
            <send code="0">
            <destination code="0" description="Message accepted" session_id="A434FD02" package_id="">
                <message_id>A434FD02</message_id>
                <message_id>A434FD03</message_id>
                3191324567</destination>
            <destination code="0" description="Message accepted" session_id="A434FD04" package_id="">
                <message_id>A434FD04</message_id>
                <message_id>A434FD05</message_id>
                3192345678</destination>
            <destination code="0" description="Message accepted" session_id="A434FD06" package_id="">
                <message_id>A434FD06</message_id>
                <message_id>A434FD07</message_id>
                3193456789</destination>
            <description code="0">Message accepted</description>
            <response_datetime>180902125033020</response_datetime>
            </send>
        </tangram_response>""")


class MockBillingHandler(APIHandler):
    __urls__ = [r"/algar-mock/v1/billing"]

    def post(self):
        return self.success("""
        <tangram_response company_id="2" service_id="21">
           <billing code="0">
              <destination code="0" description="Request processed" session_id="A434FD03">
                 <request_id>A434FD03</request_id>
                 <balance />
                 3192345678
              </destination>
              <description code="0">Request processed</description>
              <response_datetime>180902125033020</response_datetime>
           </billing>
        </tangram_response>""")
