import calendar
from datetime import date
import random

from slackbot.bot import respond_to
from slackbot import settings
import slacker
import git

from ..botmessage import botsend, botreply, botwebapi


@respond_to('^help$')
def help(message):
    """
    helpページのURLを返す
    """
    botsend(message, 'ヘルプはこちら→ https://github.com/pyconjp/pyconjpbot#commands')


@respond_to('^shuffle\s+(.*)')
def shuffle(message, words):
    """
    指定したキーワードをシャッフルして返す
    """
    words = words.split()
    if len(words) == 1:
        botsend(message, 'キーワードを複数指定してください\n`$shuffle word1 word2...`')
    else:
        random.shuffle(words)
        botsend(message, ' '.join(words))


@respond_to('^choice\s+(.*)')
def choice(message, words):
    """
    指定したキーワードから一つを選んで返す
    """
    words = words.split()
    if len(words) == 1:
        botsend(message, 'キーワードを複数指定してください\n`$choice word1 word2...`')
    else:
        botsend(message, random.choice(words))


@respond_to('^ping$')
def ping(message):
    """
    pingに対してpongで応答する
    """
    botreply(message, 'pong')


@respond_to('^version$')
def version(message):
    """
    バージョン情報を返す
    """
    obj = git.Repo('').head.object
    url = "https://github.com/pyconjp/pyconjpbot/commit/{}".format(obj.hexsha)
    text = "<{}|{}> {} - {}({})".format(
        url, obj.hexsha[:6], obj.summary,
        obj.committer.name, obj.committed_datetime)
    attachments = [{
        'pretext': text,
    }]
    botwebapi(message, attachments)


@respond_to('^random$')
@respond_to('^random\s+(active|help)$')
def random_command(message, subcommand=None):
    """
    チャンネルにいるメンバーからランダムに一人を選んで返す

    - https://github.com/os/slacker
    - https://api.slack.com/methods/channels.info
    - https://api.slack.com/methods/users.getPresence
    - https://api.slack.com/methods/users.info
    """

    if subcommand == 'help':
        botsend(message, '''- `$random`: チャンネルにいるメンバーからランダムに一人を選ぶ
- `$random active`: チャンネルにいるactiveなメンバーからランダムに一人を選ぶ
''')
        return

    # チャンネルのメンバー一覧を取得
    channel = message.body['channel']
    webapi = slacker.Slacker(settings.API_TOKEN)
    cinfo = webapi.channels.info(channel)
    members = cinfo.body['channel']['members']

    # bot の id は除く
    bot_id = message._client.login_data['self']['id']
    members.remove(bot_id)

    member_id = None
    while not member_id:
        # メンバー一覧からランダムに選んで返す
        member_id = random.choice(members)
        if subcommand == 'active':
            # active が指定されている場合は presence を確認する
            presence = webapi.users.get_presence(member_id)
            if presence.body['presence'] == 'away':
                members.remove(member_id)
                member_id = None

    user_info = webapi.users.info(member_id)
    name = user_info.body['user']['name']
    botsend(message, '{} さん、君に決めた！'.format(name))


@respond_to('^cal$')
@respond_to('^cal\s+(\d+)$')
@respond_to('^cal\s+(\d+)\s+(\d+)$')
def cal_command(message, month=None, year=None):
    """
    一ヶ月のカレンダーを返す
    """
    today = date.today()
    month = int(month) if month else today.month
    year = int(year) if year else today.year

    cal = calendar.TextCalendar(firstweekday=calendar.SUNDAY)
    try:
        botsend(message, '```{}```'.format(cal.formatmonth(year, month)))
    except IndexError:
        # 数字が範囲外の場合は無視する
        pass


@respond_to('^cal\s+help$')
def cal_help(message):
    """
    cal コマンドのヘルプを返す
    """
    botsend(message, '''- `$cal`: 今月のカレンダーを返す
- `$cal 9`: 今年の指定された月のカレンダーを返す
- `$cal 9 2016`: 指定された年月のカレンダーを返す
''')


@respond_to('^members$')
@respond_to('^members\s+(all|bot|help)$')
def members_command(message, subcommand=None):
    """
    チャンネルにいるメンバーの一覧を返す

    - https://github.com/os/slacker
    - https://api.slack.com/methods/channels.info
    - https://api.slack.com/methods/users.getPresence
    - https://api.slack.com/methods/users.info
    """

    if subcommand == 'help':
        botsend(message, '''- `$members`: チャンネルにいる通常のメンバーの一覧を返す
- `$members all`:チャンネルにいる全てのメンバーの一覧を返す 
- `$members bot`:チャンネルにいるbotのメンバーの一覧を返す 
''')
        return

    if subcommand == 'all':
        desc='全ての'
    elif subcommand == 'bot':
        desc='botの'
    else :
        desc='通常の'

    # チャンネルのメンバー一覧を取得
    channel = message.body['channel']
    webapi = slacker.Slacker(settings.API_TOKEN)
    cinfo = webapi.channels.info(channel)
    members = cinfo.body['channel']['members']

    name = ""
    nameall = []
    for member_id in members:
        user_info = webapi.users.info(member_id)
        #name = user_info.body['user']['name']
        #name = name + ": " + user_info.body['user']['profile']['display_name']
        #botsend(message, name)
        basename = user_info.body['user']['profile']['real_name']
        display_name = user_info.body['user']['profile']['display_name']

        if display_name != "":
            basename = display_name
        if subcommand == 'all':
            nameall.append(basename)
        elif subcommand == 'bot':
            if user_info.body['user']['is_bot']:
                nameall.append(basename)
        else:
            if not user_info.body['user']['is_bot']:
                nameall.append(basename)

        nameall.sort(key=str.lower)

#    botsend(message, nameall)
#        name = name + "\n" + format(user_info.body['user'][profile]['display_name'])+ ": " + format(user_info.body['user']['real_name'])
#    botsend(message, name)
    botsend(message, 'このチャンネルの{0}参加者一覧は\n{1}\n{2}参加者です。'.format(desc,'\n'.join(nameall),len(nameall)))
#    botsend(message, 'です。')
