from .models import User, Language #, Word, Score, Game
import string
from random import choice


def create_random_string(count):
    chars = string.ascii_lowercase + string.ascii_uppercase + string.digits
    text = "".join([choice(chars) for i in range(count)])
    return text


class DataContext:
    def __init__(self, db):
        self.db = db
        self.hashing = None

    def get_user_by_id(self, id):
        return User.query.get(id)

    def get_user_by_user_name(self, user_name):
        user = User.query.filter_by(user_name=user_name).first()
        return user

    def get_user_by_user_email(self, user_email):
        user = User.query.filter_by(user_email=user_email).first()
        return user

    def get_word_by_id(self, id):
        word = Word.query.get(id)
        return word

    def add_words(self, word1, language1, word2, language2):
        #wyszukaj slowo nr 1 (z jezykiem nr 1) jesli slowo nie istnieje to je utworz
        #wyszukaj slowo nr 2 (z jezykiem nr 1) jesli sowo nie jestnieje to je utworz
        #jesli przynajmniej jedno slowo ma word_assoc_id to drugie powinno miec to samo
        #w przeciwnym przypadku jesli zadne slowo nie ma word assoc to utworz nowy numer i wpisz go do obu rekordow
        #co w przypadku slowek rozlacznych?
        """
        kot 1 5
        cat 2 5

        assoc 5


        neko 3 6
        gato 4 6
        assoc 6

        neko
        cat
        assoc
        """

    def create_user(self, user_name, user_email, password):
        salt = create_random_string(64)
        user_password = self.hashing.hash_value(password, salt=salt)
        user = User(user_name=user_name, user_email=user_email, user_password=user_password, user_password_salt=salt)
        self.db.session.add(user)
        self.db.session.commit()
        self.db.session.refresh(user)
        return user

    def set_hashing(self, hashing):
        self.hashing = hashing

    def db_commit(self):
        self.db.session.commit()

    def word_delete(self, word):
        self.db.session.delete(word)
        self.db_commit()

    def get_all_languages(self):
        return Language.query.all()

    def add_language(self, language_code, language_name):
        language = Language(language_code=language_code,
                            language_name=language_name)
        self.db.session.add(language)
        self.db.session.commit()
        self.db.session.refresh(language)
        return language

    def get_all_scores(self):
        return Score.query.all()

    def get_score_by_score_name(self, score_name):
        score = Score.query.filter_by(user_name=score_name).first()
        return score

    def add_score(self, score_name, score_result, level_result):
        score = Score(score_name=score_name,
                      score_result=score_result,
                      level_result=level_result)
        self.db.session.add(score)
        self.db.session.commit()
        self.db.session.refresh(score)
        return score

    def add_game(self, user_id, score_id, game_name):
        game = Game(user_id=user_id, score_id=score_id, game_nam=game_name)
        self.db.session.add(game)
        self.db.session.commit()
        self.db.session.refresh(game)
        return game







