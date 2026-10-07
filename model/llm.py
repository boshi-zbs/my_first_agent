from dotenv import load_dotenv
from openai import OpenAI
import os
from pathlib import Path
env_path=Path(__file__).parent.parent / ".env"
load_dotenv(env_path)
client=OpenAI(api_key=os.getenv("API_KEY"),base_url="https://tokenhub.tencentmaas.com/v1")