# PlanktoBot
PlanktoBot is a Slack bot specialised in PlanktoScopes produced by FairScope

##### .env #####
A file to store all the environment variables. This is a way to centralize these variables and improve performance and security.

##### RAG - Retrieval Augmented Generation #####
###### langchain.py ######
- Loading data from given websites 
- Split this content into chunks
- store them in Faiss vectores
- Create vector embeddings using Faiss (langchain library) & Open Ai embedding model
- Store evrything in a file named "faiss_store_openai.pkl"
###### lgc_pinecone.py ######
- Same as langchain.py except storage of data
- Data stored in Pinecone database
##### chains.py #####
- In this file the content of the file "faiss_store_openai.pkl" is loaded
- A question is submitted to gpt-4 using the RetrievalQAWithSourcesChain module of Langchain
- We get a reponse to the question and its source(s) (urls)

##### slack_bot #####
##### bot_main.py #####
- Listening to event in a specific channel in a slack workspace (PlanktoScope)
- Answering the user in a thread under his message 
##### langchain_bot.py #####
- Same as bot_main.py but with gpt response using Langchain
##### langchain_bot.py #####
- Same as bot_main.py but with a langchain agent "web agent" which answers by doing a google search 

##### data.json #####
used by the 3 bots to store messages timestamps to keep track of threads










