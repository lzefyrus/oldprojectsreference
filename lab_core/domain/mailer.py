# encoding: utf-8


import requests
from django.conf import settings


class Mail(object):

    @staticmethod
    def send(to, subject, text, html=False, attachments=()):
        """
        Sends email via Mailgun integration
        :param to: str
        :param subject: str
        :param text: str
        :param html: bool
        :param attachments: list['file_path', 'file_2_path']
        :return:
        """
        if type(to) is not list:
            to = [to]

        if attachments and type(attachments) is not list:
            attachments = [attachments]

        content_type = "html" if html else "text"

        data = {
            "from": settings.MAILGUN_EMAIL_SENDER,
            "to": to,
            "subject": subject,
            content_type: text,

        }
        files = [("attachment", open(attachment, 'rb')) for attachment in attachments]
        response = requests.post(url=settings.MAILGUN_URL,
                                 auth=("api", settings.MAILGUN_SECRET_API_KEY),
                                 data=data,
                                 files=files)
        if response.status_code != 200:
            raise RuntimeError("Email couldn't be sent. "
                               "Status: {0}. "
                               "Response: {1}. ".format(response.status_code, response.json()))

        return response.json()
