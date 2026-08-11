# Evolução: de "só RSS" até NewsSource

> Este documento registra, em detalhe técnico, a evolução da camada de fontes
> de notícias do Sports RAG — desde a versão inicial acoplada a RSS até a
> arquitetura atual baseada em `NewsSource` e no padrão Strategy de descoberta.
>
> Ele complementa o `00-project-history.md` (que explica a *motivação*) com o
> **antes e depois concreto** de cada mudança e os commits correspondentes.
>
> O objetivo é registrar o estado real, não funcionalidades futuras.

---

# 1. Ponto de partida — "só RSS"

**Commits:** `e9adede` (create simple feed crud), `6f05c38` (consumes feed rss)

A primeira versão assumia que **toda fonte de notícias era um feed RSS**. Não
havia abstração de origem.

Componentes da época:

- **`Feed`** — entidade de fonte, **sem tipo**. Campos: `id`, `name`, `url`,
  `last_fetched_at`, `created_at`. Tabela `feeds`.
- **`RSSService.parse(url)`** — chamava `feedparser` diretamente e devolvia
  `list[RSSArticle]`.
- **`RSSArticle`** — DTO com o nome acoplado ao RSS.
- **Router `/feeds/{id}/fetch`** — injetava o `RSSService` explicitamente e
  chamava `rss_service.parse(feed.url)`. Ou seja, **a API conhecia o RSS**.

Fluxo:

```text
Feed → RSSService.parse(url) → RSSArticle[] → IngestionService.ingest()
```

Limitação: adicionar qualquer outra forma de descoberta exigiria alterar o
router e a ingestão.

---

# 2. Fase 1 — Padrão Strategy na descoberta

**Commit:** `b2f67ad` (refactor: introduce discovery strategy)
**Correção associada:** `b37ed9f` (fix: defer feed created_at evaluation)

Esta fase **desacoplou a descoberta do RSS**, ainda mantendo o nome `Feed`.

Mudanças concretas:

| Antes | Depois |
|---|---|
| `services/rss_service.py` (`RSSService`) | **removido** → `services/discovery/rss_discovery.py` (`RSSDiscovery`) |
| `dto/rss_article.py` (`RSSArticle`) | renomeado → `dto/source_article.py` (`SourceArticle`) — DTO genérico |
| — | criado o enum **`SourceType`** (`RSS`, `CRAWL`) |
| — | criada a interface **`DiscoveryStrategy`** (ABC) |
| — | criada a **`DiscoveryFactory`** (seleção por `SourceType`) |
| `Feed` sem tipo | `Feed` ganha a coluna `type` (migration `9eba7ba83165`) |
| router injeta `RSSService` | router passa a usar a **factory** para escolher a estratégia |

Resultado: a API e a ingestão deixaram de conhecer o RSS. Toda estratégia de
descoberta passou a produzir a mesma saída, `list[SourceArticle]`, e a seleção
passou a ser responsabilidade única da `DiscoveryFactory`.

Decisão registrada no `docs/decisions/ADR-004-discovery-strategy-pattern.md`.

> O fix `b37ed9f` corrigiu `default=datetime.now()` para `datetime.now` no
> `created_at`: o valor estava sendo avaliado uma única vez no import do módulo,
> em vez de a cada inserção.

---

# 3. Fase 2 — `Feed` → `NewsSource` e estabilização

**Commit:** `c80a6e3` (refactor: complete Feed → NewsSource transition and stabilize RSS architecture)

O nome `Feed` já não descrevia o domínio: a fonte não é mais "um feed RSS", e
sim uma **fonte de notícias com um tipo**. A entidade foi renomeada para
`NewsSource` em **todas as camadas**.

## 3.1 Renomeação

| Camada | Antes | Depois |
|---|---|---|
| Model | `Feed` / tabela `feeds` | `NewsSource` / tabela `news_sources` |
| FK em `Article` | `feed_id` | `news_source_id` |
| Schema | `schemas/feed.py` | `schemas/news_source.py` |
| Repository | `feed_repository.py` | `news_source_repository.py` |
| Service | `feed_service.py` | `news_source_service.py` |
| Router | `/feeds` | `/news-sources` |
| Exceptions | `Feed*` | `NewsSource*` + `UnsupportedNewsSourceType` |
| Migration | — | `3f6a1f2b8c9d` (renomeia tabela e coluna **preservando os dados**) |

A migration usa `rename_table` e renomeação de coluna (não recria estruturas),
portanto **não há perda de dados** existentes. Encaixa-se no head anterior
(`9eba7ba83165`) e possui `downgrade` simétrico.

## 3.2 Estabilizações

- **CRAWL bloqueado na criação** — `NewsSourceService` rejeita qualquer tipo
  diferente de RSS com `UnsupportedNewsSourceType` (HTTP 400), em vez de aceitar
  e falhar depois no fetch.
- **`DiscoveryFactory`** passou a lançar a exceção de domínio
  `UnsupportedNewsSourceType` em vez de um `ValueError` cru.
- **Testes mínimos** adicionados para `NewsSourceService` (criação RSS, rejeição
  de CRAWL, URL duplicada, not-found) e `DiscoveryFactory` (RSS retorna
  `RSSDiscovery`, tipo não suportado).
- **Limpeza** — removido o método morto `NewsSourceRepository.get_by_id`.

## 3.3 Documentação da transição

**Commit:** `f322f35` (docs: update project state after NewsSource transition)

Atualização de `project-state.md`, `architecture.md` e `roadmap.md` para
refletir o estado real após a conclusão da transição. O `erd.md` já havia sido
reescrito dentro de `c80a6e3`.

---

# 4. Arquitetura atual

```text
NewsSource (SourceType: RSS | CRAWL)
      │
      ▼
DiscoveryFactory.get(news_source)     ← seleciona a estratégia pelo tipo
      │
      ▼
RSSDiscovery.discover()               ← única estratégia funcional hoje
      │
      ▼
list[SourceArticle]                   ← DTO comum da camada Discovery
      │
      ▼
IngestionService.ingest()             ← independente da origem da descoberta
      │
      ▼
Extração → Cleaning → Chunking → Embeddings → PostgreSQL + Qdrant
```

Fatos do estado atual:

- `Feed` foi totalmente substituído por `NewsSource`.
- `SourceType` define `RSS` e `CRAWL`.
- `RSS` é a **única** estratégia funcional.
- `DiscoveryFactory` é o único ponto de seleção de estratégia.
- `RSSDiscovery` implementa a descoberta via RSS.
- `SourceArticle` é o DTO comum da camada Discovery.
- `IngestionService` é independente da origem da descoberta.
- `CRAWL` existe como **preparação arquitetural**; a criação de uma
  `NewsSource` do tipo CRAWL é bloqueada enquanto não existir `CrawlDiscovery`.
- A arquitetura multi-source está preparada para receber novas estratégias sem
  alterar o restante da pipeline.

---

# 5. Pendências conhecidas

Não implementado até o momento:

- `CrawlDiscovery` (Crawl4AI ainda não foi implementado);
- normalização de datas (`published_at` ainda chega sempre como `None` a partir
  da descoberta RSS);
- normalização de metadados entre provedores diferentes.

---

# 6. Linha do tempo (commits)

```text
e9adede  create simple feed crud            ← Feed CRUD inicial
6f05c38  consumes feed rss                   ← consumo RSS acoplado
...
b2f67ad  refactor: introduce discovery strategy   ← Fase 1 (Strategy)
b37ed9f  fix: defer feed created_at evaluation
...
c80a6e3  refactor: complete Feed → NewsSource ...  ← Fase 2 (rename + estabilização)
f322f35  docs: update project state after NewsSource transition
```

---

# 7. Referências

- `docs/decisions/ADR-004-discovery-strategy-pattern.md`
- `docs/architecture/architecture.md`
- `docs/architecture/data-flow.md`
- `docs/architecture/erd.md`
- `docs/project-history/00-project-history.md` (motivação e narrativa geral)
