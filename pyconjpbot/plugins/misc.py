import calendar
import random
from datetime import date

import git
from slack_sdk import WebClient
from slackbot import settings
from slackbot.bot import respond_to
from slackbot.dispatcher import Message

from ..botmessage import botreply, botsend, botwebapi


@respond_to(r"^help$")
def help(message: Message) -> None:
    """
    helpページのURLを返す
    """
    botsend(message, "ヘルプはこちら→ https://github.com/pyconjp/pyconjpbot#commands")


@respond_to(r"^shuffle\s+(.*)")
def shuffle(message: Message, words_str: str) -> None:
    """
    指定したキーワードをシャッフルして返す
    """
    words = words_str.split()
    if len(words) == 1:
        botsend(message, "キーワードを複数指定してください\n`$shuffle word1 word2...`")
    else:
        random.shuffle(words)
        botsend(message, " ".join(words))


@respond_to(r"^choice\s+(.*)")
def choice(message: Message, words_str: str) -> None:
    """
    指定したキーワードから一つを選んで返す
    """
    words = words_str.split()
    if len(words) == 1:
        botsend(message, "キーワードを複数指定してください\n`$choice word1 word2...`")
    else:
        botsend(message, random.choice(words))


@respond_to(r"^ping$")
def ping(message: Message) -> None:
    """
    pingに対してpongで応答する
    """
    botreply(message, "pong")


@respond_to(r"^version$")
def version(message: Message) -> None:
    """
    バージョン情報を返す
    """
    obj = git.Repo("").head.object
    url = f"https://github.com/pyconjp/pyconjpbot/commit/{obj.hexsha}"
    text = (
        f"<{url}|{obj.hexsha[:6]}> {obj.summary}"
        f"- {obj.committer.name}({obj.committed_datetime})"
    )
    attachments = [
        {
            "pretext": text,
        }
    ]
    botwebapi(message, attachments)


@respond_to(r"^random$")
@respond_to(r"^random\s+(active|help)$")
def random_command(message: Message, subcommand: str = "") -> None:
    """
    チャンネルにいるメンバーからランダムに一人を選んで返す

    - https://api.slack.com/methods/conversations.members
    - https://api.slack.com/methods/users.getPresence
    - https://api.slack.com/methods/users.info
    """

    if subcommand == "help":
        botsend(
            message,
            """- `$random`: チャンネルにいるメンバーからランダムに一人を選ぶ
- `$random active`: チャンネルにいるactiveなメンバーからランダムに一人を選ぶ
""",
        )
        return

    # チャンネルのメンバー一覧を取得
    channel = message.body["channel"]
    client = WebClient(token=settings.API_TOKEN)
    result = client.conversations_members(channel=channel)
    members = result["members"]

    # bot の id は除く
    bot_id = message._client.login_data["self"]["id"]
    members.remove(bot_id)

    member_id = None
    while not member_id:
        # メンバー一覧からランダムに選んで返す
        member_id = random.choice(members)
        if subcommand == "active":
            # active が指定されている場合は presence を確認する
            presence = client.users_getPresence(user=member_id)
            if presence["presence"] == "away":
                members.remove(member_id)
                member_id = None

    user_info = client.users_info(user=member_id)
    name = user_info["user"]["name"]
    botsend(message, f"{name} さん、君に決めた！")


@respond_to(r"^cal$")
@respond_to(r"^cal\s+(\d+)$")
@respond_to(r"^cal\s+(\d+)\s+(\d+)$")
def cal_command(message: Message, month_str: str = "", year_str: str = "") -> None:
    """
    一ヶ月のカレンダーを返す
    """
    today = date.today()
    month = int(month_str) if month_str else today.month
    year = int(year_str) if year_str else today.year

    cal = calendar.TextCalendar(firstweekday=calendar.SUNDAY)
    try:
        botsend(message, f"```{cal.formatmonth(year, month)}```")
    except IndexError:
        # 数字が範囲外の場合は無視する
        pass


@respond_to(r"^cal\s+help$")
def cal_help(message: Message) -> None:
    """
    cal コマンドのヘルプを返す
    """
    botsend(
        message,
        """- `$cal`: 今月のカレンダーを返す
- `$cal 9`: 今年の指定された月のカレンダーを返す
- `$cal 9 2016`: 指定された年月のカレンダーを返す
""",
    )
