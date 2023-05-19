from flask import Flask, jsonify, request
from flask_expects_json import expects_json
from flask_marshmallow import Marshmallow
from flask_restful_swagger_3 import Api, Resource, swagger, Schema, get_swagger_blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import column, text
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.ddl import CreateTable
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
from flask_hashing import Hashing
from flask import make_response, jsonify
from jsonschema import ValidationError
from applicationinsights.flask.ext import AppInsights

import json

from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
    get_jwt,
    JWTManager
)


db = SQLAlchemy()
ma = Marshmallow()
appinsights = AppInsights()

from .data import DataContext

data_context = DataContext(db)
DB_NAME = "database.db"
USER_LOGOUT = "User <id={}> successfully logged out."
BLOCKLIST = set()
INVALID_CREDENTIALS = "Invalid credentials!"

from .models import *


class LibrarySchema(ma.Schema):
    class Meta:
        fields = (
            "library_id", "library_name")


library_schemas = LibrarySchema(many=True)


class WordSchema(ma.Schema):
    class Meta:
        fields = (
            "word_id", "word_name", "word_context")


word_schemas = WordSchema(many=True)


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


class AllWords(Resource):
    # @jwt_required()
    # def get(self):
    #     words = [{"word_id": word.word_id, "word_name": word.word_name, "word_context": word.word_context} for word in
    #              Word.query.all()]
    #     return jsonify(words)

    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()

        columns = ["word_id", "word_name", "word_context"]
        query = f"""SELECT {', '.join(columns)} FROM [user], [use], [library], [contains] ,[word] WHERE MATCH([user]-([use])->[library]-([contains])->[word]) AND [user].user_id = :user_id;"""

        query_result = (db.session.query(*list(map(column, columns)))
                        .from_statement(text(query))
                        .params(user_id=user_id).all())
        return word_schemas.dump(query_result)


class LibrariesAll(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()

        query = """SELECT library_id, library_name FROM [user], [use], [library] WHERE MATCH([user]-([use])->[library]) AND [user].user_id = :user_id;"""

        query_result = (db.session.query(column("library_id"), column("library_name"))
                        .from_statement(text(query))
                        .params(user_id=user_id).all())
        return library_schemas.dump(query_result)


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
        user_id = get_jwt_identity()
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

        insert_user_query = f"""INSERT INTO [dbo].[use] VALUES ((SELECT $node_id FROM [dbo].[user] WHERE user_id = {user_id}), (SELECT $node_id FROM library WHERE library_id = {library.library_id}), GETDATE());"""
        db.engine.execute(insert_language_pair_query)
        db.engine.execute(insert_user_query)

        return make_response(jsonify(library_id=library.library_id, library_name=library.library_name, msg="Library added", status=201),
                             201)

class ChangeLib(Resource):
    schema = {
        "type": "object",
        "properties": {
            "library_name": {"type": "string", "minLength": 2, "maxLength": 50}
        },
        "required": ["library_name"]
    }

    @expects_json(schema)
    @jwt_required()
    def put(self, library_id):
        user_id = get_jwt_identity()
        new_lib_request = request.json

        library = Library.query.filter_by(library_id=library_id).first()

        if not library:
            return make_response(jsonify(mgs="library not found", code=404), 404)

        library.library_name = new_lib_request["library_name"]
        db.session.commit()
        db.session.flush()

        return make_response(
            jsonify(library_id=library.library_id, library_name=library.library_name, msg="Library changed", status=201),
            201)

class DeleteLib(Resource):
    @jwt_required()
    def delete(self, library_id):
        # user_id = get_jwt_identity()

        library = Library.query.filter_by(library_id=library_id).first()

        if not library:
            return make_response(jsonify(mgs="library not found", code=404), 404)

        select_use_id = f"""select [use].use_id FROM [dbo].[library] , [dbo].[use] , [dbo].[user] WHERE MATCH ([user]-([use])->[library]) AND [library].library_id = {library_id}"""
        use_id = db.engine.execute(select_use_id).fetchone()[0]
        delete_use_id = f"""delete from dbo.[use] where use_id = {use_id}"""
        db.engine.execute(delete_use_id)
        delete_library_id = f"""delete from dbo.[library] where library_id = {library_id}"""
        db.engine.execute(delete_library_id)

        # library.delete()
        db.session.commit()
        db.session.flush()


        return make_response(
            jsonify(library_id=library_id, msg="Library deleted", status=201), 201)


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
            "word_difficulty": {"type": "number", "minimum": 1, "maximum": 100},
            "library_id": {"type": "number"}
                            },
        "required": ["word_name_1", "word_context_1", "language_id_1", "word_name_2", "word_context_2", "language_id_2", "word_difficulty", "library_id"]
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

        library = Library.query.filter_by(library_id=new_word_request["library_id"]).first()

        if not library:
            return make_response(jsonify(mgs=f"library not found: {new_word_request['library_id']}", code=404), 404)
        

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

        insert_contains_query_1 = f"""INSERT INTO [dbo].[contains] VALUES ((SELECT $node_id FROM library WHERE library_id = {library.library_id}), (SELECT $node_id FROM word WHERE word_id = {word_1.word_id}));"""
        insert_contains_query_2 = f"""INSERT INTO [dbo].[contains] VALUES ((SELECT $node_id FROM library WHERE library_id = {library.library_id}), (SELECT $node_id FROM word WHERE word_id = {word_2.word_id}));"""

        db.engine.execute(insert_family_query)
        db.engine.execute(insert_pair_query)
        db.engine.execute(insert_contains_query_1)
        db.engine.execute(insert_contains_query_2)
        return make_response(jsonify(word_id_1=word_1.word_id, word_id_2=word_2.word_id, msg="Word added", status=201), 201)


class ChangeWords(Resource):
    schema = {
        "type": "object",
        "properties": {
            "word_name": {"type": "string", "minLength": 2, "maxLength": 50},
            "word_context": {"type": "string", "minLength": 2, "maxLength": 200}
        },
        "required": ["word_name", "word_context"]
    }

    @expects_json(schema)
    @jwt_required()
    def put(self, word_id):
        user_id = get_jwt_identity()
        new_word_request = request.json

        word = Word.query.filter_by(word_id=word_id).first()

        if not word:
            return make_response(jsonify(mgs="word not found", code=404), 404)

        word.word_name = new_word_request["word_name"]
        word.word_context = new_word_request["word_context"]
        db.session.commit()
        db.session.flush()

        return make_response(
            jsonify(word_id=word.word_id, word_name=word.word_name, word_context=word.word_context, msg="word changed",
                    status=201),
            201)

class DeleteWords(Resource):
    @jwt_required()
    def delete(self, word_id):

        word = Word.query.filter_by(word_id=word_id).first()

        if not word:
            return make_response(jsonify(mgs="word not found", code=404), 404)

        select_contains_id_1 = f"""SELECT [dbo].[contains].[contains_id] FROM [dbo].[library] , [dbo].[use] , [dbo].[user] , [dbo].[contains], [dbo].[word] WHERE MATCH ([user]-([use])->[library]-([contains])->[word]) AND [word].word_id = {word_id}"""
        contains_id_1 = db.engine.execute(select_contains_id_1).fetchone()[0]
        select_contains_id_2 = f"""SELECT [dbo].[contains].[contains_id] FROM [dbo].[library] , [dbo].[use] , [dbo].[user] , [dbo].[contains], [dbo].[word] WHERE MATCH ([user]-([use])->[library]-([contains])->[word]) AND [word].word_id in (select word_2.word_id FROM [dbo].[pairs] , dbo.[word] as word_1, dbo.[word] as word_2 WHERE MATCH (word_1-([pairs])->word_2) AND word_1.word_id = {word_id})"""
        contains_id_2 = db.engine.execute(select_contains_id_2).fetchone()[0]
        select_word_id_2 = f"""SELECT word_2.word_id FROM [dbo].[pairs], dbo.[word] as word_1, dbo.[word] as word_2 WHERE MATCH(word_1 - ([pairs])->word_2) AND word_1.word_id = {word_id}"""
        word_id_2 = db.engine.execute(select_word_id_2).fetchone()[0]
        select_pair_id_1 = f"""SELECT [dbo].[pairs].pair_id FROM [dbo].[pairs], dbo.[word] as word_1, dbo.[word] as word_2 WHERE MATCH(word_1 - ([pairs])->word_2) AND word_1.word_id = {word_id}"""
        pair_id_1 = db.engine.execute(select_pair_id_1).fetchone()[0]
        select_pair_id_2 = f"""SELECT [dbo].[pairs].pair_id FROM [dbo].[pairs], dbo.[word] as word_1, dbo.[word] as word_2 WHERE MATCH(word_1 - ([pairs])->word_2) AND word_1.word_id = {word_id_2}"""
        pair_id_2 = db.engine.execute(select_pair_id_2).fetchone()[0]

        delete_contains_id_1 = f"""delete from [dbo].[contains] where contains_id = {contains_id_1}"""
        db.engine.execute(delete_contains_id_1)
        delete_contains_id_2 = f"""delete from [dbo].[contains] where contains_id = {contains_id_2}"""
        db.engine.execute(delete_contains_id_2)
        delete_pair_id_1 = f"""delete from [dbo].[pairs] where pair_id = {pair_id_1}"""
        db.engine.execute(delete_pair_id_1)
        delete_pair_id_2 = f"""delete from [dbo].[pairs] where pair_id = {pair_id_2}"""
        db.engine.execute(delete_pair_id_2)
        delete_word_id_1 = f"""delete from [dbo].[word] where word_id = {word_id}"""
        db.engine.execute(delete_word_id_1)
        delete_word_id_2 = f"""delete from [dbo].[word] where word_id = {word_id_2}"""
        db.engine.execute(delete_word_id_2)

        db.session.commit()
        db.session.flush()

        return make_response(
            jsonify(word_id=word_id, msg="Word deleted", status=201), 201)

class ChangeLanguages(Resource):
    schema = {
        "type": "object",
        "properties": {
            "language_code": {"type": "string", "minLength": 2, "maxLength": 50},
            "language_name": {"type": "string", "minLength": 2, "maxLength": 200}
        },
        "required": ["language_code", "language_name"]
    }

    @expects_json(schema)
    @jwt_required()
    def put(self, language_id):
        # user_id = get_jwt_identity()
        new_language_request = request.json

        language = Language.query.filter_by(language_id=language_id).first()

        if not language:
            return make_response(jsonify(mgs="language not found", code=404), 404)

        language.language_code = new_language_request["language_code"]
        language.language_name = new_language_request["language_name"]
        db.session.commit()
        db.session.flush()

        return make_response(
            jsonify(language_id=language.language_id, language_code=language.language_code, language_name=language.language_name, msg="language changed",
                    status=201),
            201)

class ChangeUsers(Resource):
    schema = {
        "type": "object",
        "properties": {
            "user_name": {"type": "string", "minLength": 2, "maxLength": 200}
        },
        "required": ["user_name"]
    }

    @expects_json(schema)
    @jwt_required()
    def put(self, user_id):
        new_user_request = request.json

        user = User.query.filter_by(user_id=user_id).first()

        if not user:
            return make_response(jsonify(mgs="user not found", code=404), 404)

        user.user_name = new_user_request["user_name"]
        db.session.commit()
        db.session.flush()

        return make_response(
            jsonify(user_id=user.user_id,
                    user_name=user.user_name, msg="user changed",
                    status=201),
            201)


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
    @swagger.tags(["language"])
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
    app.config.from_file("config.json", load=json.load)
    appinsights.init_app(app)
    ma.init_app(app)

    @app.after_request
    def after_request(response):
        appinsights.flush()
        return response

    CORS(app)

    api = Api(app=app, add_api_spec_resource=True, swagger_prefix_url="/api/doc")
    jwtmanager = JWTManager(app)
    from .routes import Words, Languages, Users, UserInfo, Echo, Scores, Games
    api.add_resource(AddWords, "/words/add")
    api.add_resource(DeleteWords, "/words/delete/<int:word_id>")
    api.add_resource(AddLib, "/libraries/add")
    api.add_resource(ChangeLib, "/libraries/change/<int:library_id>")
    api.add_resource(DeleteLib, "/libraries/delete/<int:library_id>")
    api.add_resource(AddLanguages, "/languages/add")
    api.add_resource(LibrariesAll, "/libraries")
    api.add_resource(Words, "/words/<int:id>")
    api.add_resource(ChangeWords, "/words/change/<int:word_id>")
    api.add_resource(AllWords, "/words")
    api.add_resource(Languages, "/languages")
    api.add_resource(ChangeLanguages, "/languages/change/<int:language_id>")
    api.add_resource(Scores, "/scores")
    # api.add_resource(GamesWordsAssoc, "/games-words-assoc")
    api.add_resource(Games, "/games")
    api.add_resource(Users, "/users")
    api.add_resource(UserInfo, "/users/<int:id>")
    api.add_resource(ChangeUsers, "/users/change/<int:user_id>")
    api.add_resource(Echo, "/echo")
    api.add_resource(UserLogout, "/logout")
    api.add_resource(TokenRefresh, "/refresh")
    api.add_resource(UserLogin, "/login")

    db.init_app(app)
    migrate.init_app(app=app, db=db)

    SWAGGER_URL = '/api/doc'  # URL for exposing Swagger UI (without trailing '/')
    API_URL = 'swagger.json'  # Our API url (can of course be a local resource)

    swagger_blueprint = get_swagger_blueprint(
        api.open_api_object,
        swagger_prefix_url=SWAGGER_URL,
        swagger_url=API_URL)

    app.register_blueprint(swagger_blueprint)

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