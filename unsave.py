# unsave.py: Delete all saved posts from your reddit account.
# Optional: Write post links to a file before deleting.
# Note: This script may take several minutes to complete depending on
#       the number of saved posts.
# Modified OAuth flow from: https://medium.com/@nickpgott/how-to-login-to-a-reddit-account-with-praw-when-2fa-is-enabled-4db9e82448a5

import sys, random, webbrowser, socket, os
from praw import Reddit
from time import sleep
from datetime import datetime
from praw.models import Submission, Comment

# Wait for and then return a connected socket.
# Opens a TCP connection on port 8080, and waits for a single client.
def receive_connection():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('localhost', 8080))
    server.listen(1)
    client = server.accept()[0]
    server.close()
    return client

# Send message to client and close the connection.
def send_message(client, message):
    client.send('HTTP/1.1 200 OK\r\n\r\n{}'.format(message).encode('utf-8'))
    client.close()

def main():
    reddit = Reddit(client_id='pk5GUi9wM5Toxg4hejwq8w',
                    client_secret=None,
                    user_agent='unsaving posts',
                    redirect_uri='http://localhost:8080')
    scopes = ['identity', 'history', 'save']
    state = str(random.randint(0, 65000))
    url = reddit.auth.url(scopes=scopes,
                          state=state,
                          duration='permanent')

    print('-----',
          '\nAuthenticating with reddit')
    sleep(1)
    print('Make sure you are signed in to the correct account,',
          'then click "Allow" to continue',
          end='', flush=True)
    sleep(0.75)
    print('.', end='', flush=True)
    sleep(0.75)
    print('.', end='', flush=True)
    sleep(0.75)
    print('.', end='', flush=True)
    sleep(0.75)
    webbrowser.open(url)
    print('')

    client = receive_connection()
    data = client.recv(1024).decode('utf-8')
    param_tokens = data.split(' ', 2)[1].split('?', 1)[1].split('&')
    params = {key: value for (key, value) in [token.split('=') for token in param_tokens]}

    if state != params['state']:
        error = 'State mismatch. Expected: {}, Received: {}'.format(state, params['state'])
        print('ERROR:', error)
        send_message(client, error)
        return 1
    elif 'error' in params:
        error = params['error']
        print('ERROR:', error)
        send_message(client, error)
        return 1

    refresh_token = reddit.auth.authorize(params['code'])
    send_message(client, 'Refresh token: {}\n'.format(refresh_token) +
                         '------------------------------------------\n' +
                         '---- RETURN TO THE SCRIPT TO CONTINUE ----\n' +
                         '------------------------------------------')
    me = reddit.user.me()
    print('Logged in as:', str(me),
          '\n-----')

    proceed = '-_-'
    while proceed not in ('y', 'Y', 'n', 'N'):
        if proceed != '-_-':
            print('----- INVALID INPUT -----')
        print('WARNING: This script will delete all of your saved posts! Proceed? (y/N):', end=' ')
        proceed = input()

    if proceed in ('n', 'N'):
        print('----- EXITING SCRIPT -----')
        return 0
    print('-----')

    writeToFile = '-_-'
    while writeToFile not in ('y', 'Y', 'n', 'N'):
        if writeToFile != '-_-':
            print('----- INVALID INPUT -----')
        print('Write posts to a file before unsaving from reddit? (y/N):', end=' ')
        writeToFile = input()
    print('-----')

    print('Retrieving saved posts...\n' +
          '-----')
    savedLen = len(list(me.saved(limit=None)))
    if savedLen == 0:
        print('No saved posts to unsave!')
        print('----- EXITING SCRIPT -----')
        return 0

    wtf = False # write to file (alternatively, what the fuck)
    if writeToFile in ('y', 'Y'):
        wtf = True
        fileLoc = os.path.join(os.path.dirname(__file__),
                               'unsave_out/redditSaved_{}_{}.txt'.format(
                                   str(me), datetime.today().strftime('%Y%m%d')))
        os.makedirs(os.path.dirname(fileLoc), exist_ok=True)
        outFile = open(fileLoc, 'a')

    count = 0
    redditURL = 'https://reddit.com'
    # Keep running until no saved posts remain
    # (reddit returns 100 saved posts at a time)
    while savedLen > 0:
        for item in me.saved(limit=None):
            count += 1
            permalink = str(item.permalink)

            if wtf:
                outFile.write(redditURL + permalink + '\n')
            print('{:<4}:'.format(count), permalink)

            if isinstance(item, Submission):
                reddit.submission(str(item)).unsave()
            elif isinstance(item, Comment):
                reddit.comment(str(item)).unsave()
            else:
                continue

        print('-----\n' +
              'Retrieving next batch...\n' +
              '-----')
        savedLen = len(list(me.saved(limit=None)))

    print('No saved posts remain\n' +
          '-----')

    if wtf:
        print(count, 'link{} written to:'.format('' if count == 1 else 's'),
              str(fileLoc))
        outFile.close()

    print('----- DONE -----')
    return 0

if __name__ == '__main__':
    sys.exit(main())
