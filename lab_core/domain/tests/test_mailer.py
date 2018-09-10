# encode: utf-8

from unittest.mock import Mock, patch

from rest_framework.test import APITestCase

from domain.mailer import Mail


class TestFirebaseCloudMessaging(APITestCase):

    mock_post_patcher = None
    mock_post = None
    patient = None

    @classmethod
    def setUp(cls):
        cls.mock_post_patcher = patch('domain.mailer.requests.post')
        cls.mock_post = cls.mock_post_patcher.start()

    @classmethod
    def tearDown(cls):
        cls.mock_post_patcher.stop()

    def test_send_push_notification_200_success(self):
        # Configure the mock to return a response with an OK status code.
        mailgun_success_response = {
            'id': '<20170411230739.91826.33041.923A977A@saracare.com.br>',
            'message': 'Queued. Thank you.'
        }
        self.mock_post.return_value = Mock()
        self.mock_post.return_value.status_code = 200
        self.mock_post.return_value.json.return_value = mailgun_success_response

        # Call the service, which would send a request to the server.
        response = Mail.send(to="test@gmail.com", subject="test", text="Hello, world!")

        # If the request is sent successfully.
        self.assertDictEqual(response, mailgun_success_response)

    def test_send_push_notification_400_error(self):
        # Configure the mock to return a response with a 400 status code.
        self.mock_post.return_value = Mock()
        self.mock_post.return_value.status_code = 400

        # Call the service, which would send a request to the server.
        try:
            # When status_code != 200, Mail class should raise a RunTimeError
            Mail.send(to="test@gmail.com", subject="test", text="Hello, world!")
            self.assertTrue(False, "400 error wrongly catched")
        except RuntimeError:
            self.assertTrue(True)

