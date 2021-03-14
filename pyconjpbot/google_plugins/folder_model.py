import os.path

from peewee import *

folder_db = SqliteDatabase(os.path.join(os.path.dirname(__file__), "folder.db"))


class Folder(Model):
    """
    Google Drive のフォルダーのパス情報とその Id を管理するモデル
    """

    path = CharField(primary_key=True)
    id = CharField()

    class Meta:
        database = folder_db
