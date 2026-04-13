import os

from dotenv import load_dotenv, find_dotenv
from langchain_classic.chat_models import init_chat_model


load_dotenv(find_dotenv(), override=True)


llm=init_chat_model(
    model="glm-4.7",
    base_url=os.getenv("ZHIPU_BASE_URL"),
    api_key=os.getenv("ZHIPU_API_KEY"),
    model_provider="openai"
)


