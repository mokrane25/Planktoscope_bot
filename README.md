# Planktoscope_Bot
Planktoscope_Bot is a Slack bot specialised in PlanktoScopes, main product of FairScope

The main aim of this project is to make and deploy a bot that uses Fairscope documentation and answers specific questions about the PlanktoScope from clients in a dedicated Slack channel. 


### RAG files
##### rag_lgc_faiss.py 
Basic implementation of RAG using LangChain framework :
- Loading data from given websites 
- Split this content into chunks
- Create vector embeddings using Faiss (langchain library) & OpenAi embedding model
- Store embedded vectors in `faiss_store_openai.pkl`
##### rag_lgc_pinecone.py #####
Same as `rag_lgc_faiss.py` except storage of data : documentation data is stored in Pinecone database

### Slack Bot
##### bot_web_agent.py 
- If the bot is tagged, it retrieves the last message from the channel, then sends a wait message before trying to reply (it gives threaded messages).
And for each active thread, it fetches the thread's last message and responds if necessary.
- The bot uses a `Langchain` web agent (able to browse the web) and a LLM (`gpt-4`-8k tokens or `gpt-4-1106-preview`-128k tokens) to produce an answer which passes through Langchain and then is posted in the Slack channel.
\n Check LangChain documentation at : https://python.langchain.com/docs/get_started/introduction 
##### bot_rag.py 
Same as `bot_web_agent.py` bbut instead of searching the web, it uses the RAG principle (retrieval augmented generation) where the file `faiss_store_openai.pkl` serves as a database where PlanktoScope documentation is stored, and serves as a source base for the LLM used (gpt-4 in our case), then the LLM answers the question (through Langchain) on a thread on Slack

### Other files 
##### .env 
A file to store all the environment variables to centralize them and improve security.
##### data.json 
This file is created as you run the agents, it serves to store the timestamp of each message sent in a particular slack channel, it helps to keep track of threads opened by the bot under a client's message so the bot can answer any question any time and not only the last one.
