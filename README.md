# PyCon JP Bot

* Chatbot for Slack of PyCon JP
* based on https://github.com/lins05/slackbot

<img src="pyconjpbot-image.png" width="300">

## Commands

コマンドの一覧と簡単な説明

### manual plugin

- `$manual`: マニュアルのURLを返す
- `$manual keywords`: キーワードでマニュアルを検索するURLを返す
- `$manual help`: manual コマンドのヘルプを表示
- [manual.py](https://github.com/pyconjp/pyconjpbot/blob/master/pyconjpbot/plugins/manual.py)

### jira plugin

- `SAR-123`: JIRAのissueの情報を返す
- `$jira search|検索 keywords`: 指定したキーワードでJIRAを検索した結果を返す(オープンのみ)
- `$jira allsearch|全検索 keywords`: 指定したキーワードでJIRAを検索した結果を返す(全ステータス)
- `$jira assignee|担当 keywords`: 指定されたユーザーが担当しているissueを返す
- `$jira filter|フィルター`: フィルターの一覧を返す
- [jira.py](https://github.com/pyconjp/pyconjpbot/blob/master/pyconjpbot/plugins/jira.py)

### wikipedia plugin

- `$wikipedia keywords`: 指定されたキーワードの Wikipedia ページの情報を返す
- `$wikipedia -en keywords`: 指定された言語(en等)の Wikipedia ページの情報を返す
- `$wikipedia help`: wikipedia コマンドのヘルプを表示
- [wikipedia.py](https://github.com/pyconjp/pyconjpbot/blob/master/pyconjpbot/plugins/wikipedia.py)

### calc plugin

- 以下の様な数式の計算結果を返す

```
1 + 1
100 * 100
1 / 10
sqrt(2)
```

- [calc.py](https://github.com/pyconjp/pyconjpbot/blob/master/pyconjpbot/plugins/calc.py)

### reaction plugin

- 任意のキーワードに対して emoji でのリアクションを返す
- [reaction.py](https://github.com/pyconjp/pyconjpbot/blob/master/pyconjpbot/plugins/reaction.py)

### greeting plugin

- あいさつを返す

```
takanory: おはよう
BOT: @takanory おはようございます
```

- [greeting.py](https://github.com/pyconjp/pyconjpbot/blob/master/pyconjpbot/plugins/greeting.py)

### translator plugin

- `$translate python`, `$翻訳 python`: 指定した文字列を日本語に翻訳
- `$translate へび`, `$翻訳 蛇`: 指定した文字列を英語に翻訳
- `$translate -ru へび` `$翻訳 -ru へび`: 指定した言語(ru等)に翻訳
- `$translate list` `$翻訳 リスト`: 使用できる言語の一覧を返す

- [translator.py](https://github.com/pyconjp/pyconjpbot/blob/master/pyconjpbot/plugins/translator.py)
- Powered by [Microsoft Translator API](https://www.microsoft.com/en-us/translator/getstarted.aspx "Getting Started with Microsoft Translator")

### weather plugin

- `$weather` `$天気`: 東京の天気予報を返す
- `$weather 釧路` `$天気 釧路`: 指定した地域の天気予報を返す
- `$weather list` `$天気 list`: 指定可能な地域の一覧を返す
- [weather.py](https://github.com/pyconjp/pyconjpbot/blob/master/pyconjpbot/plugins/weather.py)

### misc plugin

- `$helps`: ヘルプへのリンクを返す
- `$shuffle spam ham eggs`: 指定された単語をシャッフルした結果を返す
- `$choice spam ham eggs`: 指定された単語から一つをランダムに選んで返す
- [misc.py](https://github.com/pyconjp/pyconjpbot/blob/master/pyconjpbot/plugins/misc.py)

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
