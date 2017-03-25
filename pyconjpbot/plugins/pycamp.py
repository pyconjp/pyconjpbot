from dateutil import parser
from jira import JIRA, JIRAError
from slackbot import settings
from slackbot.bot import respond_to

# Clean JIRA Url to not have trailing / if exists
CLEAN_JIRA_URL = settings.JIRA_URL
if settings.JIRA_URL[-1:] == '/':
    CLEAN_JIRA_URL = CLEAN_JIRA_URL[:-1]

# Login to jira
jira_auth = (settings.JIRA_USER, settings.JIRA_PASS)
jira = JIRA(CLEAN_JIRA_URL, basic_auth=jira_auth)

# Python Boot Camp の issue を作成するJIRAのプロジェクトとコンポーネント名
PROJECT = 'ISSHA'
COMPONENT = 'Python Boot Camp'

# JIRA の issue の種類
ISSUE_TYPE_TASK = 3     # タスク
ISSUE_TYPE_SUBTASK = 5  # サブタスク

HELP = """
`$pycamp create (地域) (開催日) (現地スタッフJIRA) (講師のJIRA)` : pycamp のイベント用issueを作成する
"""


@respond_to('^pycamp\s+create\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)')
def pycamp_create(message, area, date_str, local_staff, lecturer):
    """
    Python Boot Camp の issue をまとめて作成する

    :params area: 地域名(札幌、大阪など)
    :params date_str: 開催日の日付文字列
    :params jira_id: 現地スタッフの JIRA ID
    """

    # 日付が正しいかチェック
    try:
        target_date = parser.parse(date_str)
    except ValueError:
        message.send('Python Boot Campの開催日に正しい日付を指定してください')
        return

    # 指定されたユーザーの存在チェック
    try:
        jira.user(local_staff)
        jira.user(lecturer)
    except JIRAError as e:
        message.send('`$pycamp` エラー:', e.text)
        return

    issue_dict = {
        'project': {'key': PROJECT},
        'components': [{'name': COMPONENT}],
        'issuetype': {'id': ISSUE_TYPE_TASK},
        'summary': 'テストのチケットです',
        'description': 'h2.目的\n\n説明文に\n改行を入れる',
        'reporter': {'name': local_staff},
        'assignee': {'name': lecturer},
        'duedate': '{:%Y-%m-%d}'.format(target_date),
        }
    try:
        issue = jira.create_issue(fields=issue_dict)
        # watcherからはずす
        jira.remove_watcher(issue, settings.JIRA_USER)
        message.send(issue.permalink())
    except JIRAError as e:
        import pdb
        pdb.set_trace()
        message.send('`$pycamp` エラー:', e.text)


@respond_to('^pycamp\s+help')
def pycamp_help(message):
    """
    ヘルプメッセージを返す
    """
    message.send(HELP)
