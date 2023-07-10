import slack_sdk
import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request
from slackeventsapi import SlackEventAdapter
from Bot import Bot

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(os.environ['SIGNING_SECRET'],'/slack/events',app)

client = slack_sdk.WebClient(token=os.environ['SLACK_TOKEN'])

my_GPT_Bot = Bot(client)

@slack_event_adapter.on('app_mention')
def botRequest(payload):
    event = payload.get('event', {})
    user = event['user']
    message = event['text']
    timeStamp = event['event_ts']
    channel = event['channel']

    response = client.users_info(user=user)
    if response['ok']:
        user_name = response['user']['name']

    command = message.lower().strip().split()[1]

    if command.isdigit() and int(command) > 0:
        my_GPT_Bot.reducePromptCount(int(command), user_name)
        my_GPT_Bot.addReaction(channel=channel,timestamp=timeStamp,name='+1')
    elif command == "remprompts":
        my_GPT_Bot.remainingMessages()
    elif command == "time":
        my_GPT_Bot.remTime()
    elif command == "stats":
        my_GPT_Bot.getUsageStats()
    elif command =='help':
        my_GPT_Bot.appHelp()
    
@slack_event_adapter.on('member_joined_channel')
def newMember(eventData):
    event = eventData['event']
    user = event['user']
    my_GPT_Bot.addMember(user)

@slack_event_adapter.on('member_left_channel')
def remMember(eventData):
    event = eventData['event']
    user = event['user']
    my_GPT_Bot.remMember(user)

@app.route('/slack/events', methods=['POST'])
def slack_events():
    slack_event_adapter.start(port=5000)
    slack_event_adapter.process_event(request.get_json())
    return 'OK'
    
if __name__ == "__main__":
    app.run(debug=True)