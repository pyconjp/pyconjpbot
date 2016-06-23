import random
import json

from slackbot.bot import respond_to

from .term_model import Term, Response

@respond_to('term\s+create\s+(\S+)')
def term_create(message, term):
    """
    指定された用語を追加する
    """
    # TODO: 予約語(jira等)は作成しない
    # 用語は小文字に統一
    term = term.lower()
    # TODO: すでに登録してある用語は登録しない
    message.send('用語 `{}` を作成しました'.format(term))

@respond_to('term\s+drop\s+(\S+)')
def term_drop(message, term):
    """
    指定された用語を消去する
    """
    # 用語は小文字に統一
    term = term.lower()
    # TODO: 指定された用語が存在しない場合
    message.send('用語 `{}` を消去しました'.format(term))

@respond_to('term\s+search\s+(\S+)')
def term_search(message, keyword):
    """
    現在使用可能な用語の一覧を返す
    """
    # TODO: attachmentsで返す
    message.send('`{}` を含む用語の一覧です'.format(keyword))

@respond_to('term\s+list')
def term_list(message):
    """
    現在使用可能な用語の一覧を返す
    """
    # TODO: attachmentsで返す
    message.send('用語の一覧です')

@respond_to('term\s+help')
def term_help(message):
    """
    term pluginのヘルプを返す
    """
    message.send('termコマンドのヘルプです')

#$(用語) add (レスポンス): 用語にレスポンスを追加する
#$(用語) del (レスポンス): 用語からレスポンスを削除する
#$(用語): 用語に登録してあるレスポンスをランダムに返す
