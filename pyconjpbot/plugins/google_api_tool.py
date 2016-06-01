import argparse
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import file
from oauth2client import tools

def get_service(name, version, filename, scope):
    """指定された Google API に接続する

    name: APIの名前
    version: APIのバージョン(通常 v3)
    file: ファイルの場所を指定する、通常 __file__ を使用する
    scope: OAuth のスコープを指定する

    serviceオブジェクトを返す
    """

    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()

    # Name of a file containing the OAuth 2.0 information for this
    # application, including client_id and client_secret, which are found
    # on the API Access tab on the Google APIs
    # Console <http://code.google.com/apis/console>.
    client_secrets = os.path.join(os.path.dirname(filename),
                                  'client_secrets.json')

    # Set up a Flow object to be used if we need to authenticate.
    flow = client.flow_from_clientsecrets(
        client_secrets,
        scope=scope,
        message=tools.message_if_missing(client_secrets))

    # Prepare credentials, and authorize HTTP object with them.
    # If the credentials don't exist or are invalid run through the native
    # client flow. The Storage object will ensure that if successful the good
    # credentials will get written back to a file.
    storagefile = os.path.join(os.path.dirname(filename),
                               name + '.dat')
    storage = file.Storage(storagefile)
    credentials = storage.get()
    if credentials is None or credentials.invalid:
        credentials = tools.run_flow(flow, storage, flags)
    http = credentials.authorize(http = httplib2.Http())

    service = discovery.build(name, version, http=http)
    return service
