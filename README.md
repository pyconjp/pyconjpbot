# PyCon JP Bot

* Chatbot for Slack of PyCon JP
* based on https://github.com/lins05/slackbot

![](pyconjpbot-image.png)

## Commands

コマンドの一覧と簡単な説明

### manual plugin

- `$manual`: マニュアルのURLを返す
- `$manual keywords`: キーワードでマニュアルを検索するURLを返す
- `$manual help`: manual コマンドのヘルプを表示

### jira plugin

- `SAR-123`: JIRAのissueの情報を返す
- `$jira search keywords`: 指定したキーワードでJIRAを検索した結果を返す(オープンのみ)
- `$jira allsearch keywords`: 指定したキーワードでJIRAを検索した結果を返す(全ステータス)
- `$jira assignee keywords`: 指定されたユーザーが担当しているissueを返す
- `$jira filter`: フィルターの一覧を返す

### wikipedia plugin

- `$wikipedia keywords`: 指定されたキーワードの Wikipedia ページの情報を返す
- `$wikipedia -en keywords`: 指定された言語(en等)の Wikipedia ページの情報を返す
- `$wikipedia help`: wikipedia コマンドのヘルプを表示

### calc plugin

- 以下の様な数式の計算結果を返す

```
1 + 1
100 * 100
1 / 10
sqrt(2)
```

### greeting plugin

- あいさつを返す

```
takanory: おはよう
BOT: @takanory おはようございます
```

### misc plugin

- `$helps`: ヘルプへのリンクを返す
- `$shuffle spam ham eggs`: 指定された単語をシャッフルした結果を返す
- `$choice spam ham eggs`: 指定された単語から一つをランダムに選んで返す

## How to build

```
$ git clone git@github.com:pyconjp/pyconjpbot.git
$ cd pyconjpbot
$ virtualenv -p python3.5 env
$ . env/bin/activate
(env)$ pip install -r requirements.txt
(env)$ cp slackbot_settings.py.sample slackbot_settings.py
(env)$ vi slackbot_settings.py
(env)$ python run.py
```

