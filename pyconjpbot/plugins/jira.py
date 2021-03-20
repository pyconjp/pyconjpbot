import argparse
import re
from urllib.parse import quote

from jira import JIRA, JIRAError
from slackbot import settings
from slackbot.bot import listen_to, respond_to

from ..botmessage import botsend, botwebapi

# Clean JIRA Url to not have trailing / if exists
CLEAN_JIRA_URL = settings.JIRA_URL
if settings.JIRA_URL[-1:] == "/":
    CLEAN_JIRA_URL = CLEAN_JIRA_URL[:-1]

# Login to jira
jira_auth = (settings.JIRA_USER, settings.JIRA_PASS)
jira = JIRA(CLEAN_JIRA_URL, basic_auth=jira_auth)

# デフォルトの検索対象プロジェクトを設定ファイルから読み込む
DEFAULT_PROJECT = settings.JIRA_DEFAULT_PROJECT

# コンポーネントの一覧
COMPONENT = {
    "全体": "0.全体",
    "事務局": "1.事務局",
    "会場": "2.会場",
    "プログラム": "3.プログラム",
    "システム": "4.システム",
    "デザイン": "5.デザイン・グッズ",
    "その他": "9.その他",
}

# $jira コマンドの引数処理用 argparse
HELP = """
```
$jira {} [-p PROJECT] [-c COMPONENT] [-l LABEL] [-s] [keywords ...]
$jira {} [-p PROJECT] [-c COMPONENT] [-l LABEL] [-s] [keywords ...]

オプション引数:
  -p PROJECT, --project PROJECT
                        検索対象のプロジェクトを指定する(default: {})
  -c COMPONENT, --component COMPONENT
                        検索対象のコンポーネントを指定する
  -l LABEL, --label LABEL
                        検索対象のラベルを指定する
  -s, --summary         要約(タイトル)のみを検索対象にする(未指定時は全文検索)
```
"""

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument(
    "-p",
    "--project",
    default=DEFAULT_PROJECT,
    type=str,
    help=f"検索対象のプロジェクトを指定する(default: {DEFAULT_PROJECT})",
)
parser.add_argument("-c", "--component", type=str, help="検索対象のコンポーネントを指定する")
parser.add_argument("-l", "--label", type=str, help="検索対象のラベルを指定する")
parser.add_argument(
    "-s",
    "--summary",
    default=False,
    action="store_true",
    help="要約(タイトル)のみを検索対象にする(未指定時は全文検索)",
)
parser.add_argument("keywords", nargs="*", type=str, help="検索対象のキーワードを指定する")


def create_attachments(issue_id):
    """
    JIRAのissue_idからそのissueに関連する情報をまとめた Slack のメッセージ用の
    attachments を生成して返す

    :param issue_id: JIRAのissue番号
    """
    project, _ = issue_id.split("-")
    # 存在しないプロジェクトの場合はNoneを返す
    if project not in settings.JIRA_PROJECTS:
        return None

    try:
        # JIRAからissue情報を取得
        issue = jira.issue(issue_id)
    except JIRAError:
        # 存在しない場合はNoneを返す
        return None

    summary = issue.fields.summary
    assignee = "未割り当て"
    if issue.fields.assignee:
        assignee = issue.fields.assignee.displayName
    status = issue.fields.status.name
    issue_url = issue.permalink()

    attachments = [
        {
            "fallback": f"{issue_id} {summary}",
            "pretext": f"<{issue_url}|{issue_id}> {summary}",
            "fields": [
                {
                    "title": "担当者",
                    "value": assignee,
                    "short": True,
                },
                {
                    "title": "ステータス",
                    "value": status,
                    "short": True,
                },
            ],
        }
    ]
    return attachments


@listen_to(r"[A-Za-z]{3,5}-[\d]+")
def jira_listener(message):
    """
    JIRAのissue idっぽいものを取得したら、そのissueの情報を返す
    """
    # botメッセージの場合は無視する
    if message.body.get("subtype", "") == "bot_message":
        return

    text = message.body["text"].upper()
    # JIRAのissue idっぽい文字列を取得
    for issue_id in re.findall(r"[A-Z]{3,5}-[\d]+", text):
        # issue_id から issue 情報の attachments を取得
        attachments = create_attachments(issue_id)
        if attachments:
            # issue 情報を送信する
            botwebapi(message, attachments)


def _drive_help(message, cmd1, cmd2):
    """
    jira 検索コマンドのヘルプを返す
    """
    botsend(message, HELP.format(cmd1, cmd2, DEFAULT_PROJECT))


def _build_jql(args, jql_base=""):
    """
    引数から JIRA を検索するための JQL を生成する
    """
    jql = jql_base
    jql += f"project = {args.project}"
    if args.component:
        component = COMPONENT.get(args.component, args.component)
        jql += f" AND component = {component}"
    if args.label:
        jql += f" AND labels = {args.label}"
    if args.keywords:
        target = "text"
        if args.summary:
            # 要約を検索対象にする
            target = "summary"
        keyword = " ".join(args.keywords)
        jql += f' AND {target} ~ "{keyword}"'

    return jql


@respond_to(r"^jira\s+search\s+(.*)")
@respond_to(r"^jira\s+検索\s+(.*)")
def jira_search(message, keywords):
    """
    JIRAをキーワード検索した結果を返す(オープン状態のみ)
    """

    # 引数を処理する
    try:
        args, argv = parser.parse_known_args(keywords.split())
    except SystemExit:
        botsend(message, "引数の形式が正しくありません")
        _drive_help(message, "search", "検索")
        return

    # 引数から query を生成
    jql = _build_jql(args, 'status in (Open, "In Progress", Reopened) AND ')

    title = f"「{keywords}」の検索結果(オープンのみ)"
    _send_jira_search_responce(message, jql, title)


@respond_to(r"^jira\s+allsearch\s+(.*)")
@respond_to(r"^jira\s+全検索\s+(.*)")
def jira_allsearch(message, keywords):
    """
    JIRAをキーワード検索した結果を返す(全ステータス対象)
    """
    # 引数を処理する
    try:
        args, argv = parser.parse_known_args(keywords.split())
    except SystemExit:
        botsend(message, "引数の形式が正しくありません")
        _drive_help(message, "search", "検索")
        return

    # 引数から query を生成
    jql = _build_jql(args)

    title = f"「{keywords}」の検索結果(全ステータス)"
    _send_jira_search_responce(message, jql, title)


@respond_to(r"^jira\s+assignee\s+(.*)")
@respond_to(r"^jira\s+担当者?\s+(.*)")
def jira_assignee(message, user):
    """
    指定されたユーザーにアサインされた課題の一覧を返す
    """
    jql = f'status in (Open, "In Progress", Reopened) AND assignee in ({user})'
    title = f"「{user}」の担当課題"
    _send_jira_search_responce(message, jql, title)


def _send_jira_search_responce(message, query, title):
    """
    JIRAをqueryで検索した結果を返すメソッド
    """
    pretext = title
    pretext += f"(<{CLEAN_JIRA_URL}/issues/?jql={quote(query)}|JIRAで見る>)"
    text = ""

    try:
        issues = jira.search_issues(query)
    except JIRAError as err:
        # なんらかのエラーが発生
        botsend(message, f"JIRAError: `{err.text}`")
        return

    if issues:
        for issue in issues:
            summary = issue.fields.summary
            key = issue.key
            url = issue.permalink()
            status = issue.fields.status.name
            text += f"- <{url}|{key}> {summary}({status})\n"
    else:
        text += "該当するJIRA issueは見つかりませんでした"

    attachments = [
        {
            "fallback": title,
            "pretext": pretext,
            "text": text,
        }
    ]
    botwebapi(message, attachments)


@respond_to(r"^jira\s+filters?")
@respond_to(r"^jira\s+フィルター?")
def jira_filter(message):
    """
    フィルターの一覧を返す
    """
    pretext = "フィルター一覧"
    filters = [
        ("1.事務局チーム", "10301"),
        ("2.会場チーム", "10302"),
        ("3.プログラムチーム", "10300"),
        ("4.メディアチーム ", "10303"),
        ("一般社団法人PyCon JP", "11500"),
    ]
    flist = []
    for label, key in filters:
        flist.append(f"<{CLEAN_JIRA_URL}/issues/?filter={key}|{label}>")

    attachments = [
        {
            "fallback": pretext,
            "pretext": pretext,
            "text": " / ".join(flist),
        }
    ]
    botwebapi(message, attachments)


@respond_to(r"^jira\s+help$")
def jira_help(message):
    """
    jiraコマンドのヘルプを返す
    """
    botsend(
        message,
        """- `INU-123`: 指定されたチケットの詳細情報を返す
- `$jira search keywords` `$jira 検索 keywords`: 指定されたキーワードで検索(オープンのみ)
- `$jira allsearch keywords` `$jira 全検索 keywords`: 指定されたキーワードで検索(全ステータス)
- `$jira assignee user` `$jira 担当 user`: 指定されたユーザーが担当しているissueを返す
- `$jira filter` `$jira フィルター`: フィルターの一覧を返す

検索/全検索時に使用できるオプション"""
        + HELP.format("検索", "全検索", DEFAULT_PROJECT),
    )
