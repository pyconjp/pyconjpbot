import os.path

from peewee import *  # NOQA

db = SqliteDatabase(os.path.join(os.path.dirname(__file__), 'plusplus.db'))


class Plusplus(Model):
    """
    plusplusの状況を保存するモデル
    """
    name = CharField(primary_key=True)
    counter = IntegerField(default=0)

    class Meta:
        database = db


db.connect()
db.create_tables([Plusplus], safe=True)
