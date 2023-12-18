import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import pickle
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.chains.question_answering import load_qa_chain
from langchain.chat_models import ChatOpenAI
import time
import json
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
SLACK_TOKEN = os.getenv("SLACK_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
BOT_ID = os.getenv("BOT_ID")

client = WebClient(token=SLACK_TOKEN)

def listen_to_channel(channel_id):
    try:
        result = client.conversations_history(channel=channel_id, limit=1)
        messages = result.get("messages", [])

        if messages:
            message = messages[0]
            user = message.get("user")
            message_ts = message.get("ts")

            if "thread_ts" in message:
                thread_ts = message["thread_ts"]
                return message.get("text", ""), user, message_ts, thread_ts, result

            return message.get("text", ""), user, message_ts, None, result

    except SlackApiError as e:
        print(f"Error: {e.response['error']}")
        return None, None, None, None, None

def get_last_message_in_thread(channel_id, parent_ts):
    try:
        result = client.conversations_replies(channel=channel_id, ts=parent_ts)
        replies = result.get("messages", [])

        if replies:
            sorted_replies = sorted(replies, key=lambda x: float(x.get("ts", 0)), reverse=True)
            last_reply = sorted_replies[0]
            last_message = last_reply.get("text", "")
            user = last_reply.get("user", "")
            message_ts = last_reply.get("ts", "")

            return last_message, user, message_ts, result

    except SlackApiError as e:
        print(f"Error: {e.response['error']}")
        return None, None, None, None

def send_message(channel_id, message, message_ts):
    try:
        result = client.chat_postMessage(channel=channel_id, text=message, thread_ts=message_ts)
    except SlackApiError as e:
        print(f"Error: {e.response['error']}")



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



if __name__ == "__main__":
    running = True

    while running:
        try:
            current_message, user, message_ts, thread_ts, result = listen_to_channel(CHANNEL_ID)

            if user != BOT_ID and result:
                message_blocks = result[0].get("blocks", [])
                
                if message_blocks:
                    elements = message_blocks[0].get("elements", [])
                    
                    if elements:
                        user_id = elements[0].get("user_id")
                        
                        if user_id == BOT_ID:
                            with open('data.json', 'r') as file:
                                data = json.load(file)
                            data[message_ts] = ''
                            
                            with open('data.json', 'w') as file:
                                json.dump(data, file, indent=0)
                                
                            send_message(CHANNEL_ID, f"Hi <@{user}>! Let me think ... ", message_ts)
                            response = agent(current_message)['output']
                            send_message(CHANNEL_ID, response, message_ts)

            # ... (le reste du code)

            time.sleep(1)  # Sleep to avoid hitting rate limits

        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(10)  # Sleep longer if an error occurs
