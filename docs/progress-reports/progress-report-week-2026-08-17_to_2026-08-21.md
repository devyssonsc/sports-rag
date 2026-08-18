# Development Log --- Semana

**Período:** 17/08/2026 a 21/08/2026

## Objetivo da semana

Iniciar a Fase 6 (Avaliação): montar um harness de avaliação para o pipeline
RAG, medir uma linha de base e começar a testar melhorias de retrieval de forma
mensurável, sem alterar o comportamento de produção do chat.

------------------------------------------------------------------------

## 17/08/2026

-   Análise das aulas 1 e 2 do curso *Building and Evaluating Advanced RAG*
    (DeepLearning.AI) e decisão de implementar a **RAG Triad** de forma **nativa**
    (LLM-as-a-judge com o `LLMService`), em vez de TruLens/LlamaIndex query
    engines (ver **ADR-007**).
-   Novo pacote `backend/evaluation/` (offline, fora do request path da API):
    -   `judge.py`: as três métricas da tríade (Context Relevance, Groundedness,
        Answer Relevance) pontuadas por LLM, cada uma com razão (chain-of-thought);
        parser JSON robusto.
    -   `harness.py`: runner que corre o pipeline real (retrieve → prompt →
        generate) por pergunta e avalia as três métricas em paralelo.
    -   `corpus.py`: congela o corpus inteiro (ids + contagens) para detetar
        *drift*, e amostra N artigos aleatórios com conteúdo para autorar
        perguntas.
    -   `leaderboard.py`: grava o detalhe por run e acrescenta linha ao
        leaderboard.
    -   `run_eval.py`: CLI (`sample` / `run` / `board`).
-   `LLMService.generate` ganhou parâmetro `temperature` opcional e
    retrocompatível (default preserva o chat; o juiz usa `temperature=0`).
-   Corpus congelado: **494 artigos / 1281 chunks**; 20 artigos amostrados.
    Conjunto fixo de **20 perguntas** curadas (14 de artigo único, 6 temáticas).
-   **Baseline medido** (top-5): Context Relevance **0.39**, Groundedness
    **0.93**, Answer Relevance **0.91**. Diagnóstico: o retrieval é o gargalo.
-   **Experimento e5-instruct:** aplicar o prefixo instruct do e5 só do lado da
    query (`embed_query`), corrigindo o uso indevido de `embed_document` no
    retrieval. Resultado: **0.46 / 0.97 / 0.97** (as três sobem) e recuperou uma
    falha total de recuperação (pergunta do Wrexham). **Adotado no pipeline.**
-   **Experimento top10 (`top_k=10`):** Context Relevance caiu para **0.32** sem
    melhorar as respostas — confirma que a métrica é de **precisão** (média por
    chunk), enviesada contra top_k maior. **Rejeitado; `top_k` fica em 5.**
-   **Reranking (adotado em produção, ADR-008):** cross-encoder local via
    fastembed (ONNX, sem torch), retrieve-then-rerank (20 → top-5). Together sem
    rerank serverless → optou-se por local. Resultado **0.48 / 0.99 / 0.96**.
    Ligado ao `/chat` (singleton via `lru_cache`), validado end-to-end.
-   **Sentence-window (rejeitado):** `--window 1` sobe Context Relevance (0.52)
    mas baixa Groundedness (0.99 → 0.94) — o contexto alargado nem sempre apoia
    a resposta. Fica como capacidade do harness.
-   **Hybrid BM25 (rejeitado):** coleção esparsa `Qdrant/bm25` + fusão RRF com a
    densa. **Sem ganho** (0.46) — perguntas semânticas, onde o e5 já vence e o
    BM25 mete ruído lexical. Fica como capacidade do harness (`index-sparse`).
-   **Infra:** volume de cache para os modelos ONNX; retry/backoff no harness.

## 18/08/2026

-   **PR #2** (`feat/evaluation-harness` → `main`) aberto e **mergeado**: todo o
    trabalho da Fase 6 está em `main`.
-   **Documentação de arquitetura atualizada** (estava desatualizada face ao
    pipeline novo):
    -   `architecture.md`: `RetrievalService` agora reflete query-instruct +
        rerank; nova secção `RerankService`; `fastembed` nas tecnologias;
        reranking/evaluation saíram de "futuro".
    -   `data-flow.md`: diagrama e passos 2–3 do pipeline de QA (embed_query com
        prefixo e5 → pool denso → rerank).
    -   Novo `backend/evaluation/README.md`: guia estável de como correr
        experiências e o significado das três métricas.
-   **Retrospetiva da sessão** e decisão de rumo: o *retrieval puro* dá retornos
    decrescentes (context relevance limitada pela métrica de precisão); próximo
    foco em **chunking** e **query rewriting**.

------------------------------------------------------------------------

# Estado atual

## Implementado

-   Harness de avaliação da RAG Triad (nativo, LLM-as-a-judge) — Fase 6.
-   Corpus e conjunto de perguntas congelados; leaderboard de experiências.
-   Produção: query no padrão instruct do e5 + reranking cross-encoder local.

## Próximos passos

1.  **Chunking sweep (próximo experimento).** Variar `chunk_size`/`overlap` no
    `LlamaIndexChunkingService` (hoje 350/50) — ex.: 256/32, 512/64. Para cada
    configuração: reindexar (chunks + embeddings densos e, se aplicável, o índice
    esparso), correr o harness e comparar no leaderboard. Requer um passo de
    reindexação limpa (apagar chunks/vetores e regerar) — o corpus de artigos
    fica igual; o que muda é a granularidade. Atenção: reindexar re-embeda via
    Together (custo).
2.  **Query rewriting / HyDE.** O LLM reescreve/expande a pergunta antes do
    retrieval; útil sobretudo nas perguntas temáticas.
3.  **Recall@k com respostas-verdade** — anotar a(s) fonte(s) esperada(s) por
    pergunta para medir cobertura (a métrica atual mede só precisão).
4.  Paralelizar a avaliação de Context Relevance no harness (reduzir latência).
5.  (Opcional) juiz distinto do gerador para reduzir enviesamento same-model.
