# STATE

Handoff enxuto entre sessões. Snapshot detalhado: `docs/development/project-state.md`.

## Concluído nesta sessão
- **Fase 6 (Avaliação)** operacional: harness da **RAG Triad** nativo
  (LLM-as-a-judge com o `LLMService`), offline, em `backend/evaluation/` — não
  TruLens (ver **ADR-007**). Corpus congelado (494 artigos / 1281 chunks) e
  **20 perguntas** curadas (14 de artigo único, 6 temáticas).
- **Experimentos (leaderboard — Context / Groundedness / Answer):**
  - baseline `0.39 / 0.93 / 0.91`
  - **e5-instruct** `0.46 / 0.97 / 0.97` — adotado (prefixo instruct do e5 na query)
  - top10 (`k=10`) `0.32 / 0.97 / 0.96` — rejeitado (métrica de precisão diluída)
  - **rerank** `0.48 / 0.99 / 0.96` — **adotado em produção** (cross-encoder local
    fastembed, retrieve-then-rerank 20→5; ver **ADR-008**)
  - rerank-window `0.52 / 0.94 / 0.95` — rejeitado (sobe context, baixa groundedness)
  - hybrid-rerank `0.46 / 0.99 / 0.94` — rejeitado (sem ganho em perguntas semânticas)
- **Infra/robustez:** volume de cache para os modelos ONNX do fastembed; retry
  com backoff no harness (erros transitórios 503/429/timeout).
- **Capacidades ativáveis no harness** (fora de produção): sentence-window
  (`--window`), hybrid dense+BM25 (`--hybrid` + `index-sparse`).
- Docs atualizados: ADR-007, **ADR-008**, project-state, roadmap, relatório semanal.

## Pela metade / em aberto
- **Nada de código pela metade** — working tree limpo. Fase 6 mergeada em `main`
  (PR #2). Neste projeto pode-se commitar direto na `main`.
- O índice esparso BM25 (`article_chunks_sparse` no Qdrant) existe mas só é usado
  pelo experimento hybrid, que não foi adotado.

## Próxima tarefa
**Chunking sweep** (próximo experimento). Variar `chunk_size`/`overlap` no
`LlamaIndexChunkingService` (hoje 350/50) — ex. 256/32 e 512/64. Para cada:
reindexar (apagar chunks/vetores e regerar — corpus de artigos igual, muda só a
granularidade; re-embeda via Together = custo), correr o harness e comparar no
leaderboard. Ataca também a context relevance, pela via da preparação dos dados.

A seguir: **query rewriting / HyDE**; e a melhoria de metodologia mais importante,
**recall@k com respostas-verdade** (a métrica atual é só de precisão).

Backlog anterior: Crawl4AI (JS); normalização de metadados; fila/worker;
limpeza de vetores órfãos no Qdrant; paralelizar a avaliação de Context Relevance.

## Como correr a avaliação (dentro do container)
```
docker compose exec backend python -m evaluation.run_eval sample -n 20
docker compose exec backend python -m evaluation.run_eval index-sparse      # p/ --hybrid
docker compose exec backend python -m evaluation.run_eval run -e <nome> [--rerank] [--window N] [--hybrid]
docker compose exec backend python -m evaluation.run_eval board
```
