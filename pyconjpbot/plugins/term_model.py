import os.path
from datetime import datetime

from peewee import CharField, DateTimeField, ForeignKeyField, Model, SqliteDatabase

db = SqliteDatabase(os.path.join(os.path.dirname(__file__), "term.db"))


class BaseModel(Model):
    """
    ベースとなるモデル
    """

    class Meta:
        database = db


class Term(BaseModel):
    """
    用語を登録するモデル
    """

    command = CharField(unique=True)
    creator = CharField()
    created = DateTimeField(default=datetime.now())


class Response(BaseModel):
    """
    用語に対する応答を登録するモデル
    """

    term = ForeignKeyField(Term)
    text = CharField()
    creator = CharField()
    created = DateTimeField(default=datetime.now())


db.connect()
db.create_tables([Term, Response], safe=True)
