import os

from together import Together
from dotenv import load_dotenv

load_dotenv()

client = Together(
    api_key=os.getenv("TOGETHER_API_KEY")
)

response = client.embeddings.create(
    model="intfloat/multilingual-e5-large-instruct",
    input="Lionel Messi scored two goals against Brazil."
)

embedding = response.data[0].embedding

print(f"Dimensions: {len(embedding)}")
print("First 10 values:")
print(embedding[:10])