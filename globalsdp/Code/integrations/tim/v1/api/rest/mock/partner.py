"""
    This file intends to simulate all TIM API behaviours which will be accessed by the Gateway.
"""
from application.src.rewrites import APIHandler
from tornado.escape import json_decode
import logging

# Logging handler
log = logging.getLogger(__name__)

partner_name = 'tim'
api_version = 'v1'


class MockCancellationHandler(APIHandler):
    __urls__ = [r"/tim-mock/v1/subscription/([a-zA-Z\-0-9\.:,_]+)"]

    def delete(self, subscription_id):
        # Getting header (mandatory parameter)
        headers = self.request.headers
        try:
            bearer_token = headers['Authorization']
        except KeyError:
            log.error("Token not found in request")
            return self.error({"message": "Invalid Token"}, 401)

        # Getting URL param:
        if not subscription_id:
            log.error("Subscription_id not found in request")
            return self.error({"message": "Invalid subscription_id"})

        log.info("Cancellation successfully done.")
        return self.success({"message": "success"}, 204)


class MockSubscribeHandler(APIHandler):
    __urls__ = [r"/tim-mock/v1/subscription/([a-zA-Z\-0-9\.:,_%]+)/([a-zA-Z\-0-9\.:,_]+)"]

    def post(self, application_name, subscriber_address):
        # Getting header (mandatory parameter)
        headers = self.request.headers
        try:
            token = headers['Authorization']
        except KeyError:
            log.error("Token not found in request")
            return self.error({"message": "Invalid Token"}, 401)

        # Getting URL param:
        if not application_name or not subscriber_address:
            log.error("application_name or subscriber_address not found in requested URL")
            return self.error({"message": "application_name or subscriber_address not found in requested URL"})

        log.info("Subscribing successfully done.")
        success = {"subscriptionResp":
                      {"subscriptionId": "asd4tyg5vffv-sdfsdcfds-sdfsr4tfwe-asd32rff"}
                  }
        return self.success(success, 201)


class MockMtHandler(APIHandler):
    __urls__ = [r"/tim-mock/v1/oneapi/1/smsmessaging/outbound/([a-zA-Z\-0-9\.:,_]+)/requests"]

    def post(self, la):
        # Getting header (mandatory parameter)
        headers = self.request.headers
        try:
            token = headers['Authorization']
        except KeyError:
            log.error("Token not found in request")
            return self.error({"message": "Invalid Token"}, 401)

        # Getting URL param:
        if not la:
            log.error("LA not found on URL")
            error = {"requestError":
                         {"policyException":
                              {"messageId": "POL0001", "text": "Invalid la"}
                          }
                     }
            return self.error(error)

        # Getting body:
        try:
            body = json_decode(self.request.body)
        except:
            log.error("Invalid JSON Object")
            error = {"requestError":
                         {"policyException":
                              {"messageId": "POL0001", "text": "Invalid JSON OBJECT"}
                          }
                     }
            return self.error(error)

        try:
            body = body['outboundSMSMessageRequest']
            msisdn = body['address']
            la = body['senderAddress']
            message = body['outboundSMSTextMessage']
        except Exception as e:
            log.error("Missing mandatory parameters inside body: {0}".format(e))
            error = {"requestError":
                         {"policyException":
                              {"messageId": "POL0001", "text": "Missing mandatory parameters inside body"}
                          }
                     }
            return self.error(error)

        log.debug("MT successfully sent!")
        response = {"resourceReference":
                        {"resourceURL":
                             "http://127.0.1.1:8001/oneapi/1/smsmessaging/outbound/tel%3A1234/requests/-49409727900490796353-2051273256"
                         }
                    }
        return self.success(response, 201)


class MockBillingHandler(APIHandler):
    __urls__ = [r"/tim-mock/v1/oneapi/1/payment/([a-zA-Z\-0-9\.:,_]+)/transactions/amount"]

    def post(self, msisdn):
        # Getting header (mandatory parameter)
        headers = self.request.headers
        try:
            token = headers['Authorization']
        except KeyError:
            log.error("Token not found in request")
            return self.error({"message": "Invalid Token"}, 401)

        # Getting URL param:
        if not msisdn:
            log.error("Invalid msisdn on URL")
            error = {
                "requestError": {
                    "serviceException": {
                        "messageID": "System Generated ID",
                        "text": "Invalid msisdn on URL"
                    }
                }
            }
            return self.error(error)

        # Getting body:
        try:
            body = json_decode(self.request.body)
        except:
            log.error("Invalid JSON Object")
            error = {
                "requestError": {
                    "serviceException": {
                        "messageID": "System Generated ID",
                        "text": "Invalid JSON Object"
                    }
                }
            }
            return self.error(error)

        try:
            body = body['amountTransaction']
            msisdn = body['endUserId']
            amount = body['paymentAmount']['chargingInformation']['amount']
            code = body['paymentAmount']['chargingInformation']['code']
            tax_amount = body['paymentAmount']['chargingMetaData']['taxAmount']
            mandate_id = body['paymentAmount']['chargingMetaData']['mandateId']
            service_id = body['paymentAmount']['chargingMetaData']['serviceId']
            product_id = body['paymentAmount']['chargingMetaData']['productId']
            transaction_status = body['transactionOperationStatus']
            reference_code = body['referenceCode']
        except:
            log.error("Missing mandatory parameters inside body")
            error = {
                "requestError": {
                    "serviceException": {
                        "messageID": "System Generated ID",
                        "text": "Missing mandatory parameters inside body"
                    }
                }
            }
            return self.error(error)

        # Returns a response
        return self._response_201()

    def _response_201(self):
        response = {
            "amountTransaction": {
                "endUserId": "tel:5511988776601",
                "paymentAmount": {
                    "chargingInformation": {
                        "description": [
                            "chargeAmount"
                        ],
                        "amount": 1.0,
                        "code": "11241"
                    },
                    "chargingMetaData": {
                        "taxAmount": 0,
                        "mandateId": "1",
                        "serviceId": "558",
                        "productId": "0080000300001"
                    }
                },
                "transactionOperationStatus": "Charged",
                "referenceCode": "558",
                "resourceURL": "http://10.171.135.31:8080/oneapi/1/payment/tel%3A5511988776601/transactions/amount/10.171.135.35%3B1434572700%3B18-1435855573378"
            }
        }

        headers = {
            "Content-Type": "application/json",
            "X-Plugin-Param-Values": '10<Avp-List><Session-Id Flags="64">10.171.135.32;1426866124;257</Session-Id><Result-Code Flags="64">2001</Result-Code><Origin-Host Flags="64">10.171.29.173</Origin-Host><Origin-Realm Flags="64">internal.timbrasil.com.br</Origin-Realm><Auth-Application-Id Flags="64">4</Auth-Application-Id><CC-Request-Type Flags="64">4</CC-Request-Type><CC-Request-Number Flags="64">0</CC-Request-Number><Service-Parameter-Info><Service-Parameter-Type Flags="64">501</Service-Parameter-Type><Service-Parameter-Value Flags="64">1</Service-Parameter-Value></Service-Parameter-Info></Avp-List>,10.171.135.32;1426866124;257'
        }

        return self.success(response, 201, headers)

    def _response_400_A(self):
        error = {
            "requestError": {
                "serviceException": {
                    "messageId": "SVC0270",
                    "text": "Request denied by credit control server",
                    "variables": ["DIAMETER3001"]
                }
            }
        }
        return self.error(error)

    def _response_400_B(self):
        error = {
            "requestError": {
                "policyException": {
                    "messageId":"POL0001",
                    "text": "A policy error occurred. Error code is %1",
                    "variables": ["3004"]
                }
            }
        }
        return self.error(error)


class MockBillingStatusHandler(APIHandler):
    __urls__ = [r"/tim-mock/v1/oneapi/1/payment/([a-zA-Z\-0-9\.:,_]+)/transactions/amount/([a-zA-Z\-0-9\.:,_]+)"]

    def get(self, msisdn, transaction_id):
        # Getting URL param:
        if not msisdn or not transaction_id:
            log.error("msisdn or transaction_id not found on URL")
            error = {
                "requestError": {
                    "serviceException": {
                        "messageId": "SVC0001",
                        "text": "can't find transaction:10.114.200.60;1439304297;0-1439322538333"
                    }
                }
            }
            return self.error(error)

        log.debug("Billing Status successfully sent!")
        response = {
            "amountTransaction": {
                "endUserId": "tel:5511985236652",
                "paymentAmount": {
                    "chargingInformation": {
                        "description": ["chargeAmount"],
                        "amount": 1,
                        "code": "11336"
                    },
                    "totalAmountCharged": 1,
                    "chargingMetaData": {
                        "taxAmount": 0,
                        "mandateId": "1",
                        "productId": "0000000900005"
                    }
                },
                "transactionOperationStatus": "Charged",
                "referenceCode": "558",
                "resourceURL": "http://10.114.200.57:8080/oneapi/1/payment/tel%3A5511985236652/transactions/amount/10.114.200.60%3B1439304297%3B0-1439322538332"
            }
        }
        return self.success(response, 200)

        
class MockMigrationHandler(APIHandler):
    __urls__ = [r"/tim-mock/v1/daf/Migration/1/migration"]

    def post(self):
        # Getting header (mandatory parameter)
        headers = self.request.headers
        try:
            token = headers['Authorization']
        except KeyError:
            log.error("Token not found in request")
            return self.error({"message": "Invalid Token"}, 401)

        # Getting body:
        try:
            body = json_decode(self.request.body)
        except:
            log.error("Invalid JSON Object")
            error = {
                "requestError": {
                    "serviceException": {
                        "messageID": "SVC0001",
                        "text": "can't find transaction:10.114.200.60;1439304297;0-1439322538333"
                    }
                }
            }
            return self.error(error)

        try:
            subscription = body['subscription']
            msisdn = subscription['msisdn']
            application_id = subscription['applicationId']
        except KeyError:
            log.error("Missing mandatory parameters inside body")
            error = {
                "requestError": {
                    "serviceException": {
                        "messageID": "SVC0001",
                        "text": "Missing mandatory parameters inside body"
                    }
                }
            }
            return self.error(error)

        log.info("Migration successfully sent")
        response = {"amountTransaction": {
            "endUserId": "tel:{0}".format(msisdn),
            "paymentAmount": {
                "chargingInformation": {
                    "description": ["chargeAmount"],
                    "amount": 1,
                    "code": "11336"
                },
                "totalAmountCharged": 1,
                "chargingMetaData": {
                    "taxAmount": 0,
                    "mandateId": "1",
                    "productId": "0000000900005"
                }
            },
            "transactionOperationStatus": "Charged",
            "referenceCode": "558",
            "resourceURL":
            "http://10.114.200.57:8080/oneapi/1/payment/tel%3A{0}/transactions/amount/10.114.200.60%3B1439304297%3B0-1439322538332".format(msisdn)
            }
        }
        return self.success(response, 201)
