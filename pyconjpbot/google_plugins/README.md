# gadmin.py の利用手順

- gadmin_client_secret.json を取得する
- 参考: [Python Quickstart](https://developers.google.com/admin-sdk/directory/v1/quickstart/python?hl=ja&amp;authuser=2 "Python Quickstart  |  Directory API  |  Google Developers")

## 1. Dicrectory API を有効にする

1. https://console.developers.google.com/start/api?id=admin&hl=ja にアクセス
    「続行」→「認証情報に進む」
2. 「プロジェクトへの認証情報の追加」ページで「キャンセル」をクリック
3. 「OAuth同意画面」タブを選択でメールアドレスとサービス名を指定して「保存」
4. 「認証情報」タブで「認証情報を作成」→「OAuth クライアント ID」
5. 「アプリケーションの種類」で「その他」名前「pyconjpbot」を指定して「作成」
6. ダイアログで「OK」をクリック
7. 右端の下矢印をクリックして json をダウンロード
8. ダウンロードしたファイルを gadmin_client_secret.json にリネームする

## 2. `gadmin_quicksart.py` を実行する

```
(env)$ pip install -r ../requirements.txt
(env)$ python gadmin_client_secret.json
```

1. The sample will attempt to open a new window or tab in your default browser. If this fails, copy the URL from the console and manually open it in your browser.

   If you are not already logged into your Google account, you will be prompted to log in. If you are logged into multiple Google accounts, you will be asked to select one account to use for the authorization.

2. Click the Accept button.
3. The sample will proceed automatically, and you may close the window/tab.

## admin.google.com でAPIを有効にする

- [Enable API access in the Admin console - G Suite Administrator Help](https://support.google.com/a/answer/60757?hl=en "Enable API access in the Admin console - G Suite Administrator Help")
- Security > API reference
- Enable API accessをチェック
- Save