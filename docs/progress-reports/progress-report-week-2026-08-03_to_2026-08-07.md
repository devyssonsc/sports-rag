# Development Log --- Semana

**Período:** 03/08/2026 a 07/08/2026

## Objetivo da semana

Evoluir o pipeline de ingestão e recuperação de notícias até um sistema
RAG funcional, preparando a arquitetura para suportar múltiplas fontes
de dados.

------------------------------------------------------------------------

## 03/08/2026

-   Estudo do funcionamento de embeddings e busca vetorial.
-   Integração inicial com o Qdrant.
-   Criação automática da collection.
-   Implementação da persistência de chunks no PostgreSQL.
-   Validação da geração e armazenamento dos chunks.

## 04/08/2026

-   Integração entre ingestão, chunking e embeddings.
-   Geração automática de embeddings durante a ingestão.
-   Armazenamento dos vetores no Qdrant.
-   Revisão do algoritmo de chunking manual.
-   Correções de limpeza de texto.

## 05/08/2026

-   Migração do chunking manual para o LlamaIndex SentenceSplitter.
-   Ajuste do tamanho dos chunks para o modelo de embeddings.
-   Implementação do RetrievalService.
-   Integração PostgreSQL + Qdrant.
-   Inclusão de metadados nos resultados da busca.

## 06/08/2026

-   Implementação do LLMService.
-   Implementação do PromptBuilderService.
-   Implementação do ChatService.
-   Integração Retrieval → Prompt → LLM.
-   Utilização do modelo GPT-OSS-120B.
-   Testes com artigos da ESPN e BBC Sport.

## 07/08/2026

-   Criação do enum SourceType.
-   Renomeação de RSSArticle para SourceArticle.
-   Criação da infraestrutura DiscoveryStrategy.
-   Implementação da RSSDiscovery.
-   Implementação da DiscoveryFactory.
-   Adição do tipo RSS/CRAWL ao modelo Feed.
-   Migration com Alembic.
-   Refatoração da rota /feeds/{id}/fetch para utilizar a
    DiscoveryFactory.

# Estado atual

## Implementado

-   Cadastro de feeds.
-   Ingestão automática.
-   Extração de conteúdo com Trafilatura.
-   Chunking semântico com LlamaIndex.
-   Embeddings.
-   Qdrant.
-   Busca vetorial.
-   Pipeline RAG.
-   Arquitetura preparada para múltiplas estratégias de descoberta.

## Próximos passos

1.  Finalizar a refatoração Feed → NewsSource.
2.  Implementar CrawlDiscovery.
3.  Integrar Crawl4AI.
4.  Adicionar novas fontes de notícias.
5.  Normalizar datas e metadados.
