from flask_restful_swagger_3 import Schema


class EchoModel(Schema):
    type = 'object'

    properties = {
        'msg': {
            'type': 'string'
        },
        'status': {
            'type': 'string'
        }
    }


class WordsModel(Schema):
    type = 'object'

    properties = {
        'msg': {
            'type': 'string'
        },
        'status': {
            'type': 'string'
        }
    }