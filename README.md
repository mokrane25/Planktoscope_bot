# PlanktoBot
PlanktoBot is a Slack bot specialised in PlanktoScopes produced by FairScope

The main aim of this project is to make and deploy a bot that uses Fairscope documentation and answers questions concerning PlanktoScope from clients in a dedicated Slack channel. 


### .env ###
A file to store all the environment variables. This is a way to centralize these variables and improve performance and security.


## RAG - Retrieval Augmented Generation : ##
##### langchain.py #####
- Loading data from given websites 
- Split this content into chunks
- store them in Faiss vectores
- Create vector embeddings using Faiss (langchain library) & OpenAi embedding model
- Store evrything in a file named "faiss_store_openai.pkl"
##### lgc_pinecone.py #####
- Same as langchain.py except storage of data
- Data stored in Pinecone database
##### webAgent.py #####
- A langchain agent is used to make internet search to answer questions 
- Note : unlike `langchain.py` this code provides answer without the source
- The file `lgc_web.py` is just a variant of the `webAgent.py` 


## slack_bot : ##
##### bot_main.py #####
- Listening to event in a specific channel in a slack workspace (PlanktoScope)
- Answering the user in a thread under his message 
##### langchain_bot.py #####
- Same as bot_main.py but with a LLM (gpt-4) response using Langchain
- Uses the file `faiss_store_openai.pkl` as a database where PlanktoScope documentation is stored, and serves as a training base for the LLM used (gpt-4 in our case), then the LLM answers the question through Langchain and then posted in the Slack channel
##### webAgent_bot.py #####
- Same as bot_main.py but with a langchain agent "web agent" which answers by doing a google search 
##### data.json #####
- In this file we store the timestamp of each message sent in a particular slack channel, it helps to keep track of threads opened by the bot under a client's message so the bot can answer any question any time and not only the last one.
- It is used by the 3 bots 









