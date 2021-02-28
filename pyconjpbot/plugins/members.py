from slackbot.bot import respond_to
from slackbot import settings
import slacker
import json

from ..botmessage import botsend, botreply, botwebapi


@respond_to('^members$')
@respond_to(r'^members\s+(all|bot|help)$')
def members_command(message, subcommand=None):
    """
    チャンネル参加者のメンション名の一覧を返す

    - https://github.com/os/slacker
    - https://api.slack.com/methods/conversations.members
    - https://api.slack.com/methods/users.list
    - https://api.slack.com/methods/users.getPresence
    - https://api.slack.com/methods/users.info
    """

    if subcommand == 'help':
        botsend(message, '''- `$members`: チャンネルにいる通常の参加者のメンション名の一覧を返す
- `$members all`:チャンネルにいる全ての参加者のメンション名の一覧を返す
- `$members bot`:チャンネルにいるbotの参加者メンション名の一覧を返す
''')
        return

    if subcommand == 'all':
        desc = '全ての'
    elif subcommand == 'bot':
        desc = 'botの'
    else:
        desc = '通常の'

    # チャンネルのメンバー一覧を取得
    channel = message.body['channel']
    webapi = slacker.Slacker(settings.API_TOKEN)
    cinfo = webapi.conversations.members(channel)
    members = cinfo.body['members']

    # 全メンバーを取得
    all_user_info = webapi.users.list()

    # 作業用リスト初期化
    member_list = []

    # 警告文字列初期化
    warn_str = ""

    # このチャンネルのメンバーを順次処理
    for member_id in members:
        # 全ユーザー情報リストから該当するユーザで抽出
        memberkeys = [x for x in all_user_info.body['members']
                      if x['id'] == member_id]
        # 全ユーザ情報リストに該当無いケースは無視
        if memberkeys == []:
            continue

        # idが複数ヒットした場合警告を出す
        if len(memberkeys) > 1:
            warn_str += "\nidが複数ヒットしたので注意\n"
            warn_str += json.dumps(memberkeys)

        if subcommand == 'all':
            # allは全て通す対象
            pass
        elif subcommand == 'bot' and not memberkeys[0]['is_bot']:
            # bot指定時通常ユーザはskip
            continue
        elif subcommand is None and memberkeys[0]['is_bot']:
            # 通常時はbotをskip
            continue

        # real_nameまたはdisplay_nameにメンション用文字列が入っている推測
        basename = memberkeys[0]['profile']['real_name']
        display_name = memberkeys[0]['profile']['display_name']

        # display_nameが設定されていればそれを優先
        if display_name != "":
            basename = display_name

        member_list.append(basename)

    # 探しやすいように大小文字区別なしアルファベット順
    member_list.sort(key=str.lower)

    pretext = 'このチャンネルの{0}参加者は以下{1}名です。'.format(desc, len(member_list))
    maintext = '{0}\n{1}'.format('\n'.join(member_list), warn_str)

    attachments = [{
        'pretext': pretext,
        'text': maintext,
        'color': '#59afe1'}]

    message.reply_webapi('', json.dumps(attachments), in_thread=True)
