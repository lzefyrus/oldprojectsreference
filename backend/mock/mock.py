import time

from flask import Flask, redirect, request
from flask_restful import reqparse, abort, Api, Resource
from flask_cors import CORS, cross_origin
from uuid import uuid4

app = Flask(__name__)
CORS(app, resources=r'/api/*')

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

api = Api(app)

CHEADER = {'Allow': 'POST,GET,PUT'}, 200, {'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'POST,PUT,GET', 'Access-Control-Allow-Headers': "Content-Type,Authorization"}

NEXT_LIFE = (4.20 * 60)


LIVES = 5
EXTRA_LIVES = False
MISSING_FORM = False

USER = {
  "status": "success",
  "nextLife": NEXT_LIFE,
  "email": "adriano@gmail.com",
  "state": "sp",
  "city": "São Paulo",
  "address": "Rua Estados Unidos, 136",
  "name": 'Adriano Fernandes',
  "avatar": {
    "big": 'http://graph.facebook.com/100002160106961/picture?type=large',
    "small": 'http://graph.facebook.com/100002160106961/picture?type=small'
  },
  "shareUrl": "http://www.next.me",
  "firstAccess": False,
  "lives": LIVES
}

PRIZE = {
  "level": "medium",
  "prize": {
    "name": "Boné Next by Rosário",
    "ico": "cap",
    "img": "http://placehold.it/200x200?text=Placeholder",
    "details": [
      "100% algodão", 
      "Regulador traseiro feito em plástico reciclado", 
      "Snapback cinco gomos"
    ]
  }
}

GAME = {
    "message": "",
    "icons": [
        {"code": "eb", "key": "cow"},
        {"code": "P8", "key": "note"},
        {"code": "RB", "key": "camera"},
        {"code": "nK", "key": "spray"},
        {"code": "oz", "key": "airplane"},
        {"code": "Aq", "key": "skate"},
        {"code": "N3", "key": "sun"},
        {"code": "re", "key": "helm"},
        {"code": "y5", "key": "tenis"},
        {"code": "p5", "key": "coco"},
        {"code": "9K", "key": "sunglass"},
        {"code": "0V", "key": "fone"}
    ],
    "status": "success",
    "nextLife": NEXT_LIFE
}

GAME2 = {
    "message": "",
    "icons": [
        {"code": "p5", "key": "note"},
        {"code": "P8", "key": "hand"},
        {"code": "eb", "key": "phone"},
        {"code": "nK", "key": "globo"},
        {"code": "oz", "key": "guitar"},
        {"code": "y5", "key": "disco"},
        {"code": "N3", "key": "ring"},
        {"code": "RB", "key": "joystick"},
        {"code": "9K", "key": "moto"},
        {"code": "Aq", "key": "spray"},
        {"code": "0V", "key": "megafone"},
        {"code": "re", "key": "lamp"}
    ],
    "status": "success",
    "nextLife": NEXT_LIFE
}

GAME3 = {
    "message": "",
    "icons": [
        {"code": "P8", "key": "lock"},
        {"code": "p5", "key": "chavetool"},
        {"code": "nK", "key": "raio"},
        {"code": "eb", "key": "book"},
        {"code": "y5", "key": "interruptor"},
        {"code": "oz", "key": "sino"},
        {"code": "RB", "key": "lamp"},
        {"code": "N3", "key": "ghost"},
        {"code": "Aq", "key": "sofa"},
        {"code": "9K", "key": "squeeze"},
        {"code": "re", "key": "location"},
        {"code": "0V", "key": "push"}
    ],
    "status": "success",
    "nextLife": NEXT_LIFE
}

GAME4 = {
    "message": "",
    "icons": [
        {"code": "P8", "key": "phone"},
        {"code": "p5", "key": "note"},
        {"code": "nK", "key": "heart_b"},
        {"code": "eb", "key": "car"},
        {"code": "y5", "key": "hand"},
        {"code": "oz", "key": "garfo"},
        {"code": "RB", "key": "microfone"},
        {"code": "N3", "key": "semaforo"},
        {"code": "Aq", "key": "flag"},
        {"code": "9K", "key": "tv"},
        {"code": "re", "key": "spray"},
        {"code": "0V", "key": "cow"}
    ],
    "status": "success",
    "nextLife": NEXT_LIFE
}

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response

def check_authorization(request):
    if not request.get('Authorization'):
        abort(401, message="Must login first")


def check_level(level):
    if level not in ['easy', 'medium', 'hard', 'impossible']:
        abort(404, message="Game level {} does note exist".format(level))


userparser = reqparse.RequestParser()
userparser.add_argument('state', location='json')
userparser.add_argument('city', location='json')
userparser.add_argument('address', location='json')
userparser.add_argument('email', location='json')
userparser.add_argument('optin', location='json')

gameparser = reqparse.RequestParser()
gameparser.add_argument('sequence', location='json')

userp = reqparse.RequestParser()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

@app.route('/auth/login')
def auth():
    next = request.args.get('next') or \
           request.referrer or \
           '/'
    pre = ''
    if 'http' not in pre:
        pre = 'http://{}'.format(pre)
    # return redirect('{}{}?code={}'.format(pre, next, uuid4().hex))
    return redirect('{}#/code/{}'.format(request.referrer, uuid4().hex))


# @app.route('/auth/login')
# def auth():
# next = request.args.get('next') or \
#        request.referrer or \
#        '/'
# pre = ''
# if 'http' not in pre:
#     pre = 'http://{}'.format(pre)
# return redirect('{}{}?code={}'.format(pre, next, uuid4().hex))

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

@app.route('/')
def dummy():
    return """<html>
        <head>
            <script language='Javascript'>
                window.opener[btoa('loginCallback').replace(/\=/g,'')]('{}');
                window.close();
            </script>
        </head>
        <body>
            <a href="javascript:window.close()"> Close Window</a>
        </body>
        </html>""".format(uuid4().hex)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

class Game(Resource):

    def get(self, level):
        check_level(level)
        check_authorization(request.headers)

        # if level == 'medium':
        #     abort(400, status='error', serverTime=int(time.time()), lives=2,
        #           message='Only one win per game level per week')

        if level == 'easy': 
          game = GAME.copy()

        if level == 'medium': 
          game = GAME2.copy()

        if level == 'hard': 
          game = GAME3.copy()

        if level == 'impossible': 
          game = GAME4.copy()

        game['nextLife'] = NEXT_LIFE
        return game

    def post(self, level):
        check_level(level)
        check_authorization(request.headers)
        args = gameparser.parse_args()

        if args['sequence'] == 'eb|P8|RB|nK':
            return {
                "message": "Congratulations ! You won !",
                "prize": PRIZE,
                "win": True,
                "status": "success",
                "nextLife": NEXT_LIFE,
                "lives": LIVES
            }
        if args['sequence'] == 'a1|b2':
            abort(400, **{
                "message": "No more lives, wait for new ones.",
                "win": False,
                "status": "error",
                "nextLife": NEXT_LIFE,
                "lives": LIVES
            })

        if args['sequence'] == 'a1':
            abort(400, **{
                "message": "Only one win per game level per week",
                "win": False,
                "status": "error",
                "nextLife": NEXT_LIFE,
                "lives": LIVES
            })

        return {
            "message": "Not this time.",
            "win": False,
            "status": "success",
            "nextLife": NEXT_LIFE,
            "lives": LIVES
        }

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

class Challenge(Resource):

    def get(self):
        return {
            "levels": [
                {
                    "name": "easy",
                    "locked": False,
                    "soldOut": False,
                    "prize": {}
                    # "prize": {
                    #     "name": "Boné Next by Rosário.",
                    #     "img": "bone.png",
										# 		"ico": "cap",
                    #     "details": [
                    #         "100% algodão", 
                    #         "Regulador traseiro feito em plástico reciclado", 
                    #         "Snapback cinco gomos"
                    #     ]
                    # }                
                },{

                    "name": "medium",
                    "locked": True,
                    "soldOut": False,
                    "prize": {
                        "name": "Outra coisa by Alguém.",
                        "img": "bone.png",
												"ico": "lamp",
                        "details": [
                            "100% algodão", 
                            "Regulador traseiro feito em plástico reciclado", 
                            "Snapback cinco gomos"
                        ]
                    }                
                },{

                    "name": "hard",
                    "locked": False,
                    "soldOut": True,
                    "prize": {}
                    # "prize": {
                    #     "name": "Boné Next by Rosário",
                    #     "img": 'bone.png',
										# 
                    #     "details": [
                    #         "100% algodão", 
                    #         "Regulador traseiro feito em plástico reciclado", 
                    #         "Snapback cinco gomos"
                    #     ]
                    # }                
                },{

                    "name": "impossible",
                    "locked": False,
                    "soldOut": True,
                    "prize": {
                        "name": "Boné Next by Rosário",
                        "img": "bone.png",
												"ico" : "experience",
                        "details": [
                            "100% algodão", 
                            "Regulador traseiro feito em plástico reciclado", 
                            "Snapback cinco gomos"
                        ]
                    }
                }
            ],
            "status": "success",
            "nextLife": NEXT_LIFE,
            "lives": LIVES
        }

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

class Friends(Resource):
    def get(self):
        check_authorization(request.headers)
        return {
            "friends": [],
            "status": "success",
            "nextLife": NEXT_LIFE
        }

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

class User(Resource):

    def post(self):
        args = userparser.parse_args()
        check_authorization(request.headers)
        for k, w in args.items():
            if w in ['', None, False, 0, []]:
                abort(400, message='Field {} is required'.format(k))
        return USER

    def get(self):
        check_authorization(request.headers)
        args = userp.parse_args()
        data = USER
        if MISSING_FORM:
            data['missing'] = PRIZE
        else:
            data['missing'] = {}

        return data

    def put(self):
        check_authorization(request.headers)
        args = userp.parse_args()
        data = USER
        if MISSING_FORM:
            data['missing'] = PRIZE
        else:
            data['missing'] = {}

        return data

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

class Tips(Resource):

    def get(self, level=''):
        check_authorization(request.headers)
        check_level(level)
        if level == 'medium':
            return {'tips': [],
                    "status": "success",
                    "nextLife": NEXT_LIFE
                    }

        return {'tips': [
            "Prêmio 1: Rola usar em qualquer lugar. Menos na mesa.",
            "Prêmio 2: Pro look é bom, né?",
            "O melhor esquema pra se proteger do sol.",
            "Gluglu ié ié, eu nunca tiro o meu.",
            "Rola usar em qualquer lugar. Menos na mesa.",
            "Pro look é bom, né?",
            "O melhor esquema pra se proteger do sol.",
            "Gluglu ié ié, eu nunca tiro o meu.",
            "Rola usar em qualquer lugar. Menos na mesa.",
            "Pro look é bom, né?",
            "O melhor esquema pra se proteger do sol.",
            "Gluglu ié ié, eu nunca tiro o meu.",
            "Rola usar em qualquer lugar. Menos na mesa.",
            "Pro look é bom, né?",
            "O melhor esquema pra se proteger do sol.",
            "Gluglu ié ié, eu nunca tiro o meu.",
            "Pra frente ou pra trás, você quem faz o estilo."
        ],
            "status": "success",
            "nextLife": NEXT_LIFE}

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

class Ping(Resource):

    def get(self):
        check_authorization(request.headers)
        return {
          "extraLives": EXTRA_LIVES,
          "status": "success",
          "nextLife": NEXT_LIFE
        }

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

class Prizes(Resource):

    def get(self):
        return {
          "totals": {
            "prizes": {
              "total": 500,
              "delivered": 500
            },
            "users": 27983,
            "tries": 233984
          },
          "prizes": [
            {
              "key": "prize-0",
              "total": 100,
              "delivered": 20,
              "level": "easy"
            },{
              "key": "prize-1",
              "total": 100,
              "delivered": 60,
              "level": "medium"
            },{
              "key": "prize-2",
              "total": 100,
              "delivered": 20,
              "level": "hard"
            },{
              "key": "prize-3",
              "total": 100,
              "delivered": 10,
              "level": "impossible"
            }
          ],
          "status": "success",
          "nextLife": NEXT_LIFE
        }

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

##
## Actually setup the Api resource routing here
##
api.add_resource(Game, '/api/game/<level>')
api.add_resource(User, '/api/user')
api.add_resource(Friends, '/api/friends')
api.add_resource(Challenge, '/api/challenge')
api.add_resource(Tips, '/api/tips/<level>')
api.add_resource(Ping, '/api/ping')
api.add_resource(Prizes, '/api/prizes')

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", threaded=True, port=8889)
