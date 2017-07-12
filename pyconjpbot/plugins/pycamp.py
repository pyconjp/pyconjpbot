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
* 公開のタイミングは平日の昼間が狙い目（多くの人に見てもらえる）
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

* 現地スタッフ、コアスタッフ、講師のやること認識合わせのために事前打ち合わせを実施する
* Slack の Call を使う想定

h2. 内容

* 調整さんで日程調整
* connpassでイベントを作成→参加忘れを防ぐため
* Google Driveに議事録を準備
* JIRAのチケットをベースにして確認を進める
* TODOがあった場合は、JIRAのチケットを作成する
** JIRAのチケットを作成する際には、親チケットに対してサブタスクとしてぶら下げて下さい
** 参考URL http://manual.pycon.jp/staff/tool-tips.html#create-issue
'''
        },
        {
            'assignee_type': 'local_staff',  # reporter/local_staff/lecturer
            'delta': -5,  # 開催直前
            'summary': '参加者への事前連絡(現地スタッフ)',
            'description': '''h2. 目的

* 参加者が当日スムーズにイベントに参加できるように、重要事項をを事前に連絡する

h2. 内容

* 以下をconnpassメッセージで参加者に伝える
* 事前準備(python3、エディタインストール)をすること
* 懇親会の案内
* pyconjp-fellow.slack.com への誘導( https://pyconjp-fellow.herokuapp.com/ )
* 会場へのアクセス
* 無線LANの有無確認
* 電源コンセントが十分足りるか確認
* 参考: 過去文面は ISSHA-470 とかを参考にしてください

'''
        },
        {
            'assignee_type': 'local_staff',  # reporter/local_staff/lecturer
            'delta': -2,  # 開催直前
            'summary': 'お茶、お菓子購入(現地スタッフ)',
            'description': '''h2. 目的

* イベント当日、講師や参加者が飲み食べするためのお茶とお菓子を購入して会場に持っていく

h2. 内容

* お菓子は小分けしやすいスナック菓子など
* お茶はペットボトル+紙コップでOK
* お金はあとで精算するので領収書をもらってください
* 3時くらいに休憩を取って、お菓子を配って和気あいあいとしましょう

'''
        },
    ],
    '2.広報': [
        {
            'assignee_type': 'local_staff',  # reporter/local_staff/lecturer
            'delta': -14,  # 開催2週間前
            'summary': '事前ブログ執筆(現地スタッフ)',
            'description': '''h2. 目的

* イベントを広く知ってもらうために PyCon JP のブログに記事を書く

h2. 内容

* メールアドレスを [~ryu22e] に伝えて、ブログの書き込み権限をもらってください
* その後ブログの記事を書いて、公開してください
* このblogの公開のタイミングも平日の昼間が狙い目
* 必要なら事前に内容を Slack でレビューしてください

h2. 記事作成の参考情報

* 以下のような内容を入れる。フランクな文体で書いてもOK
** 開催地をイメージできるような写真
** Python Boot Campについて簡単な説明
** connpassのURL（イベント本体・懇親会）
** 講師のプロフィール紹介
** 「懇親会も参加するのがお勧めです！」みたいな文
* 記事の設定は以下のようにする
** ラベルは「pycamp, pyconjp, tutorial」
** パーマリンクは「pycamp-in-地域名.html」（地域名に今回の開催地名がローマ字で入る）
* 過去の記事
** 札幌: http://pyconjp.blogspot.jp/2016/10/pycamp-in-sapporo.html
** 栃木小山: http://pyconjp.blogspot.jp/2017/01/pycamp-in-tochigioyama.html
** 広島: http://pyconjp.blogspot.jp/2017/02/python-boot-camp-in.html
** 大阪: http://pyconjp.blogspot.jp/2017/03/pycamp-in-osaka.html
'''
        },
        {
            'assignee_type': 'reporter',  # reporter/local_staff/lecturer
            'delta': -14,  # 開催2週間前
            'summary': 'メディアスポンサー経由での告知(コアスタッフ)',
            'description': '''h2. 目的

* イベントの認知度を上げるために、メディアスポンサーに告知してもらう

h2. 内容


* 各メディアスポンサーのサイトにイベントの情報が掲載されたり、記事が載ったりする
* エンジニアtypeについては終了後のインタビューとかできないか打診する

'''
        },
        {
            'assignee_type': 'reporter',  # reporter/local_staff/lecturer
            'delta': -14,  # 開催2週間前
            'summary': 'Twitter定期通知(コアスタッフ)',
            'description': '''h2. 目的

* イベントを知ってもらうためにTwitterの定期通知を入れる

h2. 内容


* うざくならない程度のTwitterの定期通知にする
** https://docs.google.com/spreadsheets/d/1lpa9p_dCyTckREf09-oA2C6ZAMACCrgD9W3HQSKeoSI/edit#gid=0
* 満席になった場合は定期通知を止めることをお忘れなく

'''
        },
        {
            'assignee_type': 'local_staff',  # reporter/local_staff/lecturer
            'delta': -14,  # 開催2週間前
            'summary': '現地メディア経由での告知(現地スタッフ)',
            'description': '''h2. 目的

* いろいろな人に知ってもらうために、PyCon JP 以外の現地のチャネルを使って広報する

h2. 内容


* 以下のような候補があると思います
* 地方紙
* 現地コミュニティ
* 近県のコミュニティ
* 現地の大学、高専など

'''
        },
    ],
    '3.イベント当日': [
        {
            'assignee_type': 'local_staff',  # reporter/local_staff/lecturer
            'delta': -1,  # 開催前日
            'summary': 'ランチミーティング(主: 現地スタッフ)',
            'description': '''h2. 目的

* 講師、TA、現地スタッフが事前に顔合わせをするためのランチミーティングを実施する
* イベント当日の11:30くらいから開始
* 顔合わせをすることよにって、仲良くなって、お互いに助け合ってよりよいイベントにする

h2. 内容

* 店を決めて、集合時間、場所などを関係者(講師、TAなど)に周知
* おいしく楽しくランチを食べる
'''
        },
        {
            'assignee_type': 'local_staff',  # reporter/local_staff/lecturer
            'delta': -1,  # 開催前日
            'summary': '参加者アンケート実施(現地スタッフ)',
            'description': '''h2. 目的

* 参加者の満足度を確認するため、今後よりよいイベントとするためにアンケートを実施

h2. 内容

* https://docs.google.com/forms/d/1x125tHum4MVmiUbcxQdCmOqFMirNZPICF-9QsVNJ2eg/edit をコピーしてアンケート作成
* イベントの終了直前に、参加者にアンケートのURLを告知して回答してもらう
** connpassのメッセージ機能を使うとよさそう
** 事前ミーティングでお知らせ済みのgoogle Driveに共有してね。程度でOK
* 振り返りミーティングでアンケートの結果を確認する
'''
        },
    ],
    '4.事後処理': [
        {
            'assignee_type': 'local_staff',  # reporter/local_staff/lecturer
            'delta': 14,  # 開催2週間後
            'summary': '精算処理(現地スタッフ)',
            'description': '''h2. 目的

* 現地スタッフが使用した経費を精算する

h2. 内容

* 経費の内訳(お茶菓子等)、金額について記載する
* 領収書の電子データでこのチケットに添付する
** 宛名：一般社団法人PyCon JP
** 領収書のデータはGoogle Driveのフォルダに入れて、リンクをJIRAから貼ること
** スキャナーない人はCamScannerアプリおすすめ
* 振込先の口座情報を記載する
* これらの情報が揃ったら [~ryu22e] にチケットをまわしてください

h3. 経費の内訳

* (ここに経費の内訳と金額、合計金額を書く)

h3. 振込先口座

* (ここに振込先口座の情報を書く)

'''
        },
        {
            'assignee_type': 'lecturer',  # reporter/local_staff/lecturer
            'delta': 14,  # 開催2週間後
            'summary': '精算処理(講師)',
            'description': '''h2. 目的

* 講師が使用した経費を精算する
* 講師謝礼とまとめて振り込む

h2. 内容

* 旅費、宿泊費の領収書を電子データでこのチケットに添付する
** 宛名：一般社団法人PyCon JP
** 領収書のデータはGoogle Driveのフォルダに入れて、リンクをJIRAから貼ること
* 合計金額を記載する
* 振込先の口座情報を記載する
* 謝礼の源泉徴収をおわすれなく(会計担当)

'''
        },
        {
            'assignee_type': 'local_staff',  # reporter/local_staff/lecturer
            'delta': 14,  # 開催2週間後
            'summary': '事後ブログ(現地スタッフ)',
            'description': '''h2. 目的

* Python Boot Camp の開催報告として事後ブログをPyCon JPブログに書く
* 他の地域の人が「自分のところでも開催しようかな」と思えるような内容にする


h2. 内容

* 写真入りで雰囲気を伝える
* やってみてどうだったかの感想を書く
* このblogの公開のタイミングも平日の昼間が狙い目
** 公開前に、ラベル・パーマリンクの設定を忘れずに
* 現地スタッフ申し込みフォームへのリンクを追加する
** https://www.pycon.jp/support/bootcamp.html
** https://docs.google.com/forms/d/e/1FAIpQLSedZskvqmwH_cvwOZecI10PA3KX5d-Ui-74aZro_cvCcTZLMw/viewform
'''
        },
        {
            'assignee_type': 'local_staff',  # reporter/local_staff/lecturer
            'delta': 21,  # 開催3週間後
            'summary': '振り返りミーティング(主: 現地スタッフ)',
            'description': '''h2. 目的

* Python Boot Camp をよりよいものにするために、振り返りミーティングを実施し、今後の改善につなげる

h2. 内容

* 調整さんで日程調整(主: 現地スタッフ、講師、TA、コアスタッフ)
* connpassでイベントを作成→参加忘れを防ぐため
** 管理者に @takanory を入れる。
* 議事録を準備
* ミーティングを実施
* 振り返りミーティングで出た内容でkeep/problem/tryすることをまとめる(コアスタッフ)

'''
        },
        {
            'assignee_type': 'reporter',  # reporter/local_staff/lecturer
            'delta': 28,  # 開催4週間後
            'summary': '経費まとめ(コアスタッフ)',
            'description': '''h2. 目的

* イベントの最後に実際にかかった経費とかをシートにまとめる

h2. 内容

* connpass、精算チケットの内容を元に、下記のシートを埋める
* https://docs.google.com/spreadsheets/d/1Fcgck7fMl6JpqeEVS7j542LE39ibRmCi3UxzfWhcLuc/edit#gid=1024129981


'''
        },
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
