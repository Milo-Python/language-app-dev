from flask import Flask, jsonify, request
from flask_expects_json import expects_json
from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.ddl import CreateTable
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
from flask_hashing import Hashing
import os
from flask import make_response, jsonify
from jsonschema import ValidationError
from applicationinsights.flask.ext import AppInsights

from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
    get_jwt,
    JWTManager
)

db = SQLAlchemy()
appinsights = AppInsights()

from .data import DataContext

data_context = DataContext(db)
DB_NAME = "database.db"
USER_LOGOUT = "User <id={}> successfully logged out."
BLOCKLIST = set()
INVALID_CREDENTIALS = "Invalid credentials!"

from .models import *


def authenticate(username, password):
    # user = User.query.filter_by(user_name=username).first()
    user = data_context.get_user_by_user_name(username=username)
    if user and check_password_hash(user.password, password):
        user.id = user.user_id
        return user


def identity(payload):
    user_id = payload['identity']
    user = data_context.get_user_by_id(user_id)
    if user:
        user.id = user_id
        return user


# class GamesWordsAssoc(Resource):
#     @jwt_required()
#     def get(self):
#         new_gwa_request = request.json
#         game_word_assoc = [{"game_word_id": new_gwa_request.game_word_id, "word_id": new_gwa_request.word_id,
#                             "game_id": new_gwa_request.game_id,
#                             "success_flag": new_gwa_request.success_flag} for new_gwa_request in
#                            GameWordAssoc.query.all()]
#         return jsonify(game_word_assoc)
#
#     @jwt_required()
#     def post(self):
#         new_gwa_request = request.json
#         word = Word.query.filter_by(word_name=new_gwa_request["word_name"]).first()
#         game = Game.query.filter_by(game_name=new_gwa_request["game_name"]).first()
#         game_word_assoc = GameWordAssoc(word_id=word.word_id, game_id=game.game_id,
#                                         success_flag=new_gwa_request["success_flag"])
#         db.session.add(game_word_assoc)
#         db.session.commit()
#         game_word_assoc = GameWordAssoc.query.filter_by(success_flag=new_gwa_request["success_flag"]).first()
#         return jsonify(id=game_word_assoc.game_word_id, msg="Game word association added", status=201)


class AllWords(Resource):
    @jwt_required()
    def get(self):
        words = [{"word_id": word.word_id, "word_name": word.word_name, "word_context": word.word_context} for word in
                 Word.query.all()]
        return jsonify(words)

    # schema = {
    #     "type": "object",
    #     "properties": {
    #         "word_name": {"type": "string", "minLength": 2, "maxLength": 50},
    #         "context": {"type": "string", "minLength": 2, "maxLength": 200},
    #         "language_name": {"type": "string", "minLength": 2, "maxLength": 50}
    #     },
    #     "required": ["word_name", "context", "language_name"]
    # }

#     @expects_json(schema)
#     @jwt_required()
#     def post(self):
#         new_word_request = request.json
#         language = Language.query.filter_by(language_name=new_word_request["language_name"]).first()
#         if not language:
#             return jsonify(mgs="language not found", code=404)
#
#         parent_id = new_word_request.get("parent_word_id", None)
#         if parent_id:
#             parent = Word.query.get(parent_id)
#             parent_id = parent.word_id if parent else None
#
#         word = Word(word_name=new_word_request["word_name"], parent_word_id=parent_id,
#                     language_id=language.language_id, context=new_word_request.get("context", None))
#         db.session.add(word)
#         db.session.commit()
#         word = Word.query.filter_by(word_name=new_word_request["word_name"]).first()
#         return jsonify(id=word.word_id, msg="Word added", status=201)
#
class LibrariesAll(Resource):
    @jwt_required()
    def get(self):
        libraries = [{"library_id": lib.library_id, "library_name": lib.library_name} for lib in
                 Library.query.all()]
        return jsonify(libraries)


class AddLib(Resource):

    schema = {
        "type" : "object",
        "properties" : {
            "library_name" : {"type" : "string", "minLength" : 2, "maxLength" : 50},
            "language_id_1": {"type" : "number"},
            "language_id_2": {"type": "number"}
        },
        "required" : ["library_name", "language_id_1", "language_id_2"]
    }

    @expects_json(schema)
    @jwt_required()
    def post(self):
        new_lib_request = request.json

        language_1 = Language.query.filter_by(language_id=new_lib_request["language_id_1"]).first()

        if not language_1:
            return make_response(jsonify(mgs="language 1 not found", code=404), 404)

        language_2 = Language.query.filter_by(language_id=new_lib_request["language_id_2"]).first()

        if not language_2:
            return make_response(jsonify(mgs="language 2 not found", code=404), 404)

        library = Library(library_name=new_lib_request["library_name"])
        db.session.add(library)
        db.session.commit()
        db.session.flush()

        insert_language_pair_query = f"""
        INSERT INTO translation VALUES ((SELECT $node_id FROM [Library] WHERE [library_id] = {library.library_id}), (SELECT $node_id FROM [Language] WHERE [language_id] = {language_1.language_id}), 'from'),
		   ((SELECT $node_id FROM [Library] WHERE [library_id] = {library.library_id}), (SELECT $node_id FROM [Language] WHERE [language_id] = {language_2.language_id}), 'to');"""

        db.engine.execute(insert_language_pair_query)

        return make_response(jsonify(library_id=library.library_id, library_name=library.library_name, msg="Library added", status=201),
                             201)


class AddWords(Resource):

    schema = {
        "type": "object",
        "properties": {
            "word_name_1": {"type": "string", "minLength": 2, "maxLength": 50},
            "word_context_1": {"type": "string", "minLength": 2, "maxLength": 200},
            "language_id_1": {"type": "number"},
            "word_name_2": {"type": "string", "minLength": 2, "maxLength": 50},
            "word_context_2": {"type": "string", "minLength": 2, "maxLength": 200},
            "language_id_2": {"type": "number"},
            "word_difficulty": {"type": "number", "minimum": 1, "maximum": 100}
                            },
        "required": ["word_name_1", "word_context_1", "language_id_1", "word_name_2", "word_context_2", "language_id_2", "word_difficulty"]
    }

    @expects_json(schema)
    @jwt_required()
    def post(self):

        new_word_request = request.json
        language_1 = Language.query.filter_by(language_id=new_word_request["language_id_1"]).first()

        if not language_1:
            return make_response(jsonify(mgs="language 1 not found", code=404), 404)

        language_2 = Language.query.filter_by(language_id=new_word_request["language_id_2"]).first()

        if not language_2:
            return make_response(jsonify(mgs="language 2 not found", code=404), 404)

        word_1 = Word(word_name=new_word_request["word_name_1"], word_context=new_word_request.get("word_context_1", None))
        db.session.add(word_1)

        word_2 = Word(word_name=new_word_request["word_name_2"],
                      word_context=new_word_request.get("word_context_2", None))
        db.session.add(word_2)

        db.session.commit()
        db.session.flush()
        insert_family_query = f"""INSERT INTO family VALUES ((SELECT $node_id FROM Word WHERE word_id = {word_1.word_id}), (SELECT $node_id FROM [Language] WHERE language_id = {language_1.language_id})),
	       ((SELECT $node_id FROM [Language] WHERE language_id = {language_1.language_id}), (SELECT $node_id FROM Word WHERE word_id = {word_1.word_id})),
	       ((SELECT $node_id FROM Word WHERE word_id = {word_2.word_id}), (SELECT $node_id FROM Language WHERE language_id = {language_2.language_id})),
		   ((SELECT $node_id FROM [Language] WHERE language_id = {language_2.language_id}), (SELECT $node_id FROM [Word] WHERE word_id = {word_2.word_id}));"""

        insert_pair_query = f"""INSERT INTO pairs VALUES ((SELECT $node_id FROM Word WHERE word_id = {word_1.word_id}), (SELECT $node_id FROM Word WHERE word_id = {word_2.word_id}), {new_word_request["word_difficulty"]}, 'translation'),
	       ((SELECT $node_id FROM Word WHERE word_id = {word_2.word_id}), (SELECT $node_id FROM Word WHERE word_id = {word_1.word_id}), {new_word_request["word_difficulty"]}, 'translation');"""

        db.engine.execute(insert_family_query)
        db.engine.execute(insert_pair_query)
        return make_response(jsonify(word_id_1=word_1.word_id, word_id_2=word_2.word_id, msg="Word added", status=201), 201)

class AddLanguages(Resource):

    schema = {
        "type": "object",
        "properties": {
            "language_code": {"type": "string", "minLength": 3, "maxLength": 3},
            "language_name": {"type": "string", "minLength": 3, "maxLength": 50}
                            },
        "required": ["language_code", "language_name"]
    }

    @expects_json(schema)
    @jwt_required()
    def post(self):

        new_language_request = request.json

        language = Language(language_code=new_language_request["language_code"], language_name=new_language_request["language_name"])
        db.session.add(language)

        db.session.commit()
        db.session.flush()

        # insert_language_query = f"""INSERT INTO language VALUES ('{language.language_code}', '{language.language_name}');"""
        # db.engine.execute(insert_language_query)
        return make_response(jsonify(language_id=language.language_id, language_name=language.language_name, msg="Language added", status=201), 201)


class UserLogout(Resource):
    @jwt_required()
    def post(self):
        jti = get_jwt()["jti"]  # jti is "JWT ID", a unique identifier for a JWT.
        user_id = get_jwt_identity()
        BLOCKLIST.add(jti)
        return jsonify(message=USER_LOGOUT.format(user_id))


class TokenRefresh(Resource):
    @jwt_required(refresh=True)
    def post(self):
        current_user = get_jwt_identity()
        new_token = create_access_token(identity=current_user, fresh=False)
        return {"access_token": new_token}, 200


class UserLogin(Resource):
    schema = {
        "type": "object",
        "properties": {
            "password": {"type": "string", "minLength": 2, "maxLength": 50},
            "email": {"type": "string", "minLength": 2, "maxLength": 50}
        },
        "required": ["email", "password"]
    }

    @expects_json(schema)
    def post(self):
        data = request.json
        user = User.query.filter_by(user_email=data["email"]).first()
        if user and hashing.check_value(user.user_password, data["password"], salt=user.user_password_salt):
            user.id = user.user_id
            access_token = create_access_token(identity=user.id, fresh=True)
            refresh_token = create_refresh_token(user.id)
            return jsonify(access_token=access_token, refresh_token=refresh_token)
        return {"message": INVALID_CREDENTIALS}, 401


migrate = Migrate()
hashing = Hashing()


def create_app():
    # https://flask-restful.readthedocs.io/en/latest/quickstart.html
    app = Flask(__name__)
    appinsights.init_app(app)

    @app.after_request
    def after_request(response):
        appinsights.flush()
        return response

    CORS(app)
    # app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_NAME}"
    # app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f"sqlite:///{DB_NAME}").replace("postgres", "postgresql")
    app.config[
        #'SQLALCHEMY_DATABASE_URI'] = "mssql+pyodbc://localhost\\SQLEXPRESS/TestDB2?driver=ODBC+Driver+17+for+SQL+Server"
        #'SQLALCHEMY_DATABASE_URI'] = "mssql+pyodbc://languageapp:Kanapa123@languageapp.database.windows.net/LanguageDB?driver=ODBC+Driver+17+for+SQL+Server"
        'SQLALCHEMY_DATABASE_URI'] = "mssql+pyodbc://admin-app-dev:chair!9Bag@language-app-dev-server.database.windows.net/LanguageAppDevDB?driver=ODBC+Driver+17+for+SQL+Server"

    app.config["SECRET_KEY"] = "123456789"
    api = Api(app=app)
    jwtmanager = JWTManager(app)
    from .routes import Words, Languages, Users, UserInfo, Echo, Scores, Games
    api.add_resource(AddWords, "/words/add")
    api.add_resource(AddLib, "/libraries/add")
    api.add_resource(AddLanguages, "/languages/add")
    api.add_resource(LibrariesAll, "/libraries")
    api.add_resource(Words, "/words/<int:id>")
    api.add_resource(AllWords, "/words")
    api.add_resource(Languages, "/languages")
    api.add_resource(Scores, "/scores")
    # api.add_resource(GamesWordsAssoc, "/games-words-assoc")
    api.add_resource(Games, "/games")
    api.add_resource(Users, "/users")
    api.add_resource(UserInfo, "/users/<int:id>")
    api.add_resource(Echo, "/echo")
    api.add_resource(UserLogout, "/logout")
    api.add_resource(TokenRefresh, "/refresh")
    api.add_resource(UserLogin, "/login")

    db.init_app(app)
    migrate.init_app(app=app, db=db)

    # jwt = JWT(app, authenticate, identity)

    @jwtmanager.token_in_blocklist_loader
    def check_if_token_in_blocklist(jwt_header, jwt_payload):
        return (
                jwt_payload["jti"] in BLOCKLIST
        )  # Here we blocklist particular JWTs that have been created in the past.

    hashing.init_app(app)
    data_context.set_hashing(hashing)

    @app.errorhandler(400)
    def bad_request(error):
        if isinstance(error.description, ValidationError):
            original_error = error.description
            return make_response(jsonify({'error': original_error.message}), 400)
        # handle other "Bad Request"-errors
        return error

    @jwtmanager.unauthorized_loader
    def unauthorized_callback(callback):
        return make_response(jsonify(msg="Invalid Token"), 401)

    @compiles(CreateTable)
    def create_as_node(create_table, compiler, **kw):
        if create_table.element.name in ["word", "language", "library", "user"]:
            compiler.post_create_table = lambda x: ' AS NODE'
        elif create_table.element.name in ["pairs", "family", "contains", "play", "use", "relation", "translation"]:
            compiler.post_create_table = lambda x: ' AS EDGE'
        return compiler.visit_create_table(create_table, **kw)

    return app
