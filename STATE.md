# STATE

Handoff enxuto entre sessões. Snapshot detalhado: `docs/development/project-state.md`.

## Concluído nesta sessão — PROMPT ENGINEERING (qualidade da resposta no /chat)
Mudança de área: do retrieval (no teto) para a **geração**. Só se mexeu no prompt
(`PromptBuilderService`); retrieval intacto. Decisão registada em **ADR-011**.

- **Problema de medição confirmado (triad saturado para prompt):** Context Relevance
  é question↔chunk (não vê a resposta → invariante ao prompt), Answer Relevance já em
  **1.000** (teto), Groundedness ~0.98. O board seria cego a citações/concisão. E as
  20 perguntas não tinham nenhuma não-respondível → recusa nunca era medida.
- **Instrumento novo (construído ANTES de mexer no prompt):**
  - **Juiz de qualidade** (LLM, Llama, temp 0): 0..1 sobre concisão + clareza +
    atribuição + abstenção.
  - **Métrica de citações** (determinística, sem LLM): valida marcadores `[n]`
    contra as fontes reais; apanha citações inventadas.
  - **Set adversarial** `backend/evaluation/questions_hard.json` (`--hard`): 4
    não-respondíveis, 2 ambíguas, 4 temáticas difíceis. Separado das 20.
  - **Geração a temp 0 no harness** (só avaliação; `/chat` de produção intacto) —
    porque a geração corria a ~0.7 e o ruído de sampling era maior que o efeito do
    prompt.
- **Prompt adotado (v2):** fontes numeradas + citação `[n]` ASCII após cada
  afirmação + "informação indisponível" + cláusula de ambiguidade + síntese concisa.
- **Bug de medição corrigido:** o gerador cita com `【1】` full-width (e `【1†L1-L7】`);
  a regex só apanhava `[1]` ASCII → 0.45 falso. Regex tolerante + prompt exige ASCII.

## Baselines canónicos (juiz Llama, temp 0) — comparar com estes
| Set | ctx | ground | answer | quality | cite |
|---|:-:|:-:|:-:|:-:|:-:|
| **prompt-v2-t0** (standard 20) | 0.530 | 0.965 | 1.000 | 0.864 | **1.000** |
| **prompt-v2-t0-hard** (10) | 0.424 | 0.937 | 0.580 | 0.863 | **1.000** |

- **Ganho limpo = citações** (0.000 → 1.000, sem marcadores inventados). Triad
  estável no ruído; quality quase igual (juiz coarse).
- **`answer=0.580` no set difícil é artefacto:** o juiz de answer-relevance pontua
  uma recusa correta como "não respondeu". No set difícil ler `quality`.
- **Achado do set difícil:** perguntas SEM referente ("Did the club complete the
  signing?") → o modelo **inventa com confiança** (quality 0.25), invisível ao triad.
  Não-respondíveis genuínas já bem tratadas (recusa limpa, 1.0). **Ambiguidade aceite
  como está** por decisão (input degenerado; forçar recusa arrisca over-refusal).

## Estado do working tree (por commitar)
Alterações desta sessão, todas ligadas ao prompt engineering:
- `backend/app/services/prompt_builder_service.py` — prompt de citações (v2).
- `backend/evaluation/`: `judge.py` (juiz de qualidade), `harness.py` (citação
  determinística + temp 0 + metadados), `schemas.py`, `leaderboard.py` (2 colunas),
  `run_eval.py` (`--hard`), `questions_hard.json` (novo).
- Docs: `ADR-011`, `evaluation-results.md`, `project-state.md`, relatório semanal.
- `results/` e `leaderboard.jsonl` são gitignored (não commitar).
- Neste projeto pode-se commitar direto na `main`.

## Produção atual
- **Retrieval:** e5-large-instruct (prefixo instruct na query) → denso top-20 →
  rerank cross-encoder local → top-5. (No teto; não mexer — ADR-008/009.)
- **Geração:** prompt com fontes numeradas + citações `[n]` (ADR-011).

## Próxima tarefa (sugestões, decisão do dev)
1. **Sensibilidade do juiz de qualidade** — se quisermos deltas de prompt finos:
   sub-scores (concisão/clareza/atribuição) ou rúbrica mais dura. (O sinal atual mais
   fiável é a métrica determinística de citações.)
2. **k adaptativo / corte por score do reranker** — menos chunks quando poucos são
   relevantes (subir context relevance).
3. Ground-truth para as temáticas do set difícil (repor recall@k aí).
4. Paralelizar a avaliação de Context Relevance (latência).

## Como correr a avaliação (dentro do container)
```
docker compose exec backend python -m evaluation.run_eval run -e <nome> --rerank          # standard (20)
docker compose exec backend python -m evaluation.run_eval run -e <nome> --rerank --hard    # set adversarial (10)
docker compose exec backend python -m evaluation.run_eval board
```
