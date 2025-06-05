#  ____    ____   ____ 
# |    \  /    | /    |
# |  D  )|  o  ||   __|
# |    / |     ||  |  |
# |    \ |  _  ||  |_ |
# |  .  \|  |  ||     |
# |__|\_||__|__||___,_|
# RETRIEVAL AUGMENTED GENERATION 
                                                                                   
# IDEA : we retrieve relevant information from an external knowledge base (PlantoScope Documentation) 
# and give that knowledge base to a LLM (gpt-4) using Langchain

## USING PINECONE & LANGCHAIN TO BUILD A CHATBOT
# https://docs.pinecone.io/docs/langchain
# https://docs.pinecone.io/docs/openai

# LangChain - a framework that makes it easier to assemble the components to build a chatbot
# Pinecone - a 'vectorstore' to store your documents in number 'vectors'

'______________________________________________________________________________________________________________________'

#pip install -qU langchain==0.0.162 openai tiktoken "pinecone-client[grpc]" datasets apache_beam mwparserfromhell
#pip install langchain openai pinecone-client requests beautifulsoup4 tiktoken python-dotenv
# made with langchain==0.0162 & openai==0.28.1


from dotenv import load_dotenv
import os

env_path = os.path.join(os.path.dirname(__file__), '..', '.env') 	# Relative path to .env file
load_dotenv(env_path)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")



############## EXTARCT DESIRED URLS FROM HTML #################################
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def get_urls(base_url):
  
  # Initialize a list to store the extracted URLs
  #urls_doc = []

  # Initialize a set to store the extracted URLs + remove duplicates
  urls_set = set()

  # Send an HTTP GET request to the base URL
  response = requests.get(base_url)

  # Check if the request was successful
  if response.status_code == 200:
    # Parse the HTML content of the webpage using BeautifulSoup
    soup = BeautifulSoup(response.text, "html.parser")

    # Find all anchor tags (links, hyperlinks) in the HTML
    links = soup.find_all("a")

    # Extract and append the href attribute from each link to the list
    for link in links:
        href = link.get("href")
        if href is not None:
            # Create an absolute URL by joining the base URL with the relative URL
            absolute_url = urljoin(base_url, href)

            #urls_doc.append(absolute_url)
            urls_set.add(absolute_url)

  # Filter the list to keep only URLs with the base URL
  #filtered_urls = [url for url in urls_doc if url.startswith(base_url)]
  #filtered_urls = [url for url in list(urls_set) if url.startswith(base_url)]
  return list(urls_set)

base_url1 = "https://www.planktoscope.org/discover"
filtered_urls1 = get_urls(base_url1)

base_url2 = "https://docs.planktoscope.community/"
filtered_urls2 = get_urls(base_url2)

base_url3 = "https://planktoscope.readthedocs.io/en/latest/"
filtered_urls3 = get_urls(base_url3)

filtered_urls = filtered_urls1 + filtered_urls2 + filtered_urls3

#print("number of fetched urls : ")
#print(len(filtered_urls1), len(filtered_urls2), len(filtered_urls3), len(filtered_urls))



############## LOADING DATA FROM URLS #################################
 # 2 urls/second
# pip show numpy
# pip install numpy==1.25.0
# pip install --upgrade apache-beam

from langchain.document_loaders import WebBaseLoader
loader = WebBaseLoader(filtered_urls3)
data = loader.load() 



############## FUNCTION TO CALCULATE THE EQUIVALENT NUMBER OF TOKENS ####################
import tiktoken

# tokenizer_name = tiktoken.encoding_for_model('gpt-4')   #tokenizer_name = <Encoding 'cl100k_base'>
# tokenizer = tiktoken.get_encoding(tokenizer_name.name)

tokenizer = tiktoken.get_encoding('cl100k_base')
# create the length function
def tiktoken_len(text):
    tokens = tokenizer.encode(
        text,
        disallowed_special=()
    )
    return len(tokens)
  


############## BUILDING THE KNOWLEDGE BASE #################################
# SPLITING DATA INTO SMALL CHUNKS
# chunking the extracted text into more "concise" chunks to later be embedding and stored in a Pinecone vector database
from langchain.text_splitter import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1400,
    chunk_overlap=150,
    length_function=tiktoken_len,
    separators=["\n\n", "\n", " ", ""]
)

chunks = text_splitter.split_documents(data)



############## CREATING EMBEDDINGS #################################
# from langchain.vectorstores import Pinecone  # https://docs.pinecone.io/docs/overview
# from langchain.embeddings import OpenAIEmbeddings

from langchain.embeddings.openai import OpenAIEmbeddings 
embed = OpenAIEmbeddings(model='text-embedding-ada-002', openai_api_key=OPENAI_API_KEY)
chunks_text = [chunks[i].page_content for i in range(len(chunks))]
embeddings = embed.embed_documents(chunks_text)
print("embeddings dimensions : ")
print(len(embeddings), len(embeddings[0]))



############## PINECONE-VECTOR DATABASE #################################
import pinecone
import time 

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")  # find API key in console at app.pinecone.io
PINECONE_ENV = os.getenv("PINECONE_ENV")  # find ENV (cloud region) next to API key in console
pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
# pinecone.whoami()

index_name = 'langchain-retrieval-augmentation'
if index_name not in pinecone.list_indexes():
    # we create a new index
    pinecone.create_index(
        name=index_name,
        metric='cosine',
        dimension=len(embeddings[0])  # second dim of text-embedding-ada-002
    )
    # wait for index to be initialized
    while not pinecone.describe_index(index_name).status['ready']:
        time.sleep(1)
        
        
#index = pinecone.GRPCIndex(index_name)
index = pinecone.Index(index_name)
print(index.describe_index_stats())  #check that the number of vectors in our index = 0 because we haven't added any vector yet



############## INDEXING #################################
# add vectors to the Pinecone index

# The indexing task will be performed (in batches of 100 or more) 
# using the Pinecone python client rather (much faster than the LangChain vector store object)

# print(data)
# data = [Document(page_content='text...', metadata={'source': 'https://...', 'title': 'Collection devices - PlanktoScope', 'language': 'en'})]


from tqdm.auto import tqdm
from uuid import uuid4

batch_limit = 100

texts = []
metadatas = []

for i, record in enumerate(tqdm(data)):
    # first get metadata fields for this record
    metadata = {
        'id': str(uuid4()),  # Update with an appropriate ID generation for your use case
        'source': record.metadata.get('source', ''),
        'title': record.metadata.get('title', '')
    }
    # now we create chunks from the document text
    record_texts = text_splitter.split_text(record.page_content)
    # create individual metadata dicts for each chunk
    record_metadatas = [{
        "chunk": j, "text": text, **metadata
    } for j, text in enumerate(record_texts)]
    # append these to current batches
    texts.extend(record_texts)
    metadatas.extend(record_metadatas)
    # if we have reached the batch_limit we can add texts
    if len(texts) >= batch_limit:
        ids = [str(uuid4()) for _ in range(len(texts))]
        embeds = embed.embed_documents(texts)
        index.upsert(vectors=zip(ids, embeds, metadatas))
        texts = []
        metadatas = []

if len(texts) > 0:
    ids = [str(uuid4()) for _ in range(len(texts))]
    embeds = embed.embed_documents(texts)
    index.upsert(vectors=zip(ids, embeds, metadatas))
    
# check the number of vectors in our index    
print(index.describe_index_stats())



############## CREATING A VECTOR STORE AND QUERING #################################
#switch back to LangChain to initialize a vectore store using the index we just created

from langchain.vectorstores import Pinecone

# switch back to normal index for langchain
index = pinecone.Index(index_name)
query = "What is a Planktoscope?"
text_field = "text"


vectorStore = Pinecone(index, embeddings.embed_query, text_field)
#vectorStore = Pinecone(index, embed, text_field)



############## GENERATIVE QUESTION ANSWERING #################################
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQAWithSourcesChain

#GPT-4 can process up to 25,000 words – about eight times as many as GPT-3 – handle much more nuanced instructions than GPT-3.5
llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model_name='gpt-4', temperature=0.0)
#create a chain
qa_with_sources = RetrievalQAWithSourcesChain.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorStore.as_retriever()
)

question = "What is a Planktoscope?"
response = qa_with_sources({"question": question})
print (response)


############## DELETE INDEX TO SAVE RESSOURCES #################################
pinecone.delete_index(index_name)     
