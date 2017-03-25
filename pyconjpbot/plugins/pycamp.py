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

# Python Boot Camp の issue を作成するJIRAのプロジェクトとコンポーネント
PROJECT = 'ISSHA'
COMPONENT = 'Python Boot Camp'

HELP = """
`$pycamp create (地域) (開催日) (現地スタッフJIRA ID)` : pycamp のイベント用issueを作成する
"""


@respond_to('^pycamp\s+create\s+(\S+)\s+(\S+)\s+(\S+)')
def pycamp_create(message, area, date_str, jira_id):
    """
    Python Boot Camp の issue をまとめて作成する

    :params area: 地域名(札幌、大阪など)
    :params date_str: 開催日の日付文字列
    :params jira_id: 現地スタッフの JIRA ID
    """
    try:
        target_date = parser.parse(date_str)
    except ValueError:
        message.send('Python Boot Campの開催日に正しい日付を指定してください')
        return

    issue_dict = {
        'project': {'key': PROJECT},
        'components': [{'name': COMPONENT}],
        'issuetype': {'id': 3},
        'summary': 'テストのチケットです',
        'description': 'h2.目的\n\n説明文に\n改行を入れる',
        'reporter': {'name': 'takanory'},
        'assignee': {'name': 'takanory'},
        'duedate': '{:%Y-%m-%d}'.format(target_date),
        }
    issue = jira.create_issue(fields=issue_dict)
    message.send(issue.permalink())


@respond_to('^pycamp\s+help')
def pycamp_help(message):
    """
    ヘルプメッセージを返す
    """
    message.send(HELP)
