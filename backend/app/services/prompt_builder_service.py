from app.schemas.retrieval import RetrievedChunk


class PromptBuilderService:

    def build(
        self,
        question: str,
        chunks: list[RetrievedChunk],
    ) -> str:

        context_parts = []

        for chunk in chunks:

            context_parts.append(
                f"""
Article Title: {chunk.article_title}
Source: {chunk.source}

Content:
{chunk.content}
"""
            )

        context = "\n\n----------------------\n\n".join(
            context_parts
        )

        return f"""
You are an AI assistant specialized in football news.

Use ONLY the information provided in the context.

If the answer is not contained in the context, explicitly state that the information is unavailable.

Never invent facts.

When possible:

- Answer in complete sentences.
- Summarize the relevant information.
- If multiple articles contribute to the answer, combine them into a coherent response.
- Do not mention that you are using a context unless explicitly asked.

----------------------------------------

Context

{context}

----------------------------------------

Question

{question}

----------------------------------------

Answer
""".strip()