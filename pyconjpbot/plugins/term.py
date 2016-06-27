import random
import json

from slackbot.bot import respond_to

from .term_model import Term, Response

# すでに存在するコマンドは登録できない
RESERVED = (
    'drive', 'manual', 'jira', 'wikipedia', 'translate',
    'weather', 'shuffle', 'help', 'choice', 'ping', 'version',
    'term',
)

# コマンド一覧を初期化
commands = {term.command for term in Term.select()}

@respond_to('term\s+(create|add)\s+(\w+)')
def term_create(message, subcommand, command):
    """
    指定されたコマンドを生成する
    """
    # コマンドは小文字に統一
    command = command.lower()
    # 予約語の場合は実行しない
    if command in RESERVED:
        message.send('コマンド `${}` は予約語なので登録できません'.format(command))
        return

    creator = message.body['user']
    term, created = Term.create_or_get(command=command, creator=creator)
    if created == False:
        # すでに登録してあるコマンドは登録しない
        message.send('コマンド `${}` はすでに登録されています'.format(command))

    else:
        msg = 'コマンド `${}` を作成しました。\n'.format(command)
        msg += '`${} add (レスポンス)` でレスポンスを追加できます'.format(command)
        message.send(msg)

        # コマンド一覧に追加
        commands.add(command)

@respond_to('term\s+(drop|del|delete)\s+(\w+)')
def term_drop(message, subcommand, command):
    """
    指定されたコマンドを消去する
    """
    # コマンドは小文字に統一
    command = command.lower()
    # TODO: 指定された用語が存在しない場合
    message.send('コマンド `${}` を消去しました'.format(term))

@respond_to('term\s+search\s+(\w+)')
def term_search(message, keyword):
    """
    指定したキーワードを含む用語コマンドの一覧を返す
    """
    # TODO: 検索してattachmentsで返す
    command_list = ''
    for command in sorted(commands):
        if keyword in command:
            command_list += '`${}`, '.format(command)
    attachments = [{
        'pretext': '`{}` を含む用語コマンドの一覧です'.format(keyword),
        'text': command_list[:-2],
        'mrkdwn_in': ['pretext', 'text'],
    }]
    message.send_webapi('', json.dumps(attachments))

@respond_to('term\s+list')
def term_list(message):
    """
    現在使用可能な用語コマンドの一覧を返す
    """
    # {'foo', 'bar', 'baz'} -> '`$bar`, `$baz`, `$foo`'
    command_list = ', '.join(['`$' + c + '`' for c in sorted(commands)])

    attachments = [{
        'pretext': '用語コマンドの一覧です',
        'text': command_list,
        'mrkdwn_in': ["text"],
    }]
    message.send_webapi('', json.dumps(attachments))

@respond_to('term\s+help')
def term_help(message):
    """
    term pluginのヘルプを返す
    """
    message.send('termコマンドのヘルプです')

@respond_to('^(\w+)\s+(add)\s+(.*)')
def add_response(message, command, subcommand, text):
    """
    用語コマンドに応答を追加する
    """
    if command in RESERVED:
        return
    if command not in commands:
        message.send('コマンド `${}` は登録されていません'.format(command))
        return

    term = Term.get(command=command)
    creator = message.body['user']
    # 用語を登録数
    resp, created = Response.get_or_create(term=term, text=text, creator=creator)
    if created == False:
        message.send('コマンド `${}` に `${}` は登録済みです'.format(command, text))
        return
        

    message.send('コマンド `${}` に `{}` を追加しました'.format(command, text))

@respond_to('^(\w+)\s+(del|delete)\s+(.*)')
def add_response(message, command, subcommand, text):
    """
    用語コマンドから応答を削除する
    """
    if command in RESERVED:
        return
    if command not in commands:
        message.send('コマンド `${}` は登録されていません'.format(command))
        return

    term = Term.get(command=command)
    response = Response.get(term=term, text=text)
    response.delete_instance()

    message.send('コマンド `${}` から `{}` を削除した'.format(command, text))

@respond_to('^(\w+)$')
def return_response(message, command):
    """
    用語コマンドに登録されている応答をランダムに返す
    """
    if command in RESERVED:
        return
    if command not in commands:
        message.send('コマンド `${}` は登録されていません'.format(command))
        return

    response_set = Term.get(command=command).response_set
    if len(response_set) == 0:
        msg = 'コマンド `${}` には応答が登録されていません\n'.format(command)
        msg+= '`${} add (レスポンス)` で応答を登録してください'.format(command)
        message.send(msg)
    else:
        response = random.choice(response_set)
        message.send(response.text)
