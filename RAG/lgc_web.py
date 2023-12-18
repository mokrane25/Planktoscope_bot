# https://python.langchain.com/docs/integrations/tools/google_search
# https://github.com/langchain-ai/langchain/issues/3091 
from dotenv import load_dotenv
import os

env_path = os.path.join(os.path.dirname(__file__),  '.env') 	# Relative path to .env file
load_dotenv(env_path)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")    # in the Google Cloud Console > Library > enable Custom Search API 
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")    # in the Google Programmable Search Engine

from langchain.tools import Tool
from langchain.utilities import GoogleSearchAPIWrapper

search = GoogleSearchAPIWrapper() # k=2 to set the number of results at 2

def top5_results(query):
    return search.results(query, 1)

tool = Tool(
    name="Google Search",
    description="Search Google for recent results, and give a concise and argumented answer.",
    func=search.run,
    # func=top5_results,
)

result = tool.run("what is the software that controls the Planktoscope?" )
print(result)


