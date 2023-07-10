import logging
#import heapq as hq
from datetime import datetime, timedelta
import sched
import time

logger = logging.getLogger('gptBot-LoggerTest')
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler('gptBot_TestLog.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

class Bot:

    BASEERRORMESSAGE = "Sorry, there seems to be an issue. An issue report has been created. You do not have to do anything at this time."

    prompt_Count = 25
    exclusive_Channel = 'chatgpt'
    active_Session = False
    session_StartTime, session_endTime = None, None
    start_Time, end_Time = None, None

    def __init__(self, client) -> None:
        self.client = client
        self.channelMembers, self.memberCount = self.getChannelMembers()
    
    def reducePromptCount(self, reduce_Prompt_Count, memUsed) -> None:
        if not self.active_Session:
            self.timer_on()

        if reduce_Prompt_Count > self.prompt_Count or self.prompt_Count == 0:
            self.prompt_Count = 0
        else:    
            self.prompt_Count -= reduce_Prompt_Count
            self.channelMembers[memUsed] -= reduce_Prompt_Count
    def addReaction(self, channel, timestamp, name) -> None:
        response = self.client.reactions_add(
            channel=channel, timestamp=timestamp, name=name
        )
        if not response['ok']:
            self.client.chat_postMessage(
                channel=self.exclusive_Channel, text=self.BASEERRORMESSAGE
            )
            logger.info("Failed to add reaction.")

    def timer_on(self) -> None:
        self.active_Session = True
        self.session_StartTime = datetime.now()
        self.start_Time = time.time()
        self.session_endTime = self.session_StartTime + timedelta(hours=3)
        self.end_Time = self.start_Time + 10800

        scheduler = sched.scheduler(time.time, time.sleep)
        scheduler.enterabs(self.end_Time, 1, self.timer_off, ())
        scheduler.run()
    def timer_off(self) -> None:
        self.active_Session = False
        self.prompt_Count = 25
        self.session_StartTime, self.session_endTime = None, None
        self.start_Time, self.endTime = None, None
        self.client.chat_postMessage(channel=self.exclusive_Channel,text=f'GPT-4 Prompts have been reset.')
    def remainingTime(self):
        timeUnit = ['hour(s)', 'minute(s)', 'second(s)']
        timeLeft = self.session_endTime - datetime.now()
        strVer = str(timeLeft).split(":")
        for i in range(3):
            if float(strVer[i]) != 0.0:
                strVer[i] = str(round(float(strVer[i]))) + " " + timeUnit[i]
        return ' '.join(strVer)
    def remTime(self) -> None:
        if not self.active_Session:
            self.client.chat_postMessage(channel=self.exclusive_Channel,text='No prompts have been used, so there is no active session going on right now.')
            return
        self.client.chat_postMessage(channel=self.exclusive_Channel,text=f"Prompts will reset in {self.remainingTime()}.")
    def remainingMessages(self):
        if(self.prompt_Count==0):
            self.client.chat_postMessage(channel=self.exclusive_Channel,text=f'All prompts have been used for this period. Reset will occur in {self.remainingTime()}.')
        else:
            self.client.chat_postMessage(channel=self.exclusive_Channel,text=f'{self.prompt_Count} messages remaining for this period.')
    def getUsageStats(self) -> None:
        if not self.active_Session:
            self.client.chat_postMessage(channel=self.exclusive_Channel,text='There is no active session right now. No prompts have been used.')
            return
        statString = "Prompt Usage:\n"
        tempMems = list(self.channelMembers.keys())
        for mem in range(self.memberCount):
            if mem == self.memberCount-1:
                statString += "\t-" + tempMems[mem] + ": " + str(abs(self.channelMembers[tempMems[mem]]))
            else:
                statString += "\t-" + tempMems[mem] + ": " + str(abs(self.channelMembers[tempMems[mem]])) +"\n"
        self.client.chat_postMessage(channel=self.exclusive_Channel,text=statString)
    def addMember(self, member) -> None:
        self.channelMembers[member] = 0
        self.memberCount += 1
    def remMember(self, member) -> None:
        del self.channelMembers[member]
        self.memberCount -= 1
    def getChannelMembers(self):
        response = self.client.conversations_members(channel='C05AMLCUE3E')
        if response['ok']:
            numMembers = 0
            member_ids = response['members']
            usernames = {}
            for member_id in member_ids:
                user_response = self.client.users_info(user=member_id)
                if user_response['ok']:
                    numMembers += 1
                    user = user_response['user']
                    usernames[user['name']] = 0
            return [usernames, numMembers]
        else:
            logger.info("Failed to retrieve channel members. Error: ", response['error'])
            return []
    def appHelp(self):
        message = """
        GPT-Bot helps track the number of remaining GPT-4 prompts for the Biomechanics group (as of June 2023 the limit is 25 per 3 hours). GPT-Bot also provides alerts and information about remaining time/prompts. You can query the bot with the following commands:

        • *@gptbot* \*prompts used\*: Tells the bot how many prompts you used (Honor Code). The bot will count them against the 25 prompt limit.
        • *@gptbot remprompts*: Returns how many of the 25 prompts are remaining for the current 3-hour period
        • *@gptbot time*: Returns when the ongoing 3-hour window will end and the prompts will refresh.
        • *@gptbot stats*: Returns a breakdown of prompt usage in the ongoing 3-hour window (format: -member: prompts used-)
        • *@gptbot help*: Returns this help description.

        Misspelled/Unrecognized commands will be ignored.

        Additional Functions:
        - GPT-Bot will send automatic notifications when there are 5 prompts remaining and 0 prompts remaining.
        - GPT-Bot will send an automatic notification when a 3-hour window ends and prompts are reset.
        - GPT-Bot will react to the *prompts used* command with an emoji to indicate that it successfully counted your used prompts
        """
        try:
            self.client.chat_postMessage(channel=self.exclusive_Channel,text=message)
        except:
            self.client.chat_postMessage(channel=self.exclusive_Channel,text=self.BASEERRORMESSAGE)
            logger.info("Error producing message from 'help' command.")