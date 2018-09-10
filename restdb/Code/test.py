#!/usr/bin/env python
#
# Copyright 2009 Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os.path
import uuid

import tornado.escape
import tornado.ioloop
import tornado.web
from tornado.options import parse_command_line


class MainHandler(tornado.web.RequestHandler):
    def initialize(self, guid):
        self.guid = guid
        self.guid.append(uuid.uuid4().hex)

    def get(self):
        self.write('\n'.join(self.guid))


class Manin2(tornado.web.RedirectHandler):
    def initialize(self, guid):
        self.guid = guid
        self.guid.append(uuid.uuid4().hex)

    def get(self):
        self.write('\n-- '.join(self.guid))


def main():
    parse_command_line()
    dd = []
    app = tornado.web.Application(
        [
            (r"/1", MainHandler, dict(guid=dd)),
            (r"/2", Manin2, dict(guid=dd)),
        ],
        cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        xsrf_cookies=True,

    )
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
