from dotenv import load_dotenv
import os

env_path = os.path.join(os.path.dirname(__file__), '..', '.env') 	# Relative path to .env file
load_dotenv(env_path)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

####### EXTARCT DESIRED URLS FROM HTML########

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

filtered_urls = filtered_urls1 + filtered_urls2
#print(len(filtered_urls1), len(filtered_urls2), len(filtered_urls))



from langchain.document_loaders import UnstructuredURLLoader
loaders = UnstructuredURLLoader(urls=filtered_urls)
data = loaders.load()


# Text Splitter
from langchain.text_splitter import CharacterTextSplitter
text_splitter = CharacterTextSplitter(separator='\n',
                                      chunk_size=1500,
                                      chunk_overlap=200)

chunks = text_splitter.split_documents(data)



#import faiss
import pickle
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(model='text-embedding-ada-002', openai_api_key=OPENAI_API_KEY)

vectorStore_openAI = FAISS.from_documents(chunks, embeddings)

with open("faiss_store_openai.pkl", "wb") as f:
    pickle.dump(vectorStore_openAI, f)
