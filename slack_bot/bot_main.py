############# BOT IMPORTS ###########################
import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

############# AI IMPORTS ###########################
import pickle
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.chains.question_answering import load_qa_chain
from langchain.chat_models import ChatOpenAI
import time
import json

############# SETTINGS ###########################
from dotenv import load_dotenv
import os
env_path = os.path.join(os.path.dirname(__file__), '..', '.env') 	# Relative path to .env file
load_dotenv(env_path)

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
SLACK_TOKEN = os.getenv("SLACK_TOKEN")
CHANNEL_ID= os.getenv("CHANNEL_ID")
BOT_ID = os.getenv("BOT_ID")

client = WebClient(token= SLACK_TOKEN)
file_path = os.environ.get("DATA_JSON_PATH", "data.json")   #retrieves the value associated with "DATA_JSON_PATH" in the .env file, Otherwise it returns "data.json"

############# LISTEN TO MESSAGES IN A CHANNEL ###########################
def listen_to_channel(channel_id):
    # Get the last message in the channel
    result = client.conversations_history(channel=channel_id, limit=1)
    last_message = result["messages"][0]["text"]
    user = result["messages"][0]["user"]
    message_ts = result["messages"][0]["ts"]

    # Check if the message is part of a thread
    if 'thread_ts' in result["messages"][0]:
        thread_ts = result["messages"][0]["thread_ts"]
        return last_message, user, message_ts, thread_ts, result

    return last_message, user, message_ts, None, result 

def listen_to_thread(channel_id, thread_ts):
    # Get the last message in the specified thread
    result = client.conversations_replies(channel=channel_id, ts=thread_ts, limit=1)
    
    # Check if there are replies in the thread
    if result["messages"]:
        last_message = result["messages"][0]["text"]
        user = result["messages"][0]["user"]
        message_ts = result["messages"][0]["ts"]
        return last_message, user, message_ts, result
    
    # If there are no replies, return None
    return None, None, None, result

def get_last_message_in_thread(channel_id, parent_ts):
    result = client.conversations_replies(channel=channel_id, ts=parent_ts)
    replies = result.get("messages", [])

    # Sort replies by timestamp in descending order
    sorted_replies = sorted(replies, key=lambda x: float(x.get("ts", 0)), reverse=True)

    # Get the information of the latest reply
    last_reply = sorted_replies[0]
    last_message = last_reply.get("text", "")
    user = last_reply.get("user", "")
    message_ts = last_reply.get("ts", "")

    return last_message, user, message_ts, result

def send_message(channel_id, message, message_ts):
    try:
        result = client.chat_postMessage(channel=channel_id, text=message, thread_ts=message_ts)
    except SlackApiError as e:
        print(f"Error: {e.response['error']}")


############# CREATE A THREAD & SEND MESSAGE ###########################

# Open the JSON file and load the data
with open(file_path, 'r') as file:
    data = json.load(file)
    
if __name__ == "__main__":
    running = True
    current_message, user, message_ts, thread_ts, result = listen_to_channel(CHANNEL_ID)
    
    while running:
        try:
            current_message, user, message_ts, thread_ts, result = listen_to_channel(CHANNEL_ID)
            last_message, user, last_message_ts, result = get_last_message_in_thread(CHANNEL_ID, message_ts) 
          
            # Process new message
            if user != BOT_ID:
                if result['messages'][0]['blocks'][0]['elements'][0]['elements'][0]['user_id'] == BOT_ID :
                    with open('data.json', 'r') as file:
                        data = json.load(file)
                    data[message_ts]=''
                    with open('data.json', 'w') as file:
                        json.dump(data, file, indent=0)
                    send_message(CHANNEL_ID, f"Hi <@{user}>! Let me think ... ", message_ts)

            # Check each active thread for new messages
            # Process the message in the thread
            for active_thread in data.keys():
                last_message, thread_user, last_message_ts, result = get_last_message_in_thread(CHANNEL_ID, active_thread)
                if thread_user != BOT_ID:
                    if result['messages'][0]['blocks'][0]['elements'][0]['elements'][0]['user_id'] == BOT_ID :
                    
                        send_message(CHANNEL_ID, f"Hi <@{user}>! Let me think ... ", active_thread)

            # Optional: Clean up old threads from active_threads set
            # Example: Remove threads older than 1 hour or one month
            # active_threads = {t for t in active_threads if time.time() - t < 3600}

            time.sleep(1)  # Sleep to avoid hitting rate limits

        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(10)  # Sleep longer if an error occurs

