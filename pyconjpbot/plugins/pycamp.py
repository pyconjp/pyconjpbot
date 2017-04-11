from datetime import timedelta

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

# コアスタッフの JIRA username
REPORTER = 'takanory'
CORE_STAFFS = ('makoto-kimura', 'takanory', 'ryu22e')

HELP = """
`$pycamp create (地域) (開催日) (現地スタッフJIRA) (講師のJIRA)` : pycamp のイベント用issueを作成する
"""

# 作成するチケットのテンプレート
TEMPLATE = {
    'assignee_type': 'reporter',  # reporter/local_staff/lecturer
    'delta': +30,  # 開催日から30日後
    'summary': 'Python Boot Camp in {area}を開催',
    'description': '''h2. 目的

* Python Boot Camp in {area}を開催するのに必要なタスクとか情報をまとめる親タスク

h2. 内容

* 日時: {target_date:%Y-%m-%d(%a)}
* 会場: 
* 現地スタッフ: [~{local_staff}]
* 講師: [~{lecturer}]
* TA: 
* イベントconnpass: https://pyconjp.connpass.com/event/XXXXX/
* 懇親会connpass: https://pyconjp.connpass.com/event/XXXXX/
'''
}

# サブタスクのテンプレート
SUBTASK_TEMPLATE = {
    '1.事前準備': [
        {
            'assignee_type': 'reporter',  # reporter/local_staff/lecturer
            'delta': -30,  # 開催一ヶ月前
            'summary': 'connpassイベント公開(現地スタッフ)',
            'description': '''h2. 目的

* 参加者を募るために、イベント本体、懇親会のconnpassイベントを作成して公開する
* イベント開催の一ヶ月前くらいには公開したい

h2. 内容

* connpassイベントを過去イベントからコピーしてベースを作成
** 事前アンケートも過去イベントからコピーする
* ロゴ設定
* 会場設定
* 説明文の修正(場所、講師など)
'''
        },
        {
            'assignee_type': 'lecturer',  # reporter/local_staff/lecturer
            'delta': -30,  # 開催一ヶ月前
            'summary': 'ホテル、移動の手配(講師)',
            'description': '''h2. 目的

* 現地往復の交通手段を事前に予約する
* ホテルの予約をする

h2. 内容

* 予約した内容と金額の記載をする
* 支払いは、Python Boot Camp 終了後に別チケットで行います
'''
        },
        {
            'assignee_type': 'reporter',  # reporter/local_staff/lecturer
            'delta': -21,  # 開催3週間前
            'summary': '事前打ち合わせ(主: コアスタッフ)',
            'description': '''h2. 目的

* 事前打ち合わせする

h2. 内容

* 日程調整
* 議事録準備
'''
        },
        {
            'assignee_type': 'local_staff',  # reporter/local_staff/lecturer
            'delta': -5,  # 開催直前
            'summary': '参加者への事前連絡(現地スタッフ)',
            'description': '''h2. 目的

h2. 内容

'''
        },
        {
            'assignee_type': 'local_staff',  # reporter/local_staff/lecturer
            'delta': -2,  # 開催直前
            'summary': 'お茶、お菓子購入(現地スタッフ)',
            'description': '''h2. 目的

h2. 内容

'''
        },
    ],
    '2.広報': [
        {
            'assignee_type': 'local_staff',  # reporter/local_staff/lecturer
            'delta': -14,  # 開催2週間前
            'summary': '事前ブログ執筆(現地スタッフ)',
            'description': '''h2. 目的

h2. 内容

'''
        },
        {
            'assignee_type': 'reporter',  # reporter/local_staff/lecturer
            'delta': -14,  # 開催2週間前
            'summary': 'メディアスポンサー経由での告知(コアスタッフ)',
            'description': '''h2. 目的

h2. 内容

'''
        },
    ],
    '3.イベント当日': [
    ],
    '4.事後処理': [
    ],
}


def create_issue(template, params, parent=None, area=None):
    """
    テンプレートにパラメーターを適用して、JIRA issueを作成する

    :params template:
    :params params:
    :params parent: 親issueのID(ISSHA-XXX)
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
        import pdb
        pdb.set_trace()
        issue = create_issue(TEMPLATE, params)
        desc = issue.fields.description

        # サブタスクを作成する
        for category in sorted(SUBTASK_TEMPLATE.keys()):
            # カテゴリーを description に追加
            desc += '\r\n\r\nh3. {}\r\n\r\n'.format(category)
            for subtask in SUBTASK_TEMPLATE[category]:
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
