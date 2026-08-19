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

## 19/08/2026

-   **Comando `reindex`** para o chunking sweep: apaga chunks (Postgres) e vetores
    densos (Qdrant), re-parte todos os artigos com `chunk_size`/`overlap` dados e
    re-embeda — mantendo os artigos. CLI `run_eval reindex`. Limpeza de `print`
    de debug no `LlamaIndexChunkingService`.
-   **Descoberta que redirecionou o sweep:** o modelo de embeddings
    `multilingual-e5-large-instruct` tem **teto rígido de 512 tokens** — a
    Together **rejeita** (erro 400), não trunca. Provado empiricamente. Logo,
    **não dá para subir o chunk** acima de ~512 com o e5. Além disso, a Together
    **não oferece nenhum modelo de embeddings de contexto longo**.
-   **Decisão:** trocar para embeddings **locais de contexto longo** via fastembed
    — `jinaai/jina-embeddings-v2-base-en` (**8192 tokens**, 768-dim, inglês,
    simétrico). Corre em CPU, **sem custo de API** (a Together fica só para o LLM).
-   **Fase A + B (troca de modelo, medidas e REJEITADAS — ver ADR-009):**
    `EmbeddingService` trocado para fastembed/jina (`VECTOR_SIZE` 768, sem prefixo
    e5) e medido contra o baseline e5+rerank (0.484 / 0.989 / 0.961):
    -   `jina-350` = **0.439 / 0.975 / 0.955** — pior nas três (modelo mais fraco).
    -   `jina-1024` = **0.430 / 0.931 / 0.958** — chunks maiores **não ajudaram** e
        baixaram a groundedness.
    -   Confirma o padrão da sessão: este corpus premeia recuperação **precisa**,
        não mais contexto.
-   **Decisão: reverter para o e5** (`ADR-009`). Código do jina revertido;
    reindex de volta a e5 (350/50, 1024-dim). O comando `reindex` fica (útil para
    experiências futuras). O e5 tem teto de 512 tokens, por isso chunks grandes
    ficam fora do alcance sem trocar de modelo de embeddings.
-   **Recall@k adicionado ao harness** (a "outra metade" — cobertura, não só
    precisão): chave de correção `ground_truth.json` (article_ids, estáveis entre
    reindexes), métrica **determinística** (sem LLM) e modo **`--retrieval-only`**
    (rápido/grátis). Diagnóstico (produção e5): **pool@20 = 0.87**, denso@5 = 0.77,
    **rerank@5 = 0.76**. Revela que ~13% dos artigos-fonte nem entram no top-20, e
    que o rerank troca ~0.01 de recall por precisão. Reabriu a questão do **hybrid**
    (rejeitado na precisão, mas talvez ganhasse no recall).
-   **Hybrid re-medido pela lente do recall — continua rejeitado (agora nos dois
    eixos):** pool@20 = 0.883 (vs denso 0.867, só +1.6pp) e top-5 = 0.767 (igual ao
    denso). O ganho de cobertura do BM25 é marginal e dilui-se até ao top-5; e a
    precisão já era pior. O verdadeiro buraco (~12–13% das fontes fora do pool@20)
    pede **query rewriting**, não hybrid. Corrigido de passagem um bug: o
    `index-sparse` acumulava pontos órfãos (recria a coleção antes do backfill) +
    guarda no retrieval para ignorar chunk_ids inexistentes.
-   **HyDE (query transform) — REJEITADO:** o LLM gera um documento hipotético e
    embute-se esse (lado documento) em vez da pergunta. Resultado: recall **pior**
    (pool@20 0.833 vs 0.867; top-5 0.742 vs 0.758). Motivo, com exemplo real: para
    "Tielemans → que clube?", o modelo inventou "Royal Antwerp, €15M, do Leicester"
    (verdade: Man Utd, £35M, do Aston Villa). O corpus é notícia **recente que o
    modelo não conhece** → o hipotético aluciná e engana a busca. Fica como
    capacidade do harness (`--hyde`). Próximo: **multi-query**, que reformula a
    *pergunta* (não pede factos ao modelo) → deve ser robusto onde o HyDE falhou.

------------------------------------------------------------------------

# Estado atual

## Implementado

-   Harness de avaliação da RAG Triad (nativo, LLM-as-a-judge) — Fase 6.
-   Corpus e conjunto de perguntas congelados; leaderboard de experiências.
-   Produção: embeddings e5 (instruct na query) + reranking cross-encoder local.
-   Comando `reindex` (base para experiências de chunking / troca de modelo).
-   Métrica **recall@k** + modo `--retrieval-only` no harness.

## Próximos passos

1.  **Multi-query (query expansion)** — o LLM gera N reformulações da *pergunta*;
    recupera-se com cada e fundem-se (RRF). Não pede factos ao modelo (ao contrário
    do HyDE), por isso deve ajudar as temáticas / o recall.
2.  **k adaptativo / corte por score do reranker** — subir a context relevance
    devolvendo menos chunks quando poucos são relevantes.
3.  Paralelizar a avaliação de Context Relevance no harness (reduzir latência).
