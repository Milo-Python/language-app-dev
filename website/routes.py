from flask_expects_json import expects_json
from . import data_context, appinsights
from flask import jsonify, request
from flask import make_response
from flask import current_app as app
from flask_restful_swagger_3 import Api, Resource, swagger, Schema, get_swagger_blueprint
from .schemas import EchoModel, WordsModel
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
    get_jwt,
    JWTManager
)



class Echo(Resource):
    @swagger.reorder_with(EchoModel, description="Returns an echo message", summary="Get Echo")
    def get(self):
        # app.logger.debug('This is a debug log message')
        # app.logger.info('This is an information log message')
        # app.logger.warn('This is a warning log message')
        app.logger.error('This is an error message')
        # app.logger.critical('This is a critical message')
        return jsonify(status=200, msg="OK")


class UserInfo(Resource):
    @jwt_required()
    def get(self, id):
        user = data_context.get_user_by_id(id)
        if user:
            return jsonify(user_id=user.user_id,
                           user_name=user.user_name,
                           email=user.email)
        else:
            return jsonify(status=404, msg="User does not exits.")


class Users(Resource):
    email_pattern = """(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])"""

    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string",  "minLength": 2, "maxLength": 50 },
            "password": {"type" : "string" ,  "minLength": 2, "maxLength": 50},
            "email": {"type": "string",  "minLength": 2, "maxLength": 50, "pattern": email_pattern}
        },
        "required": ["email", "name", "password"]
    }

    @expects_json(schema)
    def post(self):
        new_user = request.json
        user = data_context.get_user_by_user_name(new_user["name"])
        email = data_context.get_user_by_user_email(new_user["email"])
        if user:
            return make_response(jsonify(msg="Name already exists!", status=400), 400)
        if email:
            return make_response(jsonify(msg="Email already exists!", status=400), 400)

        user = data_context.create_user(new_user["name"], new_user["email"], new_user["password"])

        return make_response(jsonify(id=user.user_id, msg="User added", status=201), 201)



class Words(Resource):
    @swagger.reorder_with(WordsModel, description="Returns an Words message", summary="Get Words")
    @jwt_required()
    def get(self, id):
        word = data_context.get_word_by_id(id)
        if word:
            return jsonify(word_id=word.word_id,
                           word_name=word.word_name)
        else:
            return jsonify(status=404, msg="Word does not exits.")


    def delete(self, id):
        #word = Word.query.get(id)
        word = data_context.get_word_by_id(id)
        if not word:
            return jsonify(status=404, msg="Word does not exits.")
        # db.session.delete(word)
        # db.session.commit()
        data_context.word_delete(word)
        return jsonify(status=200, msg="Word deleted!")


class Languages(Resource):
    @jwt_required()
    def get(self):
        names = ["language_id", "language_code", "language_name"]
        languages = []
        for lang in data_context.get_all_languages():
            one_language = {}
            for name in names:
                one_language[name] = getattr(lang, name)
            languages.append(one_language)

        return jsonify(languages)

    @jwt_required()
    def post(self):
        new_language_request = request.json
        language = data_context.add_language(language_code=new_language_request["language_code"],
                                             language_name=new_language_request["language_name"])
        return jsonify(id=language.language_id, msg="Language added", status=201)

class ChangeLanguages:
    @jwt_required()

    def put(self, id):
        #word = Word.query.get(id)
        word = data_context.get_word_by_id(id)
        if not word:
            return jsonify(status=404, msg="Word does not exits.")
        word.word_name = request.form["name"]
        #db.session.commit()
        data_context.db_commit()
        return jsonify(word_id=word.word_id,
                       word_name=word.word_name)


class Scores(Resource):
    @jwt_required()
    def get(self):
        names = ["score_id", "score_name", "score_result", "level_result"]
        scores = []
        for sc in data_context.get_all_scores():
            one_score = {}
            for name in names:
                one_score[name] = getattr(sc, name)
            scores.append(one_score)

        return jsonify(scores)

    @jwt_required()
    def post(self):
        new_score_request = request.json
        score = data_context.add_score(score_name=new_score_request["score_name"],
                                          score_result=new_score_request["score_result"],
                                          level_result=new_score_request["level_result"])
        return jsonify(id=score.score_id, msg="Score added", status=201)


class Games(Resource):
    @jwt_required()
    def post(self):
        new_game_request = request.json
        user = data_context.get_user_by_user_name(new_game_request.user_name)
        score = data_context.get_score_by_score_name(new_game_request.score_name)
        game = data_context.add_game(user_id=user.user_id,
                                     score_id=score.score_id,
                                     game_name=new_game_request["game_name"])
        return jsonify(id=game.game_id, msg="Game added", status=201)
