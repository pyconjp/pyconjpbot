import google_api_tool

SCOPES = 'https://www.googleapis.com/auth/drive.metadata.readonly'

def main():
    """
    Google Drive APIを認証して使用できるようにする
    """
    service = google_api_tool.get_service('drive', 'v3', __file__, SCOPES)

    results = service.files().list(
        pageSize=10,fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])
    if not items:
        print('No files found.')
    else:
        print('Files:')
        for item in items:
            print('{0} ({1})'.format(item['name'], item['id']))

if __name__ == '__main__':
    main()
