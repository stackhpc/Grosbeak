import subprocess
import os
import json
from slack_sdk.webhook import WebhookClient
from slack_sdk.web import WebClient
import traceback
import statistics
from datetime import datetime
import matplotlib.pyplot
import matplotlib.dates

#This script generates the daily summary for Slack 

#METRICS
# total runs
# number succeeded 
# failures 
# avg start time
# avg ssh time 
# exponential moving average - slowest times of the day 

LOG_FILE = os.environ.get('LOG_FILE', './healthmon.log')
URL = os.environ.get('DAILY_WEBHOOK_URL', 'Default')
USER_TOKEN = os.environ.get('USER_TOKEN', 'Default')
SELECTED = os.environ.get('IMAGE_FOR_GRAPHING', 'Ubuntu-22.04')
FIG_NAME = "foo.png"

def smooth(scalars, weight):  # Weight between 0 and 1
    last = scalars[0]  # First value in the plot (first timestep)
    smoothed = list()
    for point in scalars:
        smoothed_val = last * weight + (1 - weight) * point  # Calculate smoothed value
        smoothed.append(smoothed_val)                        # Save it
        last = smoothed_val                                  # Anchor the last smoothed value

    return smoothed

with open(LOG_FILE,'r+') as f:
    try: 
        f = f.readlines()
        f = list(map(json.loads,f))


        today = datetime.now().date()

        #selecting todays date
        f = [log for log in f if datetime.strptime(log['time'],"%Y-%m-%d %H:%M:%S").date()==today] 

        print("Total Runs:",len(f))

        success = len([log for log in f if log['success'] is True])
        print("Successful Runs:", success)
        # failures 
        print("Failed Runs:", len(f)-success)
        # avg start time
        start_time = [log['time_to_start'] for log in f]
        print("Avg Time to READY: {:.2f}".format(statistics.fmean(start_time)))
        # avg ssh time 
        ssh_time = [ log['time_to_ssh'] for log in f if log['image']==SELECTED ]
        print("Avg Time to SSH: {:.2f}".format(statistics.fmean(ssh_time)))

        #creating graph to plot average time to READY/SSH over the day 
        matplotlib.pyplot.figure(figsize=(4,3))

        smoothed = smooth(start_time,0.6)
        times = [ datetime.strptime(log['time'],"%Y-%m-%d %H:%M:%S") for log in f ]
        matplotlib.pyplot.plot_date(times, smoothed,'b', label='To READY')

        times2 = [datetime.strptime(log['time'],"%Y-%m-%d %H:%M:%S") for log in f if log['image']==SELECTED ]
        smoothed2 = smooth(ssh_time,0.6)
        matplotlib.pyplot.plot_date(times2, smoothed2,'r', label='To SSH Access')

        matplotlib.pyplot.gca().xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%H:%M'))
        matplotlib.pyplot.xlabel('Time of Day')
        matplotlib.pyplot.ylabel('Time (Seconds)')
        matplotlib.pyplot.legend()
        matplotlib.pyplot.xticks(rotation=45)
        matplotlib.pyplot.tight_layout()

        matplotlib.pyplot.savefig(FIG_NAME)

        #uploading graph to slack 
        webclient = WebClient(USER_TOKEN)

        new_file = webclient.files_upload_v2(
                        title=FIG_NAME,
                        filename=FIG_NAME,
                        file=FIG_NAME,
                    )

        new_file = dict(new_file.get('files')[0])

        #setting file url to public
        new_file = webclient.files_sharedPublicURL(file=new_file['id'])

        #building image url 
        new_file = new_file.get('file')['permalink_public']

        location = new_file.rsplit("/",1)[1]

        permalink, pubkey = location.rsplit('-',1)

        image_url = "https://files.slack.com/files-pri/"+permalink+"/"+FIG_NAME+"?pub_secret="+pubkey

        print(image_url)

        #Slack message
        blocks=[
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Daily Summary"
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
                        "image_url": "https://cdn-icons-png.flaticon.com/512/1383/1383395.png",
                        "alt_text": "total: "
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*total:* "+str(len(f))
                    },
                    {
                        "type": "image",
                        "image_url": "https://cdn-icons-png.flaticon.com/512/463/463574.png",
                        "alt_text": "success: "
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*success:* "+str(success)
                    },
                    {
                        "type": "image",
                        "image_url": "https://cdn-icons-png.flaticon.com/512/399/399274.png",
                        "alt_text": "failure: "
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*failure:* "+str(len(f)-success)
                    },
                    {
                        "type": "image",
                        "image_url": "https://cdn-icons-png.flaticon.com/512/850/850960.png",
                        "alt_text": "time: "
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*avg READY:* "+"{:.2f}".format(statistics.fmean(start_time))+"s"
                    }
                ]
            },
            {
                "type": "image",
                "block_id": "image4",
                "image_url": image_url,
                "alt_text": "An incredibly cute kitten."
            }
        ]

        #post slack message
        webhook = WebhookClient(URL)
        response = webhook.send(
            text="Daily Summary",
            blocks=blocks
        )
        
        try:
            assert response.status_code == 200
        except:
            print("slack webhook failed with response:",response.body)

    except:
        print(traceback.format_exc())