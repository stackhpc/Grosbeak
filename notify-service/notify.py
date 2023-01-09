import subprocess
import os
import json
from slack_sdk.webhook import WebhookClient
import traceback

#This program is called by inotifywait in the shell script 'notifyjob' whenever a change is made to health monitors log file (generally /var/log/healthmon/healthmon.log)
#and posts an alert to slack if a build fails

LOG_FILE = os.environ.get('LOG_FILE', './healthmon.log')
OS_PROJECT_NAME= os.environ.get('OS_PROJECT_NAME', 'Default')

URL = os.environ.get('WEBHOOK_URL', 'Default')

#tail the log file
def get_last_log():
    try:
        f = subprocess.Popen(['tail','-n1',LOG_FILE],\
                stdout=subprocess.PIPE,stderr=subprocess.PIPE)

        line = f.stdout.readline()
        log = json.loads(line.decode("utf-8"))

        return log
    except:
        return "empty log file"

#post stack trace to text hosting website. TTL 24 hours
def pastie_get_url(content):

    payload = "language=plaintext&content={}".format(content)

    f = subprocess.Popen(
        ['curl',
        'http://pastie.org/pastes/create',
        '--data-raw',
        payload,
        '--compressed',
        '--insecure'],\
        stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    
    output = f.stdout.readline()
    
    f.communicate()

    assert(f.returncode==0)
    
    pastie_URL = "http://pastie.org" + output.decode("utf-8").split('Redirecting to ',1)[1]

    print(pastie_URL)

    return pastie_URL.strip()


log = get_last_log()

#log file empty, exit
#TODO: maybe post a warning to slack about empty log file/parsing error? something has gone wrong 

if type(log) == str:
    print(log)
    exit()

if log['success'] == False:
    #try to parse into nice message, else fallback on raw output 
    try:
        #parsing tempest error logs out of JSON object
        log_error, bootID = log['error'].split('Details: Fault: ',1)[1].split('. Server boot request ID:',1)
        log_error = log_error.replace('"','\\"')
        log_error = log_error.replace("'",'"')
        log_error = json.loads(log_error)

        details_URL = pastie_get_url(log_error['details'])

        #Slack message
        blocks=[
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "A server build has failed in project '"+OS_PROJECT_NAME+"'"
                }
		    },
            {
                "type": "divider"
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "image",
                        "image_url": "https://cdn-icons-png.flaticon.com/512/1687/1687561.png",
                        "alt_text": "image: "
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*"+log['image']+"*"
                    },
                    {
                        "type": "image",
                        "image_url": "https://cdn-icons-png.flaticon.com/512/3208/3208726.png",
                        "alt_text": "flavor: "
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*"+log['flavor']+"*"
                    },
                    {
                        "type": "image",
                        "image_url": "https://cdn-icons-png.flaticon.com/512/850/850960.png",
                        "alt_text": "datetime: "
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*"+log['time']+"*"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Server boot request ID:*"+bootID + "\n"
                    + "*Status Code:* " + str(log_error['code']) + "\n"
                    + "*Message:* " + log_error['message'] + "\n\n"
                    + "<{}|*Details*>".format(details_URL)
                }
		    }
        ]

    except:
        #fallback to raw output
        print(traceback.format_exc())

        details_URL = pastie_get_url(log['error'])

        blocks=[
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "A server build has failed in Project '"+OS_PROJECT_NAME+"'"
                }
		    },
            {
                "type": "divider"
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "image",
                        "image_url": "https://cdn-icons-png.flaticon.com/512/1687/1687561.png",
                        "alt_text": "image: "
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*"+log['image']+"*"
                    },
                    {
                        "type": "image",
                        "image_url": "https://cdn-icons-png.flaticon.com/512/3208/3208726.png",
                        "alt_text": "flavor: "
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*"+log['flavor']+"*"
                    },
                    {
                        "type": "image",
                        "image_url": "https://cdn-icons-png.flaticon.com/512/850/850960.png",
                        "alt_text": "datetime: "
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*"+log['time']+"*"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Warning:* there was an error in parsing the log file - falling back to raw output.  "  + "\n\n"
                    + "<{}|*Details*>".format(details_URL)
                }
		    }
        ]
    
    webhook = WebhookClient(URL)
    response = webhook.send(
        text="Server build failed!",
        blocks=blocks
    )

    try:
        assert response.status_code == 200
    except:
        print("slack webhook failed with response:",response.body)
