import random
import json

from slackbot.bot import respond_to

from .term_model import Term, Response

# すでに存在するコマンドは登録できない
RESERVED = (
    'drive', 'manual', 'jira', 'wikipedia', 'translate',
    'weather', 'shuffle', 'help', 'choice', 'ping', 'version',
)

# コマンド一覧を初期化
commands = {term.command for term in Term.select()}

@respond_to('term\s+create\s+(\S+)')
def term_create(message, command):
    """
    指定された用語を追加する
    """
    # 用語は小文字に統一
    command = command.lower()
    if command in RESERVED:
        message.send('用語 `{}` は予約語なので登録できません'.format(command))
        return

    creator = message.body['user']
    term, created = Term.create_or_get(command=command, creator=creator)
    if created == False:
        # すでに登録してある用語は登録しない
        message.send('用語 `{}` はすでに登録されています'.format(command))

    else:
        msg = '用語 `{}` を作成しました。\n'.format(command)
        msg += '`${} add (レスポンス)` で用語のレスポンスを追加できます'.format(command)
        message.send(msg)
        # コマンド一覧に追加
        commands.add(command)

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
