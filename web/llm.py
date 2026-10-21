from dotenv import load_dotenv
from openai import AsyncOpenAI
from pathlib import Path
import os

env_dir=Path(__file__).parent.parent / ".env"
load_dotenv(env_dir)
client=AsyncOpenAI(api_key=os.getenv("API_KEY"),base_url="https://tokenhub.tencentmaas.com/v1")