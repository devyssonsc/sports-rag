# Glossário

Este documento reúne os principais conceitos utilizados ao longo do projeto. Seu objetivo é servir como referência rápida durante o desenvolvimento e manter uma terminologia consistente em toda a documentação.

---

# ANN (Approximate Nearest Neighbor)

Algoritmo utilizado por bancos vetoriais para encontrar rapidamente os vetores mais próximos de uma consulta.

Em vez de comparar a consulta com todos os vetores armazenados, utiliza estruturas de indexação que tornam a busca muito mais eficiente.

Exemplos:

* HNSW
* IVF
* PQ

---

# Chunk

Pequena parte de um documento original.

Um documento geralmente é dividido em vários chunks antes da geração dos embeddings.

Exemplo:

Documento:

> Artigo completo da BBC Sport.

Chunks:

* Introdução
* Desenvolvimento
* Conclusão

---

# Chunking

Processo de dividir documentos em partes menores (chunks).

O objetivo é permitir que o sistema recupere apenas as informações relevantes em vez do documento inteiro.

---

# Context Window

Quantidade máxima de informação (tokens) que um LLM consegue receber em uma única requisição.

Essa limitação influencia diretamente:

* tamanho dos prompts;
* quantidade de documentos enviados ao modelo;
* estratégia de recuperação.

---

# Embedding

Representação numérica de um texto em um espaço vetorial.

Embeddings preservam significado semântico, permitindo comparar textos através de operações matemáticas.

---

# Embedding Model

Modelo responsável por transformar texto em embeddings.

Neste projeto serão utilizados inicialmente modelos open-source executados localmente.

---

# Feed RSS

Formato padronizado utilizado para distribuição de notícias e atualizações.

Será a principal fonte de documentos deste projeto.

---

# Hybrid Search

Estratégia que combina busca vetorial com busca tradicional baseada em palavras-chave (como BM25).

Será estudada em versões futuras.

---

# Inference (Inferência)

Processo de executar um modelo de IA para gerar uma resposta.

Pode ocorrer:

* localmente;
* através de uma API.

---

# LLM (Large Language Model)

Modelo de linguagem treinado para compreender e gerar texto em linguagem natural.

Exemplos:

* Llama
* Qwen
* Gemma
* DeepSeek

---

# LLM Provider

Camada responsável por fornecer acesso a modelos de linguagem.

Neste projeto existirão dois providers:

* Ollama
* Together AI

A aplicação será desacoplada do provedor utilizado.

---

# Metadata

Informações adicionais armazenadas junto aos documentos ou embeddings.

Exemplos:

* fonte;
* data de publicação;
* URL;
* título;
* campeonato.

---

# Ollama

Ferramenta utilizada para executar modelos de linguagem localmente.

Fornece uma API HTTP simples para integração com aplicações.

---

# Pipeline

Sequência organizada de etapas executadas para realizar uma tarefa.

Neste projeto existirão dois pipelines principais:

* Pipeline de Ingestão;
* Pipeline de Consulta.

---

# Prompt

Texto enviado ao modelo de linguagem.

Normalmente é composto por:

* instruções;
* contexto recuperado;
* pergunta do usuário.

---

# Prompt Engineering

Processo de projetar prompts para obter respostas melhores dos modelos de linguagem.

---

# Qdrant

Banco de dados vetorial utilizado para armazenar embeddings e realizar buscas semânticas.

---

# Quantization (Quantização)

Técnica utilizada para reduzir o tamanho e o consumo de memória de modelos de IA.

Permite executar modelos grandes em hardware mais limitado, geralmente com pequena perda de precisão.

---

# RAG (Retrieval-Augmented Generation)

Arquitetura que combina recuperação de documentos com modelos de linguagem.

Fluxo simplificado:

Documento → Embedding → Banco Vetorial

Pergunta → Embedding → Busca → Contexto → LLM → Resposta

---

# Retrieval

Processo de recuperar documentos relevantes para responder uma pergunta.

É a etapa responsável por encontrar o contexto que será enviado ao LLM.

---

# Similarity Search

Busca baseada na similaridade entre embeddings.

Permite encontrar documentos semanticamente relacionados mesmo quando utilizam palavras diferentes.

---

# Token

Unidade básica de processamento utilizada pelos modelos de linguagem.

Um token não corresponde necessariamente a uma palavra inteira; pode representar uma palavra, parte de uma palavra ou um símbolo.

Os custos de APIs comerciais e o limite da janela de contexto são normalmente medidos em tokens.

---

# Together AI

Plataforma que disponibiliza diversos modelos de IA por meio de uma API unificada.

Será utilizada para experimentação e benchmarking entre diferentes modelos.

---

# Vector Database

Banco de dados especializado no armazenamento e recuperação eficiente de embeddings.

Neste projeto será utilizado o Qdrant.

---

# Vector Search

Busca realizada utilizando embeddings em vez de palavras-chave.

É o mecanismo fundamental utilizado pelo Retrieval em sistemas RAG.
