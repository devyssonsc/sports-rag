# Development Log --- Semana

**Período:** 10/08/2026 a 14/08/2026

## Objetivo da semana

Concluir a transição Feed → NewsSource, migrar toda a stack para assíncrona
e expandir a camada de descoberta de notícias para múltiplas fontes
(RSS, HTML e sitemap), mantendo o restante do pipeline RAG inalterado.

------------------------------------------------------------------------

## 10/08/2026

-   Auditoria completa do refactor Feed → NewsSource em todas as camadas.
-   Correção do ERD (Feed → NewsSource, `news_source_id`, campos reais dos
    modelos).
-   `DiscoveryFactory` passa a lançar `UnsupportedNewsSourceType` em vez de
    `ValueError`.
-   Remoção de método morto no `NewsSourceRepository`.
-   Testes mínimos (`NewsSourceService`, `DiscoveryFactory`) e configuração do
    pytest.
-   Sincronização da documentação (project-state, architecture, roadmap).

## 11/08/2026

-   Documento de histórico da transição RSS → NewsSource
    (`01-rss-to-newssource.md`) e atualização do project-history.
-   ADR-006 e migração de toda a stack para assíncrona: FastAPI, SQLAlchemy
    (`AsyncSession` sobre psycopg 3), `AsyncQdrantClient`, `AsyncTogether`;
    Trafilatura e feedparser via `asyncio.to_thread`.
-   Correção de um bug latente que impedia o boot (sombreamento do builtin
    `list` no `article_repository`).
-   Campo `article_url_pattern` (regex por fonte) no `NewsSource`, com migration
    e validação no schema.
-   Implementação da `HtmlDiscovery` (tipo CRAWL) para páginas HTML
    server-rendered, filtrando os links por regex.
-   Implementação da `SitemapDiscovery` (tipo SITEMAP) para sitemaps XML /
    Google News, preenchendo o `published_at` a partir do sitemap.
-   Guard de conteúdo na ingestão (pula conteúdo vazio ou muito curto, como
    paredes de consentimento de cookies).
-   Tratamento de erros de descoberta: rede/HTTP/XML inválido passam a retornar
    HTTP 502 (`DiscoveryError`) em vez de 500 genérico.
-   Normalização de `published_at` para UTC em todas as fontes (via
    `app.core.dates`); o `feedparser` já entrega em UTC e um helper unifica RSS
    e SITEMAP.
-   Filtro de URL por fonte com inclusão/exclusão: prefixo `!` bloqueia (helper
    compartilhado usado por `HtmlDiscovery` e `SitemapDiscovery`).
-   Otimização de embeddings: chunks de um artigo embedados em lote (uma chamada
    à Together por artigo, em vez de uma por chunk).
-   Ingestão em background: `POST /news-sources/{id}/fetch` retorna `202` e roda
    em segundo plano (FastAPI BackgroundTasks), gravando `last_fetched_at` e
    logando o `IngestionResult`.
-   Testes acompanhando cada etapa (38 no total) e documentação atualizada.

------------------------------------------------------------------------

# Estado atual

## Implementado

-   Feed totalmente substituído por NewsSource em todas as camadas.
-   Stack assíncrona ponta a ponta (ADR-006).
-   Descoberta multi-source: RSS, CRAWL (HTML) e SITEMAP, selecionadas pela
    `DiscoveryFactory`.
-   Filtro de URLs por fonte (`article_url_pattern`), com inclusão (padrão) e
    exclusão (prefixo `!`), e guard de conteúdo na ingestão.
-   `published_at` normalizado em UTC para RSS e SITEMAP.
-   Embedding em lote por artigo.
-   Ingestão em background (`/fetch` → `202`), gravando `last_fetched_at`.
-   Pipeline RAG completo (ingestão → chunking → embeddings → retrieval → LLM).

## Próximos passos

1.  Integrar Crawl4AI como estratégia baseada em navegador para sites
    renderizados por JavaScript (novo tipo CRAWL4AI).
2.  Adicionar novas fontes de notícias.
3.  Normalizar metadados entre provedores.
4.  Evoluir a ingestão em background para fila/worker dedicado com retries e
    agendamento periódico.
5.  Remover vetores órfãos no Qdrant ao apagar artigos.
