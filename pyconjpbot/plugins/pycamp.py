from datetime import timedelta

from dateutil import parser
from jira import JIRA, JIRAError
from slackbot import settings
from slackbot.bot import respond_to

from ..google_plugins.google_api import get_service

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

# コアスタッフの JIRA username
REPORTER = 'takanory'
CORE_STAFFS = ('makoto-kimura', 'takanory', 'ryu22e')

ASSIGNEE_TYPE = {
    '作成者': 'reporter',
    '現地スタッフ': 'local_staff',
    '講師': 'lecturer',
    }

# テンプレートとなるスプレッドシートのID
# https://docs.google.com/spreadsheets/d/1LEtpNewhAFSf_vtkhTsWi6JGs2p-7XHZE8yOshagz0I/edit#gid=1772747731
SHEET_ID = '1LEtpNewhAFSf_vtkhTsWi6JGs2p-7XHZE8yOshagz0I'

HELP = """
`$pycamp create (地域) (開催日) (現地スタッフJIRA) (講師のJIRA)` : pycamp のイベント用issueを作成する
"""


def create_issue(template, params, parent=None, area=None):
    """
    テンプレートにパラメーターを適用して、JIRA issueを作成する

    :params template:
    :params params:
    :params parent: 親issueのID(ISSHA-XXX)
    :params area: 地域名(東京、大阪など)
    """

    # 担当者情報を作成
    assignee_type = template.get('assignee_type', 'reporter')
    assignee = params[assignee_type]
    # 期限の日付を作成
    delta = timedelta(days=template.get('delta', -7))
    duedate = params['target_date'] + delta

    issue_dict = {
        'project': {'key': PROJECT},
        'components': [{'name': COMPONENT}],
        'summary': template.get('summary', '').format(**params),
        'description': template.get('description', '').format(**params),
        'assignee': {'name': assignee},  # 担当者
        'reporter': {'name': REPORTER},  # 報告者
        'duedate': '{:%Y-%m-%d}'.format(duedate),  # 期限
    }

    if parent:
        # 親issueのサブタスクとして作成
        issue_dict['parent'] = {'key': parent}
        issue_dict['issuetype'] = {'id': ISSUE_TYPE_SUBTASK}

        # サブタスクはタイトルの先頭に "#pycamp 地域: " とつける
        summary = '#pycamp {area}: ' + template.get('summary', '')
        issue_dict['summary'] = summary.format(**params)
    else:
        issue_dict['issuetype'] = {'id': ISSUE_TYPE_TASK}

    # issue を作成する
    issue = jira.create_issue(fields=issue_dict)
    # JIRA bot を watcher からはずす
    jira.remove_watcher(issue, settings.JIRA_USER)
    # コアスタッフを watcher に追加
    for watcher in CORE_STAFFS:
        jira.add_watcher(issue, watcher)
    return issue


def get_task_template(service):
    """
    Google Spreadsheetから親タスクのテンプレート情報を抜き出す

    :param service: Google Sheets APIの接続サービス
    """
    result = service.spreadsheets().values().get(
        spreadsheetId=SHEET_ID, range='親タスク!A2:D2').execute()
    row = result.get('values', [])[0]
    # 作成するチケットのテンプレート
    template = {
        'assignee_type': ASSIGNEE_TYPE[row[0]],
        'delta': int(row[1]),  # 開催日からの差の日数
        'summary': row[2],  # タイトル
        'description': row[3],  # 本文
    }
    return template


def get_subtask_template(service):
    """
    Google Spreadsheetから親タスクのテンプレート情報を抜き出す

    :param service: Google Sheets APIの接続サービス
    """
    result = service.spreadsheets().values().get(
        spreadsheetId=SHEET_ID, range='サブタスク!A2:E').execute()
    subtask_template = {}
    for row in result.get('values', []):
        category = row[0]
        template = {
            'assignee_type': ASSIGNEE_TYPE[row[1]],
            'delta': int(row[2]),  # 開催日からの差の日数
            'summary': row[3],
            'description': row[4],
        }
        if category in subtask_template:
            subtask_template[category].append(template)
        else:
            subtask_template[category] = [template]
    return subtask_template


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
        message.send('`$pycamp` エラー: `{}`'.format(e.text))
        return

    # Google Sheets API でシートから情報を抜き出す
    service = get_service('sheets', 'v4')
    # 親タスクのテンプレートをスプレッドシートから取得
    task_template = get_task_template(service)
    # 親タスクのテンプレートをスプレッドシートから取得
    subtask_template = get_subtask_template(service)

    # issue を作成するための情報
    params = {
        'reporter': REPORTER,
        'local_staff': local_staff,
        'lecturer': lecturer,
        'target_date': target_date,
        'area': area,
    }
    try:
        # テンプレートとパラメーターから JIRA issue を作成する
        issue = create_issue(task_template, params)
        desc = issue.fields.description

        # サブタスクを作成する
        for category in sorted(subtask_template.keys()):
            # カテゴリーを description に追加
            desc += '\r\n\r\nh3. {}\r\n\r\n'.format(category)
            for subtask in subtask_template[category]:
                sub_issue = create_issue(subtask, params, issue.key, area)
                _, summary = sub_issue.fields.summary.split(': ', 1)
                # サブタスクへのリンクを親タスクのdescriptionに追加
                desc += '* {} {}\r\n'.format(sub_issue.key, summary)

        # descriptionを更新する
        issue.update(description=desc)

        message.send('チケットを作成しました: {}'.format(issue.permalink()))
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
