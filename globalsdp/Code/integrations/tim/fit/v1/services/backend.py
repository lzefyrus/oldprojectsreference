import logging
import boto3
import datetime
import random
from vendor import smpplib
from application.src.celeryapp import CeleryApp, Configs
from application.src import databases
import application.settings as settings
from lxml import etree
import requests
import re
from application.src.exceptions import UnexpectedResponse


# Settings
partner_name = 'tim/fit'
api_version = 'v1'

# Logging handler
log = logging.getLogger(__name__)
LOG_BILLING = settings.LOG_HASHES[partner_name]["billing"]
LOG_MT = settings.LOG_HASHES[partner_name]["mt"]

# Celery App
celery = CeleryApp.get_instance()


class BillingService(object):

    @staticmethod
    def get_configs(settings):
        """
        Returns Billing configs.
        :param settings:
        :return: dict
        """
        return {
            'wsdl': settings["config"]["tim/fit/v1/billing/wsdl"]["value"],
            'file': settings["config"]["tim/fit/v1/billing/file/path"]["value"],
            'kinesis': {
                'aws_access_key_id': settings["config"]["tim/fit/v1/billing/kinesis/aws_access_key_id"]["value"],
                'aws_secret_access_key': settings["config"]["tim/fit/v1/billing/kinesis/aws_secret_access_key"]["value"],
                'region_name': settings["config"]["tim/fit/v1/billing/kinesis/region_name"]["value"],
                'stream': settings["config"]["tim/fit/v1/billing/kinesis/stream"]["value"],
                'shard': settings["config"]["tim/fit/v1/billing/kinesis/shard"]["value"],
                'iterator': settings["config"]["tim/fit/v1/billing/kinesis/iterator"]["value"],
            }
        }

    @staticmethod
    def get_billing_key(body):
        """
        Returns the key used to uniquely identify a billing transaction.
        :param body:
        :return: string
        """
        return "{0}:{1}".format(body['msisdn'], body['contract_id'])

    @staticmethod
    def get_request(body, operation=1, recipient_number=1, reservation_id=""):
        """
        Returns the XML for SOAP Request.
        :param body: body containing the billing parameters.
        :param operation: 0=Reserve. 1=Direct Debit. 2=Commit reservation. 3=Rollback reservation. Default value = 1
        :param recipient_number: This field is used to be multiplied by service price. Default value = 1
        :param reservation_id: We won't use reservation. Default value = ""
        :return: string
        """
        return '<?xml version="1.0" encoding="ISO-8859-1"?>' \
               '' \
               '<SOAP-ENV:Envelope ' \
                    'SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" ' \
                    'xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" ' \
                    'xmlns:xsd="http://www.w3.org/2001/XMLSchema" ' \
                    'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" ' \
                    'xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/">' \
               '' \
                    '<SOAP-ENV:Body>' \
                        '<ns7182:operationRequest xmlns:ns7182="http://tempuri.org">' \
                            '<item xsi:type="q0:mapItem">' \
                                '<key xsi:type="xsd:string">EndUserMSISDN</key>' \
                                '<value xsi:type="xsd:string">{0}</value>' \
                            '</item>' \
                            '<item xsi:type="q0:mapItem">' \
                                '<key xsi:type="xsd:string">Operation</key>' \
                                '<value xsi:type="xsd:string">{1}</value></item>' \
                            '<item xsi:type="q0:mapItem">' \
                                '<key xsi:type="xsd:string">Application_ID</key>' \
                                '<value xsi:type="xsd:string">{2}</value>' \
                            '</item>' \
                            '<item xsi:type="q0:mapItem">' \
                                '<key xsi:type="xsd:string">Service_Provider_ID</key>' \
                                '<value xsi:type="xsd:string">{3}</value>' \
                            '</item>' \
                            '<item xsi:type="q0:mapItem">' \
                                '<key xsi:type="xsd:string">Contract_ID</key>' \
                                '<value xsi:type="xsd:string">{4}</value>' \
                            '</item>' \
                            '<item xsi:type="q0:mapItem">' \
                                '<key xsi:type="xsd:string">ReservationID</key>' \
                                '<value xsi:type="xsd:string">{5}</value>' \
               '            </item>' \
                            '<item xsi:type="q0:mapItem">' \
                                '<key xsi:type="xsd:string">Recipients_number</key>' \
                                '<value xsi:type="xsd:string">{6}</value>' \
                            '</item>' \
                        '</ns7182:operationRequest>' \
                    '</SOAP-ENV:Body>' \
               '</SOAP-ENV:Envelope>'\
            .format(body['msisdn'],
                    operation,
                    body['application_id'],
                    body['service_provider_id'],
                    body['contract_id'],
                    reservation_id,
                    recipient_number)

    @staticmethod
    def get_response(xml):
        """
        Returns the response in JSON format.

        Firstly: prepares the XML by removing unwanted strings.
        Secondly: parses the xml and turn it into a JSON.

        The received XML looks like this:

        ERROR:

        <?xml version="1.0" encoding="UTF-8"?>
            <SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:m0="http://xml.apache.org/xml-soap">
                <SOAP-ENV:Body>
                    <ns1:executeResponse soapenv:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:ns1="urn:cmg.stdapp.webservices.generalplugin">
                        '<executeReturn href="#id0"/>
                    </ns1:executeResponse>
                    <multiRef id="id0" soapenc:root="0" soapenv:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xsi:type="ns2:Map" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/" xmlns:ns2="http://xml.apache.org/xml-soap">
                        <item>
                            <key>SOAP_resultCode</key>
                            <value>6</value>
                        </item>
                    </multiRef>
                </SOAP-ENV:Body>
            </SOAP-ENV:Envelope>

        SUCCESS:

        <?xml version="1.0" encoding="UTF-8"?>
        <SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:m0="http://xml.apache.org/xml-soap">
            <SOAP-ENV:Body>
                <ns1:executeResponse soapenv:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:ns1="urn:cmg.stdapp.webservices.generalplugin">
                    <executeReturn href="#id0"/>
                </ns1:executeResponse>
                <multiRef id="id0" soapenc:root="0" soapenv:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xsi:type="ns2:Map" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/" xmlns:ns2="http://xml.apache.org/xml-soap">
                    <item>
                        <key>SOAP_resultCode</key>
                        <value>0</value>
                    </item>
                    <item>
                        <key>ReservationID</key>
                        <value></value>
                    </item>
                    <item>
                        <key>SOAP_sessionID</key>
                        <value>999</value>
                    </item>
                    <item>
                        <key>Account_Type</key>
                        <value>0</value>
                    </item>
                </multiRef>
            </SOAP-ENV:Body>
        </SOAP-ENV:Envelope>
        """

        def prepare_xml(xml):
            """
            Prepares the received XML response by removing unwanted strings.
            """
            prepared = re.sub('ns[0-9]:', '', xml)
            prepared = prepared.replace("""<?xml version="1.0" encoding="UTF-8"?>""", "")\
                               .replace("SOAP-ENV:", "")\
                               .replace("soapenv:", "")\
                               .replace("\n", "")\

            return prepared

        def parse_response_to_json(xml_response):
            """
            Parses the XML response to a JSON.

            - soap_result_code: Result code from business logic:
                                0=Status OK
                                1=Connection Error
                                2=Unsupported Operation
                                3=Unknown user
                                4=Insufficient funds
                                5=Time-out
                                6=Other error
                                7=Post-paid blacklist status
                                8=MSISDN Blocked (M2M & Corporate plans)
                                9=MSISDN Blocked for VAS Content

            - reservation_id: The reservation identifier. Used as correlation ID.

            - soap_session_id: Session ID used by Web Services activity internally.

            - account_type: Prepaid (0) or Postpaid (1)
            """
            xml_response = xml_response.find("Body")
            xml_response = xml_response.find("multiRef")

            soap_result_code = ""
            reservation_id = ""
            soap_session_id = ""
            account_type = ""

            for child in xml_response:
                key = child.find("key").text
                value = child.find("value").text

                if key == "SOAP_resultCode":
                    soap_result_code = value or ""
                    continue
                if key == "ReservationID":
                    reservation_id = value or ""
                    continue
                if key == "SOAP_sessionID":
                    soap_session_id = value or ""
                    continue
                if key == "Account_Type":
                    account_type = value or ""
                    continue

            return {
                "success": 1 if soap_result_code == "0" else 0,
                "soap_result_code": soap_result_code,
                "reservation_id": reservation_id,
                "soap_session_id": soap_session_id,
                "account_type": account_type,
            }

        response = etree.XML(prepare_xml(xml))
        response = parse_response_to_json(response)

        return response

    @classmethod
    def bill(cls, xml, wsdl, timeout=10):
        """
        Sends the billing transaction.
        :param xml:
        :param wsdl:
        :param timeout:
        :return: dict
        """
        response = requests.post(url=wsdl, data=xml, timeout=timeout)

        if response.status_code == 200:
            xml = response.text
            return cls.get_response(xml)

        raise UnexpectedResponse("Response received is not 200 it's {0}".format(response.status_code))

    @classmethod
    def finish(cls, settings, body, billing_key, status):
        """
        Finishes the billing process.
        :param billing_key: identifies a billing request uniquely.
        :param status: 0(error) or 1(success).
        :return:
        """
        if status == 0:
            try:
                redis = databases.Redis.get_instance("redis-prebilling")
                redis.delete(billing_key)
            except Exception as e:
                # If redis is out, ignore this step.
                pass

        cls.save(settings, body, status)

    @classmethod
    def save(cls, settings, body, success):
        """
        Saves billing information.
        Used on prebilling generic decorator.
        :param settings:
        :param body:
        :param success:
        :return:
        """
        try:
            configs = cls.get_configs(settings)
            date = datetime.datetime.now()

            cls.save_to_file(configs, body, date, success)
            cls.save_to_stream(configs, body, date, success)
        except Exception as e:
                # If something goes wrong, ignore this step.
                pass

    @classmethod
    def save_to_file(cls, configs, body, date, success):
        """
        Saves billing information into a file.
        :param configs:
        :param body:
        :param date:
        :param success:
        :return: boolean
        """
        try:
            path = configs['file']
            data = cls.format_parameters(body, date, success)

            with open(path, "a") as file:
                file.write(data)
            return True

        except:
            return False

    @classmethod
    def save_to_stream(cls, configs, body, date, success):
        """
        Saves billing information into stream (Kinesis).
        :param configs:
        :param body:
        :param date:
        :param success:
        :return: boolean
        """
        try:
            kinesis = boto3.client(
                'kinesis',
                aws_access_key_id=configs['kinesis']['aws_access_key_id'],
                aws_secret_access_key=configs['kinesis']['aws_secret_access_key'],
                region_name=configs['kinesis']['region_name']
            )

            response = kinesis.get_shard_iterator(
                StreamName=configs['kinesis']['stream'],
                ShardId=configs['kinesis']['shard'],
                ShardIteratorType=configs['kinesis']['iterator']
            )

            response = kinesis.put_record(
                StreamName=configs['kinesis']['stream'],
                Data=cls.format_parameters(body, date, success),
                PartitionKey=response['ShardIterator'],
            )

            return True if 'ShardId' in response else False

        except:
            return False

    @staticmethod
    def format_parameters(body, date, success):
        """
        Formats billing parameters as a string to be saved.
        :param body:
        :param date:
        :param success:
        :return: string
        """
        try:
            return "{0}|{1}|{2}|{3}|{4}|{5}\n".format(
                body['msisdn'], body['application_id'], body['contract_id'], body['service_provider_id'],
                date, success
            )

        except:
            return ""


class MtService(object):

    @staticmethod
    def get_configs(settings):
        """
        Returns MT configs.
        :param settings: a dict with all application settings.
        :return: dict (with all necessary MT configs)
        """
        return {
            'hosts': [
                settings['config']['tim/fit/v1/smpp/host/1']['value'],
                settings['config']['tim/fit/v1/smpp/host/2']['value'],
            ],
            'port': settings['config']['tim/fit/v1/smpp/port']['value'],
            'login': settings['config']['tim/fit/v1/smpp/login']['value'],
            'password': settings['config']['tim/fit/v1/smpp/password']['value'],
            'queues': [
                'tim-fit-mt-0',
                'tim-fit-mt-1',
                'tim-fit-mt-2',
                'tim-fit-mt-3',
            ]
        }

    @staticmethod
    def message_sent(pdu):
        """
        This is a closure used to handle sent MTs.
        :param pdu:
        :return:
        """
        pass

    @staticmethod
    def choose_queue(queues, priority):
        """
        Chooses a queue according to priority.
        :param queues: list of queues.
        :param priority: priority level (0 to 3).
        :return: string (queue name)
        """
        return queues[priority]

    @staticmethod
    def choose_host(hosts):
        """
        Chooses a host randomly.
        :param hosts: list of hosts.
        :return: string (host name)
        """
        return random.choice(hosts)

    @staticmethod
    @celery.task(base=Configs, name="tim.fit.v1.backend.send_mt")
    def send(configs, body, msisdn, la, message):
        """
        Sends the MT through the SMPP client.
        This is an async task.
        :param configs:
        :param body:
        :param msisdn:
        :param la:
        :param message:
        :return:
        """

        # SMPP client
        client = None

        try:
            ########################
            # Connect to SMPP server
            ########################
            host = MtService.choose_host(configs["hosts"])
            port = configs['port']

            try:
                client = SMPPService.connect(host, port)

            except Exception as e:
                MtService.send.log.error("Could not send MT request to partner. "
                                         "Request body: {0}. "
                                         "Host: {1}. "
                                         "Port: {2}. "
                                         "Error: can't connect to SMPP server (verify your host/port). "
                                         "Exception: {3}. "
                                         "Operation Hash: {4}."
                                         .format(body, host, port, e, LOG_MT))
                return

            #####################
            # Bind to SMPP server
            #####################
            login = configs['login']
            password = configs['password']

            try:
                SMPPService.bind(client, login, password)

            except Exception as e:
                client.disconnect()

                MtService.send.log.error("Could not send MT request to partner. "
                                         "Request body: {0}. "
                                         "Login: {1}. "
                                         "Password: {2}. "
                                         "Error: can't bind to SMPP server (verify your login/password). "
                                         "Exception: {3}. "
                                         "Operation Hash: {4}."
                                         .format(body, login, password, e, LOG_MT))
                return

            ##############
            # Send message
            ##############
            try:
                SMPPService.send(client, message, msisdn, la)

                MtService.send.log.info("MT request sent to partner. "
                                        "Request body: {0}. "
                                        "Operation Hash: {1}."
                                        .format(body, LOG_MT))

            except Exception as e:
                MtService.send.log.error("Could not send MT request to partner. "
                                         "Request body: {0}. "
                                         "Error: can't send SMS. "
                                         "Exception: {1}. "
                                         "Operation Hash: {2}."
                                         .format(body, e, LOG_MT))

            finally:
                try:
                    client.unbind()
                except Exception:
                    pass

                client.disconnect()

        except Exception as e:
            MtService.send.log.error("Could not send MT request to partner. "
                                     "Request body: {0}. "
                                     "Error: an unexpected error occurred. "
                                     "Exception: {1}. "
                                     "Operation Hash: {2}."
                                     .format(body, e, LOG_MT))

            if client:
                client.disconnect()


class SMPPService(object):

    @staticmethod
    def connect(host, port):
        """
        Connects to SMPP server.
        To connect to the SMPP server set host and port.
        A closure function must be set to handle sent messages.
        :param host: SMPP host.
        :param port: SMPP port.
        :return: smpplib.client.Client
        """
        client = smpplib.client.Client(host=host, port=port)
        client.set_message_sent_handler(func=MtService.message_sent)
        client.connect()
        return client

    @staticmethod
    def bind(client, login, password):
        """
        After connected we must bind to the SMPP server.
        To bind to the SMPP server set login and password.
        The bind command determines in which direction will be possible to send messages, there are 3 bind types:
        1) Transmitter: only allows client to submit messages to the server.
        2) Receiver: means that the client will only receive the messages.
        3) Transceiver: allows message transfer in both directions.
        For MT purpose we need a Transmitter.
        :param client: smpplib.client.Client
        :param login: SMMP user login.
        :param password: SMMP user password.
        :return:
        """
        client.bind_transmitter(system_id=login, password=password)

    @staticmethod
    def send(client, message, msisdn, la):
        """
        After connected and bound we can send the message.
        The SMPP protocol is based on pairs of request/response PDUs (also known as packets).
        After the send we must unbind and disconnect from the SMPP server.
        :param client: smpplib.client.Client
        :param message:
        :param msisdn:
        :param la:
        :return:
        """

        parts, encoding_flag, msg_type_flag = smpplib.gsm.make_parts(message)
        for part in parts:
            client.send_message(
                source_addr=la,
                destination_addr=msisdn,
                short_message=part,
                source_addr_ton=smpplib.consts.SMPP_TON_ALNUM,
                dest_addr_ton=smpplib.consts.SMPP_TON_INTL,
                data_coding=encoding_flag,
                esm_class=msg_type_flag,
                registered_delivery=True,
            )
