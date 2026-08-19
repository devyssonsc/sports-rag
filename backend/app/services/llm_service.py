import os

from together import AsyncTogether


class LLMService:

    # Production default (answer generation). The evaluation harness can point a
    # separate instance at a different model (e.g. an independent reasoning judge).
    MODEL_NAME = "openai/gpt-oss-120b"

    def __init__(self, model: str | None = None):

        self.model = model or self.MODEL_NAME

        self.client = AsyncTogether(
            api_key=os.getenv("TOGETHER_API_KEY")
        )

    async def generate(
        self,
        prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:

        # Optional params are only forwarded when provided, so the default
        # production behaviour (chat) stays byte-for-byte unchanged. The
        # evaluation harness sets them for the judge (a reasoning model needs a
        # non-zero temperature and enough tokens for its reasoning trace).
        extra: dict = {}
        if temperature is not None:
            extra["temperature"] = temperature
        if max_tokens is not None:
            extra["max_tokens"] = max_tokens

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            **extra,
        )

        return response.choices[0].message.content
