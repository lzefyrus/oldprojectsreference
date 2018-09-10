"""
    This file intends to simulate all Partner's API behaviours which will be accessed by the SDP.
"""
from application.src.rewrites import APIHandler
from tornado.escape import json_decode
import logging
import json
# Logging handler
log = logging.getLogger(__name__)

partner_name = 'claro'
api_version = 'v1'


class MockMtHandler(APIHandler):
    __urls__ = [r"/{0}-mock/{1}/mt".format(partner_name, api_version)]

    def get(self):
        return self.success("""
        <mse-response>
           <status-code>0</status-code>
           <profile>profleID</profile>
           <transaction-id>1010608241424538336</transaction-id>
           <parameters>
              <param-item>
                 <param-name>INITIALDATE</param-name>
                 <param-value>0608151207</param-value>
              </param-item>
              <param-item>
                 <param-name>SMPP_MESSAGE_STATUS</param-name>
                 <param-value>DELIVRD</param-value>
              </param-item>
              <param-item>
                 <param-name>ANUM</param-name>
                 <param-value>333</param-value>
              </param-item>
              <param-item>
                 <param-name>BNUM</param-name>
                 <param-value>1191000000</param-value>
              </param-item>
              <param-item>
                 <param-name>FINALDATE</param-name>
                 <param-value>0608151207</param-value>
              </param-item>
              <param-item>
                 <param-name>MSGSTATUS</param-name>
                 <param-value>2</param-value>
              </param-item>
           </parameters>
        </mse-response>""")


class MockMmsMtHandler(APIHandler):
    __urls__ = [r"/{0}-mock/{1}/mms".format(partner_name, api_version)]

    def post(self):
        return self.success("""
        <mse-response>
           <status-code>0</status-code>
           <profile>profleID</profile>
           <transaction-id>1010608241424538336</transaction-id>
           <parameters>
              <param-item>
                 <param-name>CTN</param-name>
                 <param-value>1191000000</param-value>
              </param-item>
              <param-item>
                 <param-name>MMS</param-name>
                 <param-value>
                    Content-Type%3A+multipart%2Frelated%3B+%0Aboundary%3D%22----
                    %3D_Part_293_32260093.1084542774606%22%0ASubject%3A+mms+example%0A%0A------
                    %3D_Part_293_32260093.1084542774606%0AContent-ID%3A+%3Ctext0.txt%3E%0AContent-
                    Type%3A+text%2Fplain%3B+charset%3DUTF-8%0A%0Atext+content+sample%0A------
                    %3D_Part_293_32260093.1084542774606%0AContent-Transfer-
                    Encoding%3A+binary%0AContent-
                    Type%3A+image%2Fgif%0A%0AGIF89a%15%00%0E%00%A2%00%00%FF%FF%FF%FF%FFf%FF%CC%00%
                    FF%993%CCf%00%00%99%CC%00%00%00%00%00%00%21%F9%04%01%00%00%07%00%2C%00%00%00%0
                    0%15%00%0E%00%00%03Xx%BAgn%2CJ%27j%80r%B96z%BF%D8%24%5CC0VV%C8%18%83u%A2%A8%0A
                    %28%ACi%B7%02Pa%F31%B3%A7%40%A0%050%E8%04%3C%1F%076%AC%1C%09%C9%1F%CC%82%8B%29
                    f%C5%16%810%85%25%7D%AC%81%A3Z%E9%A8%94%0DLX%60%3Eg%1A%DB%01%F4%FD%7E%B8%23%09
                    %00%3B%0A------%3D_Part_293_32260093.1084542774606--%0A%0A
                </param-value>
              </param-item>
           </parameters>
        </mse-response>""")


class MockWapMtHandler(APIHandler):
    __urls__ = [r"/{0}-mock/{1}/wap".format(partner_name, api_version)]

    def get(self):
        # msisdn = json.dumps({k: self.get_argument(k) for k in self.request.arguments})
        # msisdn = self.get_query_argument("pwd", None)
        return self.success("""
        <mse-response>
            <status-code>0</status-code>
            <profile>profileId</profile>
            <transaction-id>1010608241424538336</transaction-id>
            <parameters>
               <param-item>
                  <param-name>SMPP_MESSAGE_STATUS</param-name>
                  <param-value>DELIVRD</param-value>
               </param-item>
               <param-item>
                  <param-name>MSGSTATUS</param-name>
                  <param-value>2</param-value>
               </param-item>
               <param-item>
                  <param-name>FINALDATE</param-name>
                  <param-value>0608241423</param-value>
               </param-item>
               <param-item>
                  <param-name>ANUM</param-name>
                  <param-value>9619991224</param-value>
               </param-item>
               <param-item>
                  <param-name>INITIALDATE</param-name>
                  <param-value>0608241423</param-value>
               </param-item>
               <param-item>
                  <param-name>BNUM</param-name>
                  <param-value>4001</param-value>
               </param-item>
            </parameters>
        </mse-response>""")


class MockCheckCreditHandler(APIHandler):
    __urls__ = [r"/{0}-mock/{1}/check-credit".format(partner_name, api_version)]

    def get(self):
        return self.success("""
        <mse-response>
            <status-code>0</status-code>
            <profile>profleID</profile>
            <transaction-id>1010608151540160083</transaction-id>
            <parameters>
               <param-item>
                  <param-name>IS_PREPAID</param-name>
                  <param-value>false</param-value>
               </param-item>
               <param-item>
                  <param-name>HAS_CREDIT</param-name>
                  <param-value>true</param-value>
               </param-item>
               <param-item>
                  <param-name>TECNOLOGY</param-name>
                  <param-value>GSM</param-value>
               </param-item>
            </parameters>
         </mse-response>""")


class BillingHandler(APIHandler):
    __urls__ = [r"/{0}-mock/{1}/billing".format(partner_name, api_version)]

    def get(self):
        return self.success("""
        <mse-response>
            <status-code>0</status-code>
            <profile>profleID</profile>
            <transaction-id>1010608241424538336</transaction-id>
        </mse-response>""")


class WibPushHandler(APIHandler):
    __urls__ = [r"/{0}-mock/{1}/wib-push".format(partner_name, api_version)]

    def get(self):
        return self.success("""
        <mse-response>
            <status-code>0</status-code>
            <profile>profleID</profile>
            <transaction-id>1010608241424538336</transaction-id>
        </mse-response>""")

