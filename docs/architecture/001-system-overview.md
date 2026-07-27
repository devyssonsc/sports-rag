# System Overview

## 1. Objetivo

O Sports RAG é um projeto de aprendizado cujo objetivo é compreender profundamente como um sistema Retrieval-Augmented Generation (RAG) funciona internamente.

Ao contrário de tutoriais que utilizam frameworks especializados desde o início, este projeto implementará manualmente todos os componentes fundamentais de um pipeline RAG antes da introdução de abstrações como LangGraph.

Além de compreender o funcionamento do RAG, o projeto também servirá como laboratório para comparar diferentes modelos de linguagem utilizando exatamente o mesmo processo de recuperação de contexto.

---

# 2. Escopo

O sistema será capaz de:

- obter notícias esportivas através de feeds RSS;
- processar e preparar documentos;
- dividir documentos em chunks;
- gerar embeddings;
- armazenar embeddings em um banco vetorial;
- recuperar documentos semanticamente relevantes;
- construir prompts utilizando os documentos recuperados;
- gerar respostas utilizando LLMs locais e remotos;
- comparar diferentes modelos utilizando o mesmo contexto.

---

# 3. Objetivos

Os principais objetivos do projeto são:

- compreender Retrieval-Augmented Generation;
- compreender bancos vetoriais;
- compreender embeddings;
- compreender chunking;
- compreender similarity search;
- compreender prompt engineering;
- compreender inferência local;
- compreender inferência via API;
- compreender arquitetura de aplicações de IA;
- compreender benchmarking entre modelos.

---

# 4. Arquitetura Geral

O sistema será dividido em dois pipelines independentes.

## Pipeline de Ingestão

```text
RSS

↓

Download

↓

Limpeza

↓

Chunking

↓

Embeddings

↓

Qdrant
```

## Pipeline de Consulta

```text
Pergunta

↓

Embedding

↓

Similarity Search

↓

Chunks

↓

Prompt

↓

LLM

↓

Resposta
```

---

# 5. Componentes

## Frontend

Responsável pela interface do chatbot.

---

## Backend

Responsável pela coordenação do pipeline RAG.

---

## PostgreSQL

Armazena dados estruturados.

---

## Qdrant

Armazena embeddings e realiza buscas vetoriais.

---

## Ollama

Executa modelos locais para fins educacionais e testes de inferência.

---

## Together AI

Fornece acesso a diferentes modelos comerciais através de uma única API.

Será utilizado principalmente para benchmarking e comparação entre modelos.

---

# 6. Arquitetura de LLM Providers

```text
                 RAG

                  │

            LLM Provider

          ┌───────┴────────┐

          ▼                ▼

      Ollama         Together AI

          ▼                ▼

    Modelo Local    Modelo Remoto
```

Essa arquitetura desacopla o pipeline RAG do modelo utilizado.

---

# 7. Princípios Arquiteturais

Durante o desenvolvimento do projeto serão seguidos os seguintes princípios:

- implementação incremental;
- documentação antes da implementação;
- responsabilidade única por módulo;
- baixo acoplamento;
- alta coesão;
- abstrações apenas quando justificadas;
- compreensão antes de otimização.

---

# 8. Evolução Prevista

Após a implementação manual completa do sistema, serão estudadas evoluções como:

- LangGraph;
- Hybrid Search;
- Re-ranking;
- Query Expansion;
- Context Compression;
- avaliação automática de RAG;
- observabilidade;
- agentes de IA.
