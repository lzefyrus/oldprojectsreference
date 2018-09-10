# -*- coding: utf-8 -*-

import logging
from datetime import datetime
from uuid import uuid4

from utils import APIHandler

log = logging.getLogger(__name__)
from game.models import User

uuid = lambda: uuid4().hex
now = lambda: datetime.utcnow()


class BrunaHandler(APIHandler):
    __urls__ = [r"/encontact/userdata/"]

    def initialize(self):
        self.db = self.application.settings.get('engine')

    def post(self, id):
        user = self.db.query(User).filter(User.facebook_id == id).first()
        data = {}
        if user:
            data = dict(name=user.name,
                        cpf=user.cpf,
                        email=user.email,
                        mobile=user.mobile,
                        address=user.address,
                        cep=user.cep,
                        city=user.city,
                        neighborhood=user.neighborhood,
                        numb=user.numb)

        self.write({'user': data})
