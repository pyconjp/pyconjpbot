import random
import json
import re

from slackbot.bot import respond_to

from .term_model import Term, Response

# すでに存在するコマンドは無視する
RESERVED = (
    'drive', 'manual', 'jira', 'wikipedia', 'plusplus',
    'translate', '翻訳',
    'weather', '天気',
    'term',
    'shuffle', 'help', 'choice', 'ping', 'version', 'random',
)

# コマンド一覧を初期化
commands = {term.command for term in Term.select()}


@respond_to('^term\s+(create|add)\s+(\w+)')
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
    if not created:
        # すでに登録してあるコマンドは登録しない
        message.send('コマンド `${}` はすでに登録されています'.format(command))

    else:
        msg = 'コマンド `${}` を作成しました。\n'.format(command)
        msg += '`${} add (レスポンス)` でレスポンスを追加できます'.format(command)
        message.send(msg)

        # コマンド一覧の set に追加
        commands.add(command)


@respond_to('^term\s+(drop|del|delete)\s+(\w+)')
def term_drop(message, subcommand, command):
    """
    指定されたコマンドを消去する
    """
    # コマンドは小文字に統一
    command = command.lower()

    # コマンドの存在チェック
    if not _available_command(message, command):
        return

    # 用語コマンドと応答をまとめて削除
    term = Term.get(command=command)
    term.delete_instance(recursive=False)
    term.save()

    # コマンド一覧の set から削除
    commands.remove(command)
    message.send('コマンド `${}` を消去しました'.format(command))


def _create_attachments_for_list(pretext, data, command=True):
    """
    指定されたリストの一覧を message.send_webapi で送信するための
    attachments を生成する
    """
    if command:
        # ['foo', 'bar', 'baz'] -> '`$far`, `$bar`, `$baz`'
        list_text = ', '.join(['`${}`'.format(x) for x in data])
    else:
        list_text = '\n'.join([x for x in data])
    attachments = [{
        'pretext': pretext,
        'text': list_text,
        'mrkdwn_in': ['pretext', 'text'],
    }]
    return json.dumps(attachments)


@respond_to('^term\s+search\s+(\w+)')
def term_search(message, keyword):
    """
    指定したキーワードを含む用語コマンドの一覧を返す
    """
    pretext = '`{}` を含む用語コマンドの一覧です'.format(keyword)
    data = []
    for command in sorted(commands):
        if keyword in command:
            data.append(command)
    attachments = _create_attachments_for_list(pretext, data)
    message.send_webapi('', attachments)


@respond_to('^term\s+list')
def term_list(message):
    """
    現在使用可能な用語コマンドの一覧を返す
    """
    pretext = '用語コマンドの一覧です'
    attachments = _create_attachments_for_list(pretext, sorted(commands))
    message.send_webapi('', attachments)


def _available_command(message, command):
    """
    指定されたコマンドが有効化どうかを返す
    """
    result = True

    if command in RESERVED:
        result = False
    elif command not in commands:
        message.send('コマンド `${}` は登録されていません'.format(command))
        result = False

    return result


def _send_markdown_text(message, text):
    """
    指定されたtextをmarkdown形式で送信する
    """
    import pdb
    pdb.set_trace()
    attachments = [{
        'pretext': text,
        'mrkdwn_in': ['pretext'],
    }]
    message.send_webapi('', json.dumps(attachments))


@respond_to('^(\w+)\s+(add)\s+(.*)', re.DOTALL)
def add_response(message, command, subcommand, text):
    """
    用語コマンドに応答を追加する
    """
    if not _available_command(message, command):
        return

    term = Term.get(command=command)
    creator = message.body['user']
    # 用語を登録する
    resp, created = Response.get_or_create(term=term, text=text, creator=creator)
    if not created:
        message.send('コマンド `${}` に「{}」は登録済みです'.format(command, text))
        return

    text = 'コマンド `${}` に「{}」を追加しました'.format(command, text)
    _send_markdown_text(message, text)


@respond_to('^(\w+)\s+(del|delete)\s+(.*)', re.DOTALL)
def del_response(message, command, subcommand, text):
    """
    用語コマンドから応答を削除する
    """
    if not _available_command(message, command):
        return

    term = Term.get(command=command)
    try:
        response = Response.get(term=term, text=text)
    except Response.DoesNotExist:
        text = 'コマンド `${}` に指定された応答は登録されていません'.format(command)
        message.send(text)
        return

    response.delete_instance()

    text = 'コマンド `${}` から「{}」を削除しました'.format(command, text)
    _send_markdown_text(message, text)


@respond_to('^(\w+)$')
def return_response(message, command):
    """
    用語コマンドに登録されている応答をランダムに返す
    """
    if not _available_command(message, command):
        return

    response_set = Term.get(command=command).response_set
    if len(response_set) == 0:
        msg = 'コマンド `${}` には応答が登録されていません\n'.format(command)
        msg += '`${} add (レスポンス)` で応答を登録してください'.format(command)
        message.send(msg)
    else:
        response = random.choice(response_set)
        _send_markdown_text(message, response.text)


@respond_to('^(\w+)\s+search\s+(\w+)')
def search_responses(message, command, keyword):
    """
    用語コマンドに登録されている応答のうち、キーワードにマッチするものを返す
    """
    if not _available_command(message, command):
        return

    term = Term.get(command=command)
    pat = '%{}%'.format(keyword)
    responses = Response.select().where(term == term, Response.text ** pat)

    if len(responses) == 0:
        message.send('コマンド `${}` に `{}` を含む応答はありません'.format(command, keyword))
    else:
        pretext = 'コマンド `${}` の `{}` を含む応答は {} 件あります\n'.format(command, keyword, len(responses))
        data = [x.text for x in responses]
        attachments = _create_attachments_for_list(pretext, data, False)
        message.send_webapi('', attachments)


@respond_to('^(\w+)\s+list')
def get_responses(message, command):
    """
    用語コマンドに登録されている応答の一覧を返す
    """
    if not _available_command(message, command):
        return

    response_set = Term.get(command=command).response_set
    if len(response_set) == 0:
        msg = 'コマンド `${}` には応答が登録されていません\n'.format(command)
        msg += '`${} add (レスポンス)` で応答を登録してください'.format(command)
        message.send(msg)
    else:
        pretext = 'コマンド `${}` の応答は {} 件あります\n'.format(command, len(response_set))
        data = [x.text for x in response_set]
        attachments = _create_attachments_for_list(pretext, data, False)
        message.send_webapi('', attachments)


@respond_to('term\s+help')
def term_help(message):
    """
    term pluginのヘルプを返す
    """
    message.send('''- `$term create (用語)`: 用語コマンドを作成する
- `$term drop (用語)`: 用語コマンドを消去する
- `$term search (キーワード)`: キーワードを含む用語コマンドの一覧を返す
- `$term list`: 用語コマンドの一覧を返す

- `$(用語)`: 用語コマンドに登録してある応答からランダムに一つ返す
- `$(用語) add (応答)`: 用語コマンドに応答を追加する
- `$(用語) del (応答)`: 用語コマンドから応答を削除する
- `$(用語) list`: 用語コマンドの応答一覧を返す
- `$(用語) search (キーワード)`: 用語コマンドのうちキーワードを含む応答一覧を返す
```
> $term create 酒
コマンド `$酒` を作成しました。
`$酒 add (レスポンス)` でレスポンスを追加できます
> $酒 add ビール
コマンド `$酒` に `ビール` を追加しました
> $酒 add ワイン
コマンド `$酒` に `ワイン` を追加しました
> $酒
ビール
```
''')
