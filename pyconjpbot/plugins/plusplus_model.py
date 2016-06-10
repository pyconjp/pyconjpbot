import os.path

from peewee import *

db = SqliteDatabase(os.path.join(os.path.dirname(__file__), 'plusplus.db'))

class Plusplus(Model):
    """
    plusplusの状況を保存するモデル
    """
    name = CharField(primary_key=True)
    value = IntegerField()

    class Meta:
        database = db
