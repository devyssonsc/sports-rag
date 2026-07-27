# Sports RAG --- MVP de Aprendizado em Retrieval-Augmented Generation (RAG)

# Objetivo do Projeto

Este projeto tem como objetivo construir um sistema
**Retrieval-Augmented Generation (RAG)** do zero, priorizando o
entendimento dos conceitos fundamentais em vez da utilização de
frameworks que abstraem o funcionamento interno.

O foco principal não é desenvolver um produto de produção, mas
compreender profundamente como cada componente de um sistema RAG
funciona e como eles se integram para permitir que um Large Language
Model (LLM) responda perguntas utilizando informações externas.

O domínio escolhido será **notícias esportivas**, com foco em futebol
europeu. As notícias serão obtidas por meio de feeds RSS, evitando
técnicas de scraping mais complexas nesta primeira versão.

Ao final do projeto, espera-se compreender não apenas como utilizar
ferramentas existentes, mas também como implementar manualmente um
pipeline RAG completo, sendo capaz de evoluí-lo para arquiteturas mais
robustas.

------------------------------------------------------------------------

# Filosofia do Projeto

Este projeto é um **MVP de aprendizado**.

A prioridade será sempre compreender os conceitos antes de buscar
desempenho ou sofisticação arquitetural.

Cada etapa seguirá o seguinte processo:

1.  Explicação do conceito
2.  Motivação para sua utilização
3.  Implementação mínima
4.  Explicação detalhada do código
5.  Como a mesma solução é implementada em sistemas de produção

O objetivo é que todas as abstrações sejam compreendidas antes da
utilização de frameworks especializados.

------------------------------------------------------------------------

# Objetivos de Aprendizado

## Fundamentos de IA Generativa

-   Funcionamento de LLMs
-   Inferência local
-   Inferência via API
-   Prompt Engineering
-   Context Window
-   Tokens

## Retrieval-Augmented Generation (RAG)

-   Pipeline completo de um sistema RAG
-   Retrieval
-   Context Augmentation
-   Construção de prompts
-   Geração de respostas baseadas em documentos

## Recuperação de Informação

-   Chunking
-   Embeddings
-   Similarity Search
-   Bancos Vetoriais
-   Busca Semântica
-   Recuperação baseada em vetores

## Arquitetura

-   Organização modular
-   Separação de responsabilidades
-   Abstração de provedores de LLM
-   Pipeline de ingestão
-   Pipeline de consulta

## Avaliação

-   Benchmark entre diferentes modelos
-   Comparação entre modelos locais e remotos
-   Avaliação de latência
-   Avaliação de custo
-   Avaliação de qualidade das respostas

------------------------------------------------------------------------

# Escopo do MVP

A primeira versão do projeto priorizará simplicidade.

Serão implementados manualmente todos os componentes essenciais de um
sistema RAG.

Nesta fase **não serão utilizados frameworks especializados**, como:

-   LangChain
-   LangGraph
-   LlamaIndex
-   Haystack
-   CrewAI
-   AutoGen

Após compreender completamente o funcionamento interno do sistema, o
projeto evoluirá para uma segunda versão utilizando **LangGraph**,
permitindo comparar a implementação manual com uma implementação baseada
em framework.

------------------------------------------------------------------------

# Arquitetura Geral

## Pipeline de Ingestão

``` text
RSS
↓
Download das notícias
↓
Limpeza do texto
↓
Chunking
↓
Geração de Embeddings
↓
Armazenamento no Qdrant
```

## Pipeline de Consulta

``` text
Pergunta
↓
Embedding da pergunta
↓
Busca Vetorial
↓
Recuperação dos chunks relevantes
↓
Construção do Prompt
↓
LLM
↓
Resposta
```

------------------------------------------------------------------------

# Tecnologias

## Backend

### Python

Implementação do pipeline de ingestão, processamento de texto,
embeddings, recuperação de documentos, integração com LLMs e APIs REST.

### FastAPI

Framework da API responsável pelos endpoints do chatbot, ingestão e
integração entre frontend e backend.

## Frontend

### React

Interface do chatbot e aprendizado do ecossistema React.

## Banco Relacional

### PostgreSQL

Armazenamento de artigos, fontes, URLs, datas e metadados.

## Banco Vetorial

### Qdrant

Armazenamento de embeddings e realização de buscas vetoriais.

## Embeddings

Modelos open-source executados localmente.

Modelo inicial:

-   BAAI/bge-small-en-v1.5

## NLP

### spaCy

-   Tokenização
-   NER
-   Extração de entidades

## LLM Local

### Ollama

Objetivos:

-   Inferência local
-   Gerenciamento de modelos
-   Integração via HTTP
-   Compreensão do pipeline local

Modelos iniciais:

-   Gemma 3 4B
-   Qwen 2.5 3B
-   Llama 3.2 3B

## LLM por API

### Together AI

Será utilizado para:

-   Experimentar diversos modelos
-   Benchmark entre modelos
-   Comparar qualidade, latência, tokens e custo
-   Desacoplar a arquitetura do modelo utilizado

## Docker

-   Docker Compose
-   Containers
-   Volumes
-   Variáveis de ambiente

------------------------------------------------------------------------

# Arquitetura de LLM Providers

``` text
                 Pergunta
                     │
                     ▼
                Pipeline RAG
                     │
                     ▼
               LLM Provider
          ┌──────────┴──────────┐
          ▼                     ▼
      Ollama              Together AI
          ▼                     ▼
   Modelo Local        Modelo Remoto
```

------------------------------------------------------------------------

# Benchmark entre Modelos

Serão comparados:

-   Qualidade da resposta
-   Tempo de resposta
-   Latência
-   Tokens de entrada
-   Tokens de saída
-   Custo por consulta

------------------------------------------------------------------------

# Organização Arquitetural

Principais módulos:

-   API
-   Ingestion
-   Preprocessing
-   Embeddings
-   Vector Store
-   Retrieval
-   LLM
-   RAG
-   Database

------------------------------------------------------------------------

# Roadmap

1.  Estrutura do projeto
2.  Docker
3.  FastAPI
4.  React
5.  PostgreSQL
6.  Qdrant
7.  Download das notícias (RSS)
8.  Limpeza do texto
9.  Chunking
10. Embeddings
11. Inserção no banco vetorial
12. Busca vetorial
13. Similarity Search
14. Ollama
15. Together AI
16. Abstração de LLM Providers
17. Benchmark entre modelos
18. Construção manual do RAG
19. Chat
20. LangGraph
21. Melhorias e otimizações

------------------------------------------------------------------------

# Evoluções Futuras

-   Hybrid Search
-   Re-ranking
-   Query Expansion
-   Context Compression
-   Avaliação automática de RAG
-   Seleção dinâmica de modelos
-   Observabilidade
-   Agentes de IA

------------------------------------------------------------------------

# Resultado Esperado

Ao final do projeto, espera-se compreender profundamente como
implementar um sistema RAG moderno, desde a ingestão de documentos até a
geração de respostas, entendendo os fundamentos de embeddings,
recuperação de informação, bancos vetoriais, integração com LLMs e
evolução para arquiteturas mais avançadas utilizando LangGraph.
