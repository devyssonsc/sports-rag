# STATE

Handoff enxuto entre sessões. Snapshot detalhado: `docs/development/project-state.md`.

## Concluído nesta sessão
- Transição Feed → NewsSource finalizada (auditoria, ERD, factory, testes).
- Stack migrada para **async** ponta a ponta (ADR-006) + fix de boot latente.
- Descoberta multi-source: **RSS**, **CRAWL (HTML)**, **SITEMAP** via `DiscoveryFactory`.
- `article_url_pattern` por fonte, com **inclusão** e **exclusão** (`!`).
- Guard de conteúdo (pula vazio/curto) e erros de descoberta → **HTTP 502**.
- `published_at` **normalizado em UTC** em todas as fontes.
- **Embedding em lote** por artigo.
- Ingestão em **background** (`/fetch` → 202, grava `last_fetched_at`).
- Tudo commitado e com push (`HEAD = 88df997`); 38 testes passando.

## Pela metade / em aberto
- **Nada de código pela metade** — working tree limpo.
- Groundwork feito (não implementado): análise do curso *Building & Evaluating
  Advanced RAG* → decidido implementar o **RAG Triad** como *LLM-as-a-judge*
  nativo (não TruLens/LlamaIndex-query-engines).

## Próxima tarefa
Montar o **harness de avaliação** (Fase 6):
1. Congelar corpus + conjunto fixo de 15–30 perguntas.
2. Implementar RAG Triad (Context Relevance, Groundedness, Answer Relevance)
   com o `LLMService` como juiz + leaderboard simples.
3. Medir o baseline atual.
4. Experimentos, um a um — começar por **formatar a query no padrão instruct do e5**.

Backlog: rerank, híbrido (BM25), Sentence-Window; Crawl4AI (JS); normalização de
metadados; fila/worker; limpeza de vetores órfãos no Qdrant.
