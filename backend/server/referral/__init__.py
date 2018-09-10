# -*- coding: utf-8 -*-

import logging

from utils import SessionBaseHandler
from .models import ReferralRequest

log = logging.getLogger(__name__)

HTML = """<html>
<head>
    <meta http-equiv="refresh" content="2; url={}" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
    <meta charset="UTF-8" />
    <meta name="keywords" content="" />
    <meta name="description" content="Tá rolando vários prêmios loucos no next.me. Só vem." />
    <meta property="og:title" content="Next" />
    <meta property="og:description" content="Tá rolando vários prêmios loucos no next.me. Só vem." />
    <meta property="og:image" content="{}/assets/share-geral.jpg" />
    <meta property="og:type" content="website" />
    <meta name="theme-color" content="#000000" />
    <meta property="fb:app_id" content="143292476125192" />
    <title>Next.me</title>
    {}
</head>
<body>
redirecionando ...
    <noscript>
		<iframe src="//www.googletagmanager.com/ns.html?id=GTM-KSB3WC" height="0" width="0" style="display:none;visibility:hidden"></iframe>
	</noscript>
</body>
</html>
"""

GTM = """<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
      new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
      j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
      '//www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
      })(window,document,'script','dataLayer','GTM-KSB3WC');</script>"""


class ReferralHandler(SessionBaseHandler):
    def initialize(self):
        self.db = self.application.settings.get('engine')

    def get(self, referred=None):
        try:
            redirectp = '{}'.format(self.application.settings.get('instance', {}).get('front'), 'https://next.me')
            referred_ = self.db.query(ReferralRequest).filter(ReferralRequest.id == referred).first()
            if referred_:
                self.session['referred'] = referred_.user_id
        except Exception as e:
            log.error(e)
        finally:
            self.finish(HTML.format(redirectp, redirectp, GTM))
