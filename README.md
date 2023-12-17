# PlanktoBot
PlanktoBot is a Slack bot specialised in PlanktoScopes produced by FairScope


##### vect_store.py #####
- Loading data from given websites 
- Split this content into chunks
- store them in vectores
- Create vector embeddings using Faiss (langchain library) & Open Ai embedding model
- Store evrything in a file named "faiss_store_openai.pkl"

##### chains.py #####
- In this file the content of the file "faiss_store_openai.pkl" is loaded
- A question is submitted to gpt-4 using the RetrievalQAWithSourcesChain module of Langchain
- We get a reponse to the question and its source(s) (urls)

##### slack_bot.py #####
- Listening to event in a specific channel in a slack workspace (PlanktoScope)
- Answering the user in a thread under his question 

