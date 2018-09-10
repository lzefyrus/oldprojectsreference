from wsgiref.simple_server import make_server
from soapfish import soap_dispatch
from gen import SERVICE

dispatcher = soap_dispatch.SOAPDispatcher(SERVICE)
app = soap_dispatch.WsgiSoapApplication({'/ChargePoint/services/chargePointService': dispatcher})

httpd = make_server('', 5000, app)
print("Serving HTTP on port 8000...")
httpd.serve_forever()