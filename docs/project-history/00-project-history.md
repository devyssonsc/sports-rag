# Project History

> Este documento registra toda a evolução do projeto **Sports RAG**, desde sua concepção até o estado atual.
>
> O objetivo deste documento não é explicar como o sistema funciona hoje, mas sim explicar **por que ele funciona da forma atual**.
>
> Todas as decisões arquiteturais, mudanças de direção e aprendizados importantes devem ser registrados aqui.

---

# 1. Sobre o projeto

## Nome

Sports RAG

## Objetivo principal

O principal objetivo deste projeto é **aprender profundamente como sistemas Retrieval-Augmented Generation (RAG) funcionam internamente**.

O projeto **não tem como objetivo principal construir um produto comercial**, mas sim servir como uma plataforma de estudo de arquitetura de IA moderna.

Durante o desenvolvimento, o entendimento dos conceitos sempre possui prioridade sobre velocidade de implementação.

---

# 2. Filosofia de desenvolvimento

Desde o início do projeto foi definida uma filosofia bastante clara.

Sempre que possível:

- compreender primeiro o conceito;
- implementar manualmente;
- somente depois utilizar frameworks que abstraem parte da implementação.

Frameworks não são evitados.

Eles são adotados quando:

- reduzem código repetitivo;
- seguem boas práticas;
- aumentam produtividade;

desde que a abstração não impeça o entendimento do funcionamento interno.

Exemplo:

Inicialmente foi implementado um algoritmo próprio de chunking para compreender:

- divisão do texto;
- overlap;
- tamanho dos chunks;
- problemas causados por cortes incorretos.

Somente depois foi adotado o **LlamaIndex SentenceSplitter**, já entendendo exatamente quais problemas ele resolvia.

Essa filosofia deverá continuar sendo seguida durante todo o projeto.

---

# 3. Arquitetura escolhida

Desde o início decidiu-se utilizar uma arquitetura em camadas.

A estrutura principal do projeto é organizada em:

- API
- Schemas
- Services
- Repositories
- Models
- DTOs

O projeto não utiliza DDD ou Clean Architecture completa.

Essa decisão foi tomada para manter a arquitetura simples durante o aprendizado.

---

# 4. Primeira etapa: ingestão de notícias

A primeira versão do projeto possuía apenas uma origem de dados:

RSS.

Foi implementado um serviço responsável por:

- consumir feeds RSS;
- transformar cada item em um DTO;
- iniciar o processo de ingestão.

Neste momento acreditava-se que RSS seria suficiente para a maioria dos sites.

---

# 5. Extração do conteúdo

Os feeds RSS normalmente não contêm o conteúdo completo das notícias.

Foi necessário implementar uma etapa de extração.

Inicialmente foi avaliada a utilização de parsing manual de HTML.

Após pesquisa foi adotado o **Trafilatura**, pois apresentou excelente qualidade de extração para notícias esportivas.

A decisão foi mantida após testes com diferentes fontes (ESPN e BBC Sport).

Até o momento o Trafilatura continua sendo o mecanismo oficial de extração de conteúdo.

---

# 6. Primeiro algoritmo de chunking

O projeto começou utilizando um algoritmo próprio de chunking.

Esse algoritmo existia principalmente para compreender:

- tamanho dos chunks;
- overlap;
- perda de contexto;
- problemas causados por cortes arbitrários.

Durante os testes foram identificados diversos problemas:

- cortes em locais inadequados;
- quebras de linha;
- dificuldade para manter contexto entre chunks.

Após compreender esses conceitos decidiu-se abandonar a implementação manual.

---

# 7. Migração para o LlamaIndex

Foi adotado o **SentenceSplitter** do LlamaIndex.

Essa decisão foi tomada porque:

- produz chunks semanticamente mais coerentes;
- respeita limites de tokens;
- evita cortes no meio de frases;
- mantém overlap automaticamente.

A adoção do framework aconteceu somente após o entendimento completo do problema.

---

# 8. Embeddings

Após o chunking foi implementada a geração de embeddings.

Os objetivos dessa etapa eram compreender:

- representação vetorial;
- dimensionalidade;
- similaridade semântica;
- preparação para busca vetorial.

Foi utilizado o Together AI para geração dos embeddings.

Durante essa etapa também foi necessário ajustar o tamanho dos chunks para respeitar o limite do modelo escolhido.

---

# 9. Banco vetorial

Foi escolhido o Qdrant.

Antes da implementação foram estudados:

- collections;
- points;
- payloads;
- busca por similaridade.

Durante esse processo foi compreendido como os vetores são armazenados e comparados utilizando índices vetoriais.

A persistência passou a ocorrer em dois locais:

PostgreSQL

- dados estruturados

Qdrant

- embeddings

---

# 10. Busca vetorial

Após concluir a ingestão foi implementado o Retrieval.

Fluxo:

Pergunta

↓

Embedding

↓

Qdrant

↓

Chunks

↓

PostgreSQL

↓

Contexto

Esse fluxo foi implementado manualmente para compreender cada etapa.

---

# 11. Implementação do pipeline RAG

Depois da recuperação de contexto foi implementada a etapa de geração.

Foram criados:

- RetrievalService
- PromptBuilderService
- LLMService
- ChatService

O objetivo era manter cada responsabilidade isolada.

O pipeline passou a ser:

Pergunta

↓

Embedding

↓

Busca vetorial

↓

Contexto

↓

Prompt

↓

LLM

↓

Resposta

---

# 12. Qualidade da recuperação

Diversos testes foram realizados.

Foram avaliados:

- qualidade dos chunks;
- tamanho dos chunks;
- overlap;
- qualidade da recuperação;
- respostas da LLM.

Também foram feitas melhorias no PromptBuilder.



# 13. Evolução da camada de descoberta de notícias

Durante a expansão do projeto percebeu-se que muitos sites esportivos apresentam limitações na disponibilização de conteúdo através de RSS.

Os principais problemas encontrados foram:

- ausência completa de feeds RSS;
- feeds incompletos;
- feeds desatualizados;
- limitação na quantidade de notícias publicadas.

Inicialmente foi considerada a utilização do Google News como mecanismo complementar de descoberta.

Após alguns testes essa alternativa foi descartada devido à baixa qualidade dos resultados, excesso de conteúdo irrelevante e pouca previsibilidade sobre quais notícias seriam retornadas.

Durante essa pesquisa surgiu o Crawl4AI.

Inicialmente acreditava-se que ele seria utilizado para substituir o processo de extração de conteúdo.

Após estudar melhor sua arquitetura concluiu-se que seu maior valor para este projeto está em outra etapa da pipeline.

O Crawl4AI será utilizado como **mais um mecanismo de descoberta de notícias**.

Ou seja, o sistema passará a possuir múltiplas estratégias de descoberta.

Exemplo:

RSS

↓

lista de URLs

ou

Crawl4AI

↓

lista de URLs

Independentemente da estratégia utilizada, o resultado esperado será sempre uma coleção de artigos descobertos.

Depois dessa etapa toda a pipeline permanece exatamente igual.

Lista de artigos

↓

ContentExtractionService

↓

TextCleaningService

↓

Chunking

↓

Embeddings

↓

Qdrant

↓

Retrieval

↓

LLM

Essa decisão foi importante porque mantém completamente desacopladas as responsabilidades de:

- descobrir novas notícias;
- extrair o conteúdo da notícia;
- processar o texto;
- armazenar vetores;
- responder perguntas.

No futuro, adicionar uma nova estratégia de descoberta exigirá apenas implementar uma nova classe seguindo a interface `DiscoveryStrategy`, sem necessidade de alterar o restante da pipeline.


## Motivação da refatoração

Originalmente a arquitetura assumia que toda notícia seria descoberta através de RSS.

Essa premissa deixou de ser verdadeira conforme novas fontes foram sendo adicionadas ao projeto.

Para evitar que cada novo mecanismo de descoberta exigisse alterações na pipeline de ingestão, foi criada uma camada de abstração responsável exclusivamente por descobrir artigos.

Essa camada passou a utilizar o padrão Strategy, permitindo que diferentes mecanismos de descoberta coexistam de forma transparente para o restante da aplicação.


# 14. Refatoração da camada de descoberta

A arquitetura deixou de assumir que toda notícia vem de RSS.

Foi introduzido o conceito de múltiplas estratégias de descoberta.

Foram criados:

SourceType

SourceArticle

DiscoveryStrategy

RSSDiscovery

DiscoveryFactory

Essa mudança permitiu que o restante da pipeline permanecesse completamente inalterado.

No futuro serão adicionadas novas estratégias como:

- CrawlDiscovery
- APIs
- outras fontes.

---

# 15. Filosofia arquitetural

Uma regra importante do projeto é:

Sempre que possível, novas funcionalidades devem ser adicionadas sem alterar o restante da pipeline.

O objetivo é que:

Discovery

↓

Extraction

↓

Chunking

↓

Embedding

↓

Retrieval

↓

Generation

permaneçam desacoplados.

---

# 16. Situação atual

O projeto atualmente possui:

- ingestão de notícias;
- extração de conteúdo;
- limpeza de texto;
- chunking semântico;
- embeddings;
- armazenamento vetorial;
- recuperação semântica;
- geração de respostas;
- arquitetura preparada para múltiplas fontes de descoberta.

---

# 17. Próximos passos

A refatoração da camada Discovery e a transição `Feed` → `NewsSource` foram
**concluídas** (commit `c80a6e3`). Os detalhes técnicos dessa evolução, com o
antes e depois de cada camada, estão registrados em `01-rss-to-newssource.md`.

Os próximos objetivos previstos são:

- integrar Crawl4AI (implementar `CrawlDiscovery`);
- adicionar novas fontes de notícias;
- normalizar datas;
- normalizar metadados;
- evoluir continuamente a qualidade da recuperação.
