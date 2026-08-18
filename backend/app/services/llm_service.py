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
        temperature: float | None = None,
    ) -> str:

        # ``temperature`` is only forwarded when provided, so the default
        # production behaviour (chat) stays byte-for-byte unchanged. The
        # evaluation harness passes ``temperature=0`` to make the LLM-as-a-judge
        # scoring as deterministic as possible.
        extra: dict = {}
        if temperature is not None:
            extra["temperature"] = temperature

        response = await self.client.chat.completions.create(
            model=self.MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            **extra,
        )

        return response.choices[0].message.content
