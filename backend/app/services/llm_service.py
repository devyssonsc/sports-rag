import os

from together import Together


class LLMService:

    MODEL_NAME = "openai/gpt-oss-120b"

    def __init__(self):

        self.client = Together(
            api_key=os.getenv("TOGETHER_API_KEY")
        )

    def generate(
        self,
        prompt: str,
    ) -> str:

        response = self.client.chat.completions.create(
            model=self.MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        return response.choices[0].message.content