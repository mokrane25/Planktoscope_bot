# pip install google-api-python-client

################### IMPORTS ###########################
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import json
import time

################### SETTINGS ###########################
from dotenv import load_dotenv
import os
env_path = os.path.join(os.path.dirname(__file__), '..', '.env') 	# Relative path to .env file
load_dotenv(env_path)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SLACK_TOKEN = os.getenv("SLACK_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
BOT_ID = os.getenv("BOT_ID")

client = WebClient(token=SLACK_TOKEN)

################### LISTEN AND ANSWER TO SLACK MESSAGES ###########################
def post_message(channel_id, text, thread_ts=None):
    try:
        result = client.chat_postMessage(channel=channel_id, text=text, thread_ts=thread_ts)
    except SlackApiError as e:
        print(f"Error posting message: {e.response['error']}")

def listen_to_channel(channel_id):
    result = client.conversations_history(channel=channel_id, limit=1)
    last_message = result["messages"][0]["text"]
    user = result["messages"][0]["user"]
    message_ts = result["messages"][0]["ts"]

    if 'thread_ts' in result["messages"][0]:
        thread_ts = result["messages"][0]["thread_ts"]
        return last_message, user, message_ts, thread_ts, result

    return last_message, user, message_ts, None, result 

def listen_to_thread(channel_id, thread_ts):
    result = client.conversations_replies(channel=channel_id, ts=thread_ts, limit=1)
    
    if result["messages"]:
        last_message = result["messages"][0]["text"]
        user = result["messages"][0]["user"]
        message_ts = result["messages"][0]["ts"]
        return last_message, user, message_ts, result

    return None, None, None, result

def get_last_message_in_thread(channel_id, parent_ts):
    result = client.conversations_replies(channel=channel_id, ts=parent_ts)
    replies = result.get("messages", [])
    sorted_replies = sorted(replies, key=lambda x: float(x.get("ts", 0)), reverse=True)
    last_reply = sorted_replies[0]
    last_message = last_reply.get("text", "")
    user = last_reply.get("user", "")
    message_ts = last_reply.get("ts", "")

    return last_message, user, message_ts, result


####################### AGENT #################################
# pip install google-api-python-client>=2.100.0

from langchain.chat_models import ChatOpenAI
from langchain.agents import AgentType, Tool, initialize_agent
from langchain.agents import AgentType, initialize_agent, load_tools

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")    # in the Google Cloud Console > Library > enable Custom Search API 
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")      # in the Google Programmable Search Engine

llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model_name='gpt-4', temperature=0.0)
tool = load_tools(["google-search"], llm=llm, google_api_key=GOOGLE_API_KEY , google_cse_id=GOOGLE_CSE_ID)
agent = initialize_agent(tool, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, return_intermediate_steps=False)


######################### ALWAYS ANSWER INSIDE THREADS #########################################

#file_path = os.environ.get("DATA_JSON_PATH", "data.json")
script_directory = os.path.dirname(__file__) #path of executed file
data_file_path = os.path.join(script_directory, "data.json") #complete path of the .pkl file

with open(data_file_path, 'r') as file:
    data = json.load(file)
    
    
def main():
    running = True
    #data = {}  # Initialize data before entering the loop
    current_message, user, message_ts, thread_ts, result = listen_to_channel(CHANNEL_ID)
    
    while running:
        try:
            current_message, user, message_ts, thread_ts, result = listen_to_channel(CHANNEL_ID)
            last_message, user, last_message_ts, result = get_last_message_in_thread(CHANNEL_ID, message_ts)
            
            if user != BOT_ID and result['messages'][0]['blocks'][0]['elements'][0]['elements'][0]['user_id'] == BOT_ID:
                with open(data_file_path, 'r') as file:
                    data = json.load(file)
                data[message_ts] = ''
                with open(data_file_path, 'w') as file:
                    json.dump(data, file, indent=0)
                post_message(CHANNEL_ID, f"Hi <@{user}>!", active_thread)
                response = agent(last_message)['output']
                post_message(CHANNEL_ID, response, message_ts)

            for active_thread in data.keys():
                last_message, thread_user, last_message_ts, result = get_last_message_in_thread(CHANNEL_ID, active_thread)
                if thread_user != BOT_ID and result['messages'][0]['blocks'][0]['elements'][0]['elements'][0]['user_id'] == BOT_ID:
                    post_message(CHANNEL_ID, f"Hi <@{user}>!", active_thread)
                    response = agent(last_message)['output']
                    post_message(CHANNEL_ID, response, message_ts)
            time.sleep(1)

        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(10)


if __name__ == "__main__":
    main()
    