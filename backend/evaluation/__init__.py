"""Offline evaluation harness for the Sports RAG pipeline.

Implements the **RAG Triad** (Context Relevance, Groundedness, Answer
Relevance) from the DeepLearning.AI course *Building and Evaluating Advanced
RAG*, but natively (LLM-as-a-judge via ``LLMService``) instead of TruLens.

The harness is a batch tool that runs *outside* the API so it never touches the
production request path. It reuses the very same services the app uses, so any
change to chunking / retrieval / prompting is measured on the real pipeline.

Run it from inside the backend container (see ``run_eval.py``).
"""
