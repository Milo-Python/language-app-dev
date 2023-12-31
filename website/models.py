from . import db
from sqlalchemy import func, UniqueConstraint


# flask db init
# flask db migrate
# flask db upgrade


class Word(db.Model):
    word_id = db.Column(db.Integer, primary_key=True)
    word_name = db.Column(db.String(50))
    word_context = db.Column(db.String(150))


class Language(db.Model):
    language_id = db.Column(db.Integer, primary_key=True)
    language_code = db.Column(db.String(3))
    language_name = db.Column(db.String(50))


class Library(db.Model):
    library_id = db.Column(db.Integer, primary_key=True)
    library_name = db.Column(db.String(50))
    library_create_date = db.Column(db.DateTime, default=func.now())


class Game(db.Model):
    game_id = db.Column(db.Integer, primary_key=True)
    open = db.Column(db.Integer)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)


class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(50))
    user_email = db.Column(db.String(50))
    user_password = db.Column(db.String(100))
    user_password_salt = db.Column(db.String(100))

class Role(db.Model):
    role_id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(50))
    role_description = db.Column(db.String(100))

class Have(db.Model):
    have_id = db.Column(db.Integer, primary_key=True)
    have_date = db.Column(db.DateTime)

class Pairs(db.Model):
    pair_id = db.Column(db.Integer, primary_key=True)
    pair_level = db.Column(db.Integer)
    pair_type = db.Column(db.String(100))


class Family(db.Model):
    family_id = db.Column(db.Integer, primary_key=True)
    pass


class Contains(db.Model):
    contains_id = db.Column(db.Integer, primary_key=True)
    pass


class Play(db.Model):
    play_id = db.Column(db.Integer, primary_key=True)
    play_date = db.Column(db.DateTime)


class Use(db.Model):
    use_id = db.Column(db.Integer, primary_key=True)
    use_date = db.Column(db.DateTime)


class Relation(db.Model):
    relation_id = db.Column(db.Integer, primary_key=True)
    relation_type = db.Column(db.String(100))


class Translation(db.Model):
    translation_id =  db.Column(db.Integer, primary_key=True)
    translation_type = db.Column(db.String(100))




#     word_id = db.Column(db.Integer, primary_key=True)
#     word_assoc_id = db.Column(db.Integer, db.ForeignKey("word_assoc.word_assoc_id"))
#     language_id = db.Column(db.Integer, db.ForeignKey("language.language_id"))
#     word_name = db.Column(db.String(50))
#     context = db.Column(db.String(150))
#     __table_args__ = (UniqueConstraint('word_name', 'language_id', name='_word_name_language_uc'), )
#
#
# class WordAssoc(db.Model):
#     word_assoc_id = db.Column(db.Integer, primary_key=True)
#     word_assoc_type_name = db.Column(db.String(100))
#
#
# class Language(db.Model):
#     language_id = db.Column(db.Integer, primary_key=True)
#     language_code = db.Column(db.String(3))
#     language_name = db.Column(db.String(50))
#     words = db.relationship("Word")


# class User(db.Model):
#     user_id = db.Column(db.Integer, primary_key=True)
#     user_name = db.Column(db.String(50), unique=True)
#     email = db.Column(db.String(50), unique=True)
#     password = db.Column(db.String(100))
#     password_salt = db.Column(db.String(100))
#    # info = {'as_node': True}


# class Game(db.Model):
#     game_id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey("user.user_id"))
#     score_id = db.Column(db.Integer, db.ForeignKey("score.score_id"))
#     game_words = db.relationship("GameWordAssoc")
#     game_name = db.Column(db.String(50))
#     game_date = db.Column(db.DateTime(timezone=True), default=func.now())
#
#
# class GameWordAssoc(db.Model):
#     game_word_id = db.Column(db.Integer, primary_key=True)
#     word_id = db.Column(db.Integer, db.ForeignKey("word.word_id"))
#     game_id = db.Column(db.Integer, db.ForeignKey("game.game_id"))
#     success_flag = db.Column(db.Boolean)
#
#
# class Score(db.Model):
#     score_id = db.Column(db.Integer, primary_key=True)
#     score_name = db.Column(db.String(50))
#     score_result = db.Column(db.Integer)
#     level_result = db.Column(db.Integer)
#


