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

------------------------------------------------------------------------

# Estado atual

## Implementado

-   Harness de avaliação da RAG Triad (nativo, LLM-as-a-judge) — Fase 6.
-   Corpus e conjunto de perguntas congelados; leaderboard de experiências.
-   Formatação da query no padrão instruct do e5 no retrieval (melhoria medida).

## Próximos passos

1.  Experimento de **reranking** (retrieve 20 → rerank → top-5) para atacar a
    precisão do contexto de forma limpa (mantém 5 chunks, melhora a qualidade).
2.  Sentence-window / expansão por vizinhos usando o `chunk_index`.
3.  Paralelizar a avaliação de Context Relevance no harness (reduzir latência).
4.  (Opcional) juiz distinto do gerador para reduzir enviesamento same-model.
