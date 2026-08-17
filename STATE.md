# STATE

Handoff enxuto entre sessões. Snapshot detalhado: `docs/development/project-state.md`.

## Concluído nesta sessão
- **Fase 6 (Avaliação) iniciada.** Harness da **RAG Triad** nativo (LLM-as-a-judge
  com o `LLMService`), offline, em `backend/evaluation/` — não TruLens (ver
  **ADR-007**).
  - `judge.py` (3 métricas + razão), `harness.py` (runner), `corpus.py`
    (congela corpus + amostra artigos), `leaderboard.py`, `run_eval.py`
    (`sample` / `run` / `board`).
  - `LLMService.generate` com `temperature` opcional (juiz usa 0; chat inalterado).
- **Corpus congelado:** 494 artigos / 1281 chunks. **20 perguntas** curadas
  (14 de artigo único, 6 temáticas).
- **Baseline (top-5):** Context 0.39 · Groundedness 0.93 · Answer 0.91 →
  retrieval é o gargalo.
- **Experimento e5-instruct (adotado):** prefixo instruct do e5 na query
  (`embed_query`), corrigindo o uso de `embed_document` no retrieval. Sobe para
  **0.46 / 0.97 / 0.97** e recupera uma falha total de retrieval (Wrexham).
- **Experimento top10 (rejeitado):** `top_k=10` baixou a Context Relevance
  (0.32) sem melhorar respostas → a métrica é de precisão. `top_k` fica em 5.
- Docs atualizados (project-state, roadmap, ADR-007, relatório semanal).

## Pela metade / em aberto
- **Nada de código pela metade** — working tree limpo, tudo commitado na branch
  `feat/evaluation-harness` (ainda **sem push**).
- Melhoria fácil pendente no harness: paralelizar a avaliação de Context
  Relevance (hoje os chunks são avaliados em série → domina a latência).

## Próxima tarefa
Experimento de **reranking** (retrieve-then-rerank): recuperar ~20 candidatos por
embeddings → reordenar com um cross-encoder (endpoint de rerank da Together) →
ficar com os 5 melhores. Objetivo: subir a Context Relevance mantendo 5 chunks
(sem a diluição do top_k). Medir no leaderboard vs `e5-instruct`.

Backlog: sentence-window (usar `chunk_index`), híbrido/BM25, juiz distinto do
gerador, recall@k com respostas-verdade; Crawl4AI (JS); fila/worker; limpeza de
vetores órfãos no Qdrant.

## Como correr a avaliação (dentro do container)
```
docker compose exec backend python -m evaluation.run_eval sample -n 20
docker compose exec backend python -m evaluation.run_eval run -e <nome>
docker compose exec backend python -m evaluation.run_eval board
```
