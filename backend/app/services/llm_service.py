import os

from together import AsyncTogether


class LLMService:

    MODEL_NAME = "openai/gpt-oss-120b"

    def __init__(self):

        self.client = AsyncTogether(
            api_key=os.getenv("TOGETHER_API_KEY")
        )

    async def generate(
        self,
        prompt: str,
    ) -> str:

        response = await self.client.chat.completions.create(
            model=self.MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        return response.choices[0].message.content
