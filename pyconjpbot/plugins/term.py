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

        # コマンド一覧の set に追加
        commands.add(command)

@respond_to('term\s+(drop|del|delete)\s+(\w+)')
def term_drop(message, subcommand, command):
    """
    指定されたコマンドを消去する
    """
    # コマンドは小文字に統一
    command = command.lower()

    # コマンドの存在チェック
    if _available_command(message, command) == False:
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
        list_text = ', '.join(['`{}`'.format(x) for x in data])
    attachments = [{
        'pretext': pretext,
        'text': list_text,
        'mrkdwn_in': ['pretext', 'text'],
    }]
    return json.dumps(attachments)
    
        
@respond_to('term\s+search\s+(\w+)')
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

@respond_to('term\s+list')
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

@respond_to('^(\w+)\s+(add)\s+(.*)')
def add_response(message, command, subcommand, text):
    """
    用語コマンドに応答を追加する
    """
    if _available_command(message, command) == False:
        return
    
    term = Term.get(command=command)
    creator = message.body['user']
    # 用語を登録する
    resp, created = Response.get_or_create(term=term, text=text, creator=creator)
    if created == False:
        message.send('コマンド `${}` に `${}` は登録済みです'.format(command, text))
        return
        

    message.send('コマンド `${}` に `{}` を追加しました'.format(command, text))

@respond_to('^(\w+)\s+(del|delete)\s+(.*)')
def del_response(message, command, subcommand, text):
    """
    用語コマンドから応答を削除する
    """
    if _available_command(message, command) == False:
        return
    
    term = Term.get(command=command)
    response = Response.get(term=term, text=text)
    response.delete_instance()

    message.send('コマンド `${}` から `{}` を削除しました'.format(command, text))

@respond_to('^(\w+)$')
def return_response(message, command):
    """
    用語コマンドに登録されている応答をランダムに返す
    """
    if _available_command(message, command) == False:
        return
    
    response_set = Term.get(command=command).response_set
    if len(response_set) == 0:
        msg = 'コマンド `${}` には応答が登録されていません\n'.format(command)
        msg+= '`${} add (レスポンス)` で応答を登録してください'.format(command)
        message.send(msg)
    else:
        response = random.choice(response_set)
        message.send(response.text)

@respond_to('^(\w+)\s+list')
def get_responses(message, command):
    """
    用語コマンドに登録されている応答の一覧を返す
    """
    if _available_command(message, command) == False:
        return

    response_set = Term.get(command=command).response_set
    if len(response_set) == 0:
        msg = 'コマンド `${}` には応答が登録されていません\n'.format(command)
        msg+= '`${} add (レスポンス)` で応答を登録してください'.format(command)
        message.send(msg)
    else:
        pretext = 'コマンド `${}` の応答一覧です\n'.format(command)
        data = [x.text for x in response_set]
        attachments = _create_attachments_for_list(pretext, data, False)
        message.send_webapi('', attachments)

@respond_to('term\s+help')
def term_help(message):
    """
    term pluginのヘルプを返す
    """
    message.send('''- `$term create (用語)`: 用語コマンドを作成する
- `$term search (キーワード)`: キーワードを含む用語コマンドの一覧を返す
- `$term list`: 用語コマンドの一覧を返す
- `$(用語) add (応答)`: 用語コマンドに応答を追加する
- `$(用語) del (応答)`: 用語コマンドから応答を削除する
- `$(用語)`: 登録してある応答をランダムに返す

```

Takanori Suzuki [18:44]  $term create 酒
BOT [18:44]  コマンド `$酒` を作成しました。
`$酒 add (レスポンス)` でレスポンスを追加できます
Takanori Suzuki [18:44]  $酒 add ビール
BOT [18:45]  コマンド `$酒` に `ビール` を追加しました
Takanori Suzuki [18:45]  $酒 add ワイン
BOT [18:45]  コマンド `$酒` に `ワイン` を追加しました
Takanori Suzuki [18:45]  $酒
BOT [18:45]  
ビール
```
''')

