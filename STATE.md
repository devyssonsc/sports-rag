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

- **Experimento embeddings de contexto longo (jina) — REJEITADO (ADR-009):**
  trocou-se o `EmbeddingService` para `jina-embeddings-v2-base-en` (8192 tokens,
  local) e mediu-se: `jina-350` = 0.44/0.98/0.96 e `jina-1024` = 0.43/0.93/0.96 —
  **piores que o e5+rerank** (0.48/0.99/0.96); chunks grandes não ajudaram.
  **Revertido para e5.** Motivo da exploração: o e5 tem teto rígido de 512 tokens
  (Together dá erro 400) e a Together não tem modelo de contexto longo.

## Pela metade / em aberto
- **Working tree com alterações por commitar** (a manter): comando `reindex` novo,
  `chunk_repository.delete_all/list_all`, `recreate_dense_collection`, limpeza de
  `print` de debug no chunking, ADR-009 + docs. O código do jina foi **revertido**.
  A produção está de volta ao e5 (reindex 350/50, 1024-dim). Falta **commitar**.
- Fase 6 mergeada em `main` (PR #2). Neste projeto pode-se commitar direto na `main`.
- Índice esparso BM25 fica **stale** após um reindex — re-correr `index-sparse` se
  usar `--hybrid`.

## Produção atual (retrieval)
embeddings **e5-large-instruct** (prefixo instruct na query) → busca densa (cosseno)
top-20 → **rerank** cross-encoder local → top-5. É a melhor config medida.

## Recall@k (feito nesta sessão)
Harness ganhou **recall@k** (cobertura): `ground_truth.json` (article_ids), métrica
determinística sem LLM, modo `--retrieval-only` (grátis). Produção e5: pool@20 = 0.87,
denso@5 = 0.77, **rerank@5 = 0.76**. ~13% das fontes nem entram no top-20; o rerank
troca ~0.01 de recall por precisão.

## Hybrid re-medido pelo recall (feito) — continua rejeitado
pool@20 = 0.883 (vs denso 0.867, +1.6pp) e top-5 = 0.767 (igual ao denso): ganho de
cobertura marginal que dilui até ao top-5, e a precisão já era pior. Bug corrigido:
`index-sparse` recria a coleção esparsa (acumulava órfãos → KeyError).

## Estratégias de query (a testar com recall@k, grátis via --retrieval-only)
- **HyDE (feito) — REJEITADO:** recall pior (pool 0.833 vs 0.867). O LLM inventa
  o hipotético (corpus é notícia recente que ele não conhece) e engana a busca.
  Fica como capacidade (`--hyde`).

## Próxima tarefa
1. **Multi-query (query expansion)** — o LLM gera N reformulações da *pergunta*
   (não pede factos, ao contrário do HyDE); recupera-se com cada e funde-se (RRF).
   Medir recall vs baseline (rerank@5 0.758 / pool@20 0.867).
2. **k adaptativo / corte por score do reranker** — subir a context relevance.

Backlog: Crawl4AI (JS); normalização de metadados; fila/worker; limpeza de vetores
órfãos; paralelizar a avaliação de Context Relevance. Nota: chunks >512 tokens só
com outro modelo de embeddings de contexto longo (ver ADR-009).

## Como correr a avaliação (dentro do container)
```
docker compose exec backend python -m evaluation.run_eval sample -n 20
docker compose exec backend python -m evaluation.run_eval reindex --chunk-size N --chunk-overlap M
docker compose exec backend python -m evaluation.run_eval run -e <nome> [--rerank] [--window N] [--hybrid]
docker compose exec backend python -m evaluation.run_eval board
```
