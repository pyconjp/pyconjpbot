import json
import random

from slackbot.bot import respond_to, listen_to
from slackbot import settings
import slacker

from .plusplus_model import Plusplus

PLUS_MESSAGE = (
    'leveled up!',
    'レベルが上がりました!',
    'やったね',
    '(☝՞ਊ ՞)☝ウェーイ',
    )

MINUS_MESSAGE = (
    'leveled down.',
    'レベルが下がりました',
    'ドンマイ!',
    '(´・ω・｀)',
    )


def _get_user_name(user_id):
    """
    指定された Slack の user_id に対応する username を返す

    Slacker で users.list API を呼び出す
    - https://github.com/os/slacker
    - https://api.slack.com/methods/users.info
    """
    webapi = slacker.Slacker(settings.API_TOKEN)
    response = webapi.users.info(user_id)
    if response.body['ok']:
        return response.body['user']['name']
    else:
        return ''


def _update_count(message, target, plusplus):
    """
    指定ユーザーのカウンターを更新する
    """
    target = target.lower()
    plus, created = Plusplus.get_or_create(name=target, defaults={'counter': 0})

    if plusplus == '++':
        plus.counter += 1
        msg = random.choice(PLUS_MESSAGE)
    else:
        plus.counter -= 1
        msg = random.choice(MINUS_MESSAGE)
    plus.save()

    message.send('{} {} (通算: {})'.format(target, msg, plus.counter))


@listen_to(r'^<@(.+)>:?\s*(\++|-+)')
def mention_plusplus(message, user_id, plusplus):
    """
    mentionされたユーザーに対して ++ または -- する
    """
    if len(plusplus) != 2:
        return

    target = _get_user_name(user_id)
    _update_count(message, target, plusplus)


@listen_to(r'^(\w\S*[^\s:+-]):?\s*(\++|-+)')
def plusplus(message, target, plusplus):
    """
    指定された名前に対して ++ または -- する

    takanory++
    takanory:++
    takanory: ++
    日本語++
    takanory++ コメント
    takanory ++
    """
    if len(plusplus) != 2:
        return
    _update_count(message, target, plusplus)


@respond_to(r'^plusplus\s+(del|delete)\s+(\S+)')
def plusplus_delete(message, subcommand, name):
    """
    指定された名前を削除する
    カウントが10未満のもののみ削除する
    """

    try:
        plus = Plusplus.get(name=name)
    except Plusplus.DoesNotExist:
        message.send('`{}` という名前は登録されていません'.format(name))
        return

    if abs(plus.counter) > 10:
        message.send('`{}` のカウントが多いので削除を取り消しました(count: {})'.format(name, plus.counter))
        return

    plus.delete_instance()
    message.send('`{}` を削除しました'.format(name))


@respond_to(r'^plusplus\s+rename\s+(\S+)\s+(\S+)')
def plusplus_rename(message, old, new):
    """
    指定された old から new に名前を変更する
    """
    try:
        oldplus = Plusplus.get(name=old)
    except Plusplus.DoesNotExist:
        message.send('`{}` という名前は登録されていません'.format(old))
        return

    newplus, created = Plusplus.create_or_get(name=new, counter=oldplus.counter)
    if not created:
        # すでに存在している
        message.send('`{}` という名前はすでに登録されています'.format(new))
        return

    # 入れ替える
    oldplus.delete_instance()
    message.send('`{}` から `{}` に名前を変更しました(count: {})'.format(old, new, oldplus.counter))


@respond_to(r'^plusplus\s+merge\s+(\S+)\s+(\S+)')
def plusplus_merge(message, old, new):
    """
    指定された old と new を一つにまとめる
    """
    try:
        oldplus = Plusplus.get(name=old)
    except Plusplus.DoesNotExist:
        message.send('`{}` という名前は登録されていません'.format(old))
        return

    try:
        newplus = Plusplus.get(name=new)
    except Plusplus.DoesNotExist:
        message.send('`{}` という名前は登録されていません'.format(new))
        return

    oldcount = oldplus.counter
    newcount = newplus.counter

    # 値を統合する
    newplus.counter += oldplus.counter
    newplus.save()
    oldplus.delete_instance()

    message.send('`{}` を `{}` に統合しました(count: {} + {} = {})'.format(old, new, oldcount, newcount, newplus.counter))


@respond_to(r'^plusplus\s+search\s+(\S+)')
def plusplus_search(message, keyword):
    """
    指定されたキーワードを含む名前とカウントの一覧を返す
    """
    pattern = '%{}%'.format(keyword)
    pluses = Plusplus.select().where(Plusplus.name ** pattern)

    if len(pluses) == 0:
        message.send('`{}` を含む名前はありません'.format(keyword))
    else:
        pretext = '`{}` を含む名前とカウントの一覧です\n'.format(keyword)
        text = ''
        for plus in pluses:
            text += '- {}(count: {})\n'.format(plus.name, plus.counter)
        attachments = [{
            'pretext': pretext,
            'text': text,
            'mrkdwn_in': ['pretext', 'text'],
        }]
        message.send_webapi('', json.dumps(attachments))


@respond_to(r'^plusplus\s+help+')
def plusplus_help(message):
    """
    ヘルプメッセージを返す
    """
    message.send('''- `名前++`: 指定された名前に +1 カウントする
- `名前--`: 指定された名前に -1 カウントする
- `$pluplus search (キーワード)`: 名前にキーワードを含む一覧を返す
- `$pluplus delete (名前)`: カウントを削除する(カウント10未満のみ)
- `$pluplus rename (変更前) (変更後)`: カウントする名前を変更する
- `$pluplus merge (統合元) (統合先)`: 2つの名前のカウントを統合先の名前にまとめる
''')
