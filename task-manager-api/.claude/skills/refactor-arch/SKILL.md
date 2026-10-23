---
name: refactor-arch
description: Analisa, audita e refatora um projeto backend (qualquer linguagem/framework) para o padrão MVC — detecta stack e arquitetura atual, gera um relatório de auditoria de anti-patterns por severidade, e refatora o código para Models/Views-Routes/Controllers após confirmação explícita do usuário, validando que a aplicação continua funcionando.
---

# refactor-arch — Refatoração Arquitetural Automatizada

Você é um especialista em arquitetura de software atuando como auditor e refatorador. Esta skill roda em **3 fases sequenciais e obrigatórias**, nesta ordem, sem pular nenhuma: **Análise → Auditoria (com pausa de confirmação) → Refatoração (com validação)**.

A skill é **agnóstica de tecnologia**: nunca assuma Python/Flask — detecte a stack real do projeto em que você está rodando (cwd é a raiz do projeto-alvo) antes de aplicar qualquer regra.

Leia os arquivos de referência abaixo conforme a fase:
- `references/project-analysis.md` — heurísticas da Fase 1
- `references/anti-patterns-catalog.md` — catálogo usado na Fase 2
- `references/report-template.md` — formato exato do relatório da Fase 2
- `references/architecture-guidelines.md` — regras do MVC alvo, usadas na Fase 3
- `references/refactoring-playbook.md` — padrões de transformação concretos, usados na Fase 3

---

## FASE 1 — Análise

1. Liste os arquivos de código-fonte do projeto (ignore dependências instaladas, caches, artefatos de build e a própria pasta `.claude/`).
2. Aplique as heurísticas de `references/project-analysis.md` para determinar: linguagem, framework (+ versão), dependências relevantes, domínio de negócio, nível de arquitetura atual, número de arquivos-fonte analisados e tabelas/coleções de banco de dados.
3. Imprima o bloco de saída exatamente no formato definido em `references/project-analysis.md` (cabeçalho `PHASE 1: PROJECT ANALYSIS`).

Não avance para a Fase 2 sem ter examinado o conteúdo real de cada arquivo-fonte relevante — resumos superficiais por nome de arquivo não bastam.

## FASE 2 — Auditoria

1. Releia cada arquivo-fonte do projeto e cruze contra **todo** o catálogo em `references/anti-patterns-catalog.md` (os 13 anti-patterns + a tabela de APIs deprecated), mesmo que o projeto já pareça parcialmente organizado.
2. Para cada achado, registre: anti-pattern do catálogo, severidade, arquivo e linha(s) exatas, descrição concreta, impacto e recomendação acionável (ver regras de preenchimento em `references/report-template.md`).
3. Monte o relatório completo seguindo **exatamente** `references/report-template.md`, ordenado por severidade (CRITICAL → HIGH → MEDIUM → LOW).
4. Garanta um mínimo de 5 findings, com pelo menos 1 CRITICAL ou HIGH, 2 MEDIUM e 2 LOW — se o catálogo não render isso num projeto muito limpo, aprofunde a revisão (duplicação sutil, dependências mortas, nomes ruins) antes de concluir que não há mais nada.
5. Salve o relatório em `reports/audit-project-N.md` na raiz do repositório principal (não dentro do projeto-alvo), onde N é o número do projeto sendo auditado nesta execução.
6. **Pare aqui.** Pergunte explicitamente ao usuário:
   ```
   Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
   ```
   Não modifique nenhum arquivo do projeto-alvo até receber confirmação afirmativa explícita.

## FASE 3 — Refatoração

Só execute esta fase após confirmação explícita do usuário na Fase 2.

1. Siga `references/architecture-guidelines.md` para definir a estrutura MVC alvo, **adaptando ao nível de organização que o projeto já tem** — não destrua estrutura que já está correta; não imponha uma estrutura nova a um projeto que já é MVC bem formado.
2. Para cada finding do relatório da Fase 2, aplique a transformação correspondente de `references/refactoring-playbook.md` (ou um padrão equivalente quando a stack real não tiver exemplo direto no playbook).

   **REGRA DE FECHAMENTO (vale para todo finding, sem exceção):** um finding só é considerado resolvido quando o **`Impact` descrito no relatório deixa de ser reproduzível no código gerado**. Mudar a forma — mover para outro arquivo, envolver em classe/função, renomear, criar a pasta certa — **não fecha finding nenhum por si só**.

   Procedimento obrigatório, finding a finding:
   1. Releia o campo `Impact` do relatório (não a `Description`, não a `Recommendation` — o `Impact`).
   2. Declare **qual verificação concreta** prova que aquele impacto cessou. Exemplos de verificação válida: "inseri `maxEntries + 1` itens e o mais antigo foi evictado"; "`grep` mostra 0 queries dentro de loop"; "`POST` anônimo com `{\"role\":\"admin\"}` retornou 403"; "subir sem a env var falhou com erro explícito"; "o endpoint aceita `?page=2` e retorna no máximo `per_page` itens".
   3. Para findings **CRITICAL** e **HIGH**, essa verificação tem que ser **executada de fato** (rodar o comando, bater no endpoint), não presumida por leitura de código.
   4. Se a verificação não passar, o finding continua aberto — relate como pendente no resumo final em vez de marcá-lo como resolvido.

   Cada padrão do playbook traz um bloco **"Nunca faça isto"** com a correção falsa típica daquele anti-pattern e um **checklist de aceite**. Consulte os dois antes de dar o finding por fechado. A tabela "O que significa 'fechado'" no fim do playbook resume as perguntas de fechamento por tipo de impacto.

3. **VARREDURA DE SEGREDOS (etapa obrigatória, independente dos findings).**

   Corrigir apenas os segredos que algum finding nomeia **não basta** — basta um único segredo com default silencioso para o problema de credenciais hardcoded continuar existindo no projeto. Antes de encerrar a Fase 3, faça um inventário exaustivo:

   1. Percorra o código de aplicação procurando por `SECRET`, `TOKEN`, `PASSWORD`, `PASS`, `KEY`, `CREDENTIAL`, `API_KEY`, `SALT`, `AUTH` (ignore dependências instaladas, caches e a pasta `.claude/`). Inclua o que estiver fora do módulo de config.
   2. Classifique **cada** valor encontrado em uma tabela — nenhum item pode ficar sem classificação:

      | Valor | Arquivo:linha | Classificação | Consumido em | Ação |
      |---|---|---|---|---|
      | … | … | `FAIL-CLOSED` / `FAIL-OPEN` / `NÃO-É-SEGREDO` | … | … |

      - **FAIL-CLOSED** — a ausência da variável de ambiente impede o boot. É o estado desejado.
      - **FAIL-OPEN** — existe um default no código que permite subir com um valor visível no repositório. **Precisa ser corrigido**, mesmo que nenhum finding o tenha citado.
      - **NÃO-É-SEGREDO** — porta, host, nome de usuário, e-mail, flag de modo. Não precisa da guarda, mas precisa estar classificado para provar que foi avaliado.
   3. Aplique o checklist do **padrão #1** do playbook a todo item classificado como segredo.

   Duas regras que mudam a classificação:
   - **Reavalie ao introduzir autenticação.** Um segredo fail-open que antes era inócuo vira **CRITICAL** no momento em que a refatoração passa a usá-lo para assinar token/sessão ou como única autenticação — porque qualquer leitor do repositório passa a conseguir forjar credencial. Se esta Fase 3 introduziu assinatura, sessão ou token, reclassifique os segredos existentes **antes** de encerrar.
   - **Segredo sem consumidor é código morto.** Se a varredura mostrar que nada no projeto lê aquele valor, a ação correta é **remover a entrada de config** (padrão #13), não adicionar uma guarda — guardar um segredo que ninguém usa obriga o operador a configurar uma variável inútil.

4. Garanta, ao final, que a estrutura resultante satisfaz o checklist de `references/architecture-guidelines.md` (config extraída, models por domínio, rotas finas, controllers concentrando o fluxo, error handling centralizado, entry point único) **e** que nenhuma regra de negócio crítica (pagamento, autorização, detecção de fraude) ainda decide por heurística trivial previsível.
5. **Valide de verdade, não apenas por leitura de código:**
   - Suba a aplicação com o comando real do projeto (ex.: `python app.py`, `npm start`).
   - Confirme que ela inicia sem erro/exceção no log de boot.
   - Faça pelo menos uma chamada real (curl/requests/http client) a um subconjunto representativo dos endpoints originais e confirme que respondem com o status/formato esperado.
   - Encerre o processo do servidor ao final da validação.
   - Se a Fase 3 tornou algum segredo fail-closed, **teste a guarda de fato**: suba com a variável de ambiente ausente em modo não-desenvolvimento e confirme que a aplicação recusa iniciar.
6. Imprima o resumo final:
   ```
   ================================
   PHASE 3: REFACTORING COMPLETE
   ================================
   ## New Project Structure
   <árvore de diretórios resultante>

   ## Validation
     ✓ Application boots without errors
     ✓ All endpoints respond correctly
     ✓ Zero anti-patterns remaining (ou lista do que ficou pendente e por quê)
     ✓ No simulated critical business logic remains reachable in production mode
     ✓ Every finding's Impact verified as no longer reproducible (not just restructured)
     ✓ Secret sweep: every secret/token classified; zero FAIL-OPEN defaults remaining

   Para o penúltimo item, liste cada finding com a verificação concreta que foi executada, no formato
   `[SEVERIDADE] nome do finding → verificação: <comando/teste> → resultado`. Findings cujo Impact
   não pôde ser verificado devem aparecer como **PENDENTE**, nunca como resolvidos.

   Para o último item, inclua a tabela de inventário de segredos montada no passo 3 — todos os
   valores encontrados, classificados, com a ação tomada em cada um.
   ================================
   ```

## Regras gerais (valem para as 3 fases)

- Nunca pule a pausa de confirmação da Fase 2 — mesmo em execuções automatizadas/não interativas, a pergunta deve ser feita e uma resposta explícita deve ser obtida antes de tocar em arquivos.
- Nunca invente arquivo/linha em um finding — todo número de linha reportado deve corresponder ao conteúdo real lido do arquivo.
- Se o projeto-alvo usa uma stack sem exemplo direto no playbook, aplique os **princípios** de `references/architecture-guidelines.md` e `references/anti-patterns-catalog.md` (eles são agnósticos de linguagem) em vez de recusar a tarefa.
- Preserve o contrato observável da API (mesmos paths e métodos, ou documente explicitamente qualquer mudança de contrato) — o objetivo é reestruturar internamente, não quebrar clientes existentes.
