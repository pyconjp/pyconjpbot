# google_plugins の利用手順

* google_plugins にあるbotコマンドは、各種 Google API を使用するため、Google API を bot から利用できるように、事前準備が必要です

## 1. Dicrectory API を有効にする

1. [Google API Console](https://console.developers.google.com/apis/api) を開く
2. 「プロジェクトを作成」→ `pyconjpbot` などを指定して「作成」
3. 「APIを有効にする」を選択し、以下のAPIを検索して有効にする

  - `Google Drive API`
  - `Google Calendar API`
  - `Admin SDK`

4. 「認証情報」メニュー→「OAuth同意画面」タブ→以下を入力して「保存」

    メールアドレス: 自分のメールアドレス
    ユーザーに表示するサービス名: `pyconjpbot`

5. 「認証情報を作成」→「OAuth クライアント ID」→「その他」を選択→名前に `pyconjpbot` などを指定して「作成」
6. OAuth クライアント IDがダイアログで表示されるので「OK」をクリックして閉じる
7. 右端のダウンロードボタンをクリックして、 `client_secret_XXXX.json` をダウンロードする
8. ファイル名を `client_secret.json` に変更して、 `pyconjpbot/google_plugins/` に置く

## 2. credentials を生成

- 下記の手順で `google_api.py` を実行すると、ブラウザが開いて API の許可を求めます
- PyCon JP の Google アカウントで API を許可します
- 成功すると `credentials.json` という証明書ファイルが生成されます

```
$ . env/bin/activate
(env) $ cd pyconjpbot/google_plugin
(env) $ python google_api.py
(env) $ ls credentials.json
credentials.json
```
