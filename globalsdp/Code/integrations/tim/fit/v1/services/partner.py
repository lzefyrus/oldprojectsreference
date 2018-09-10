import logging
import logging.config
import random
from vendor import smpplib
from application import settings
from application.src import utils
from application.src.models import Config
from application.src import databases

# Settings
partner_name = 'tim/fit'
api_version = 'v1'

# Logging handler
logging.config.dictConfig(settings.LOGGING)
log = logging.getLogger(__name__)
LOG_MO = settings.LOG_HASHES[partner_name]["mo"]

# DB
db = databases.DB().get_instance()

# Configs
configs = utils.list2dict(db.query(Config).all())


class MoService(object):

    @staticmethod
    def get_configs():
        """
        Returns MO configs.
        :return: dict (with all necessary MO configs)
        """
        return {
            'hosts': [
                configs['tim/fit/v1/smpp/host/1']['value'],
                configs['tim/fit/v1/smpp/host/2']['value'],
            ],
            'port': configs['tim/fit/v1/smpp/port']['value'],
            'login': configs['tim/fit/v1/smpp/login']['value'],
            'password': configs['tim/fit/v1/smpp/password']['value'],
            'queues': [
                'tim-fit-mo-0',
                'tim-fit-mo-1',
                'tim-fit-mo-2',
                'tim-fit-mo-3',
            ]
        }

    @staticmethod
    def message_received(pdu):
        """
        This is a closure used to handle received MOs.
        :param pdu:
        :return:
        """
        pass

    @staticmethod
    def choose_host(hosts):
        """
        Chooses a host randomly.
        :param hosts: list of hosts.
        :return: string (host name)
        """
        return random.choice(hosts)

    @classmethod
    def receive(cls):
        """
        Receives the MO through the SMPP client.
        This is an async task.
        :return:
        """

        # SMPP client
        client = None

        # Configs
        configs = cls.get_configs()

        try:
            ########################
            # Connect to SMPP server
            ########################
            host = MoService.choose_host(configs["hosts"])
            port = configs['port']

            try:
                client = SMPPService.connect(host, port)

            except Exception as e:
                log.error("Error: can't connect to SMPP server (verify your host/port). "
                          "Host: {0}. "
                          "Port: {1}. "
                          "Exception: {2}. "
                          "Operation Hash: {3} CONNECTION."
                          .format(host, port, e, LOG_MO))
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

                log.error("Error: can't bind to SMPP server (verify your login/password). "
                          "Login: {0}. "
                          "Password: {1}. "
                          "Exception: {2}. "
                          "Operation Hash: {3} CONNECTION."
                          .format(login, password, e, LOG_MO))
                return

            ##################
            # Receive messages
            ##################
            try:
                log.info("Connected and bound to SMPP server. Listening MOs. "
                         "Host: {0}. "
                         "Port: {1}. "
                         "Login: {2}. "
                         "Password: {3}. "
                         "Operation Hash: {4} CONNECTION."
                         .format(host, port, login, password, LOG_MO))

                client.listen()

            except Exception as e:
                log.error("Error: can't listen to SMPP server. "
                          "Exception: {0}. "
                          "Operation Hash: {1} CONNECTION."
                          .format(e, LOG_MO))

                try:
                    client.unbind()
                except Exception:
                    pass

                client.disconnect()

        except Exception as e:
            log.error("Error: an unexpected error occurred. Can't connect to SMPP server. "
                      "Exception: {0}. "
                      "Operation Hash: {1} CONNECTION."
                      .format(e, LOG_MO))

            if client:
                client.disconnect()


class SMPPService(object):

    @staticmethod
    def connect(host, port):
        """
        Connects to SMPP server.
        To connect to the SMPP server set host and port.
        A closure function must be set to handle received messages.
        :param host: SMPP host.
        :param port: SMPP port.
        :return: smpplib.client.Client
        """
        client = smpplib.client.Client(host=host, port=port)
        client.set_message_received_handler(func=MoService.message_received)
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
        For MO purpose we need a Receiver.
        :param client: smpplib.client.Client
        :param login: SMMP user login.
        :param password: SMMP user password.
        :return:
        """
        client.bind_receiver(system_id=login, password=password)


# Execution
MoService.receive()
