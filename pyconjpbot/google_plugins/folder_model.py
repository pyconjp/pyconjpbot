from peewee import *
import peewee

folder_db = SqliteDatabase('folder.db')

class Folder(Model):
    """
    Google Drive のフォルダーのパス情報とその Id を管理するモデル
    """
    path = CharField(primary_key=True)
    id = CharField()

    class Meta:
        database = folder_db
