# Criação de Skills — Refatoração Arquitetural Automatizada

> Documentação da entrega (Gabriel Augusto). O enunciado original do desafio está preservado abaixo, a partir de "## Objetivo", para referência.

## A) Análise Manual

Análise de código feita antes de construir a skill, para entender os problemas que ela precisaria detectar. Critério de severidade conforme a escala definida no enunciado (seção "Definição de Severidades").

### Projeto 1 — code-smells-project (Python/Flask)

| Severidade | Problema | Localização | Por que é relevante |
|---|---|---|---|
| CRITICAL | SQL Injection com bypass de autenticação | `models.py:109-111` (`login_usuario`) | Concatenação direta de `email`/`senha` na query permite logar como qualquer usuário (`' OR '1'='1' --`) sem credenciais. |
| CRITICAL | Endpoint `/admin/query` executa SQL arbitrário do body, sem auth | `app.py:59-78` | Qualquer cliente pode ler, alterar ou apagar qualquer dado do banco — equivalente a um shell SQL público. |
| CRITICAL | `SECRET_KEY` hardcoded e vazado no `/health` junto com `debug=True` | `app.py:7-8`, `controllers.py:286-289` | A chave de sessão Flask fica exposta tanto no código-fonte quanto em uma rota pública. |
| HIGH | Senhas armazenadas em texto puro | `models.py:122-131`, seed em `database.py:75-79` | Vazamento do banco expõe todas as senhas diretamente, incluindo a de uma conta admin. |
| HIGH | God Module: dados + regra de negócio + relatório de 3 domínios no mesmo arquivo | `models.py` (314 linhas) | Impossível testar em isolamento; qualquer mudança em um domínio arrisca efeito colateral nos outros. |
| MEDIUM | N+1 (N×M+1) aninhado ao montar pedidos | `models.py:171-233` | Para N pedidos com M itens, executa `1+N+N×M` queries em vez de uma única com JOIN. |
| MEDIUM | Código quase idêntico duplicado entre `get_pedidos_usuario` e `get_todos_pedidos` | `models.py:171-201` vs `203-233` | Qualquer correção precisa ser replicada manualmente nos dois lugares. |
| LOW | Números mágicos nas faixas de desconto | `models.py:256-262` | Regra de negócio importante escondida em literais sem nome. |
| LOW | `print()` como logging, incluindo email do usuário no login | `controllers.py:179,182` | Sem nível/destino de log configurável; dado potencialmente sensível em stdout. |

Relatório completo (18 findings): [`reports/audit-project-1.md`](reports/audit-project-1.md).

### Projeto 2 — ecommerce-api-legacy (Node.js/Express)

| Severidade | Problema | Localização | Por que é relevante |
|---|---|---|---|
| CRITICAL | Segredos hardcoded (senha de banco, chave de gateway de pagamento) | `src/utils.js:2-6` | Qualquer acesso ao repo expõe credenciais de "produção" sem possibilidade de rotação sem novo deploy. |
| CRITICAL | 3 rotas sem autenticação/autorização (checkout, relatório financeiro, delete de usuário) | `src/AppManager.js:28,80,131` | Qualquer chamador anônimo vê receita de todos os alunos e pode apagar qualquer usuário. |
| CRITICAL | Cartão de crédito completo e chave de pagamento logados em texto puro | `src/AppManager.js:45` | Violação direta de boas práticas de PCI-DSS — dado de cartão nunca deveria aparecer em log. |
| HIGH | "Criptografia" de senha falsa e reversível (`badCrypto`) | `src/utils.js:17-23` | Base64 repetido não é hash — senha recuperável instantaneamente. |
| HIGH | Lógica de pagamento falsa — qualquer cartão começando com "4" é aprovado | `src/AppManager.js:46` | Regra de negócio crítica (aprovação de pagamento) é trivialmente manipulável. |
| MEDIUM | N+1 (N×M+1) no relatório financeiro | `src/AppManager.js:83-126` | Para C cursos e E matrículas/curso, gera `1+C+2CE` round-trips em vez de um JOIN. |
| MEDIUM | Callback hell sem transação — matrícula pode ficar sem pagamento correspondente | `src/AppManager.js:37-77` | Se o insert de pagamento falhar após a matrícula já criada, não há rollback. |
| LOW | Estado global mutável (`globalCache` cresce sem limite; `totalRevenue` nunca atualizado) | `src/utils.js:9-10` | Vazamento de memória não limitado e estado morto enganoso. |
| LOW | Nomes de variáveis de 1-2 letras no fluxo de checkout | `src/AppManager.js:29-33` | Reduz legibilidade e aumenta risco de troca acidental de variável. |

Relatório completo (16 findings): [`reports/audit-project-2.md`](reports/audit-project-2.md).

### Projeto 3 — task-manager-api (Python/Flask, parcialmente organizado)

| Severidade | Problema | Localização | Por que é relevante |
|---|---|---|---|
| CRITICAL | Nenhuma rota valida o token emitido no login | `routes/user_routes.py:185-211` (emissão), zero verificação em qualquer outra rota | O login existe só de fachada — toda a API de CRUD está, na prática, aberta a qualquer chamador. |
| CRITICAL | Hash de senha com MD5 sem salt | `models/user.py:29,31-32` | MD5 é quebrado para senhas — vazamento do banco expõe credenciais em minutos. |
| HIGH | Hash de senha vazado nas respostas da API | `models/user.py:16-25`, `routes/user_routes.py:33,85-86,129,209` | `to_dict()` inclui o campo de senha, devolvido em 4 rotas diferentes. |
| HIGH | Lógica correta existe mas nunca é chamada; mesma regra duplicada manualmente 5-6x | `models/task.py:38-60`, `utils/helpers.py` (quase todo o arquivo) vs. `routes/task_routes.py`, `routes/report_routes.py` | Qualquer correção de regra (ex.: "atrasado") precisa ser replicada em 5-6 lugares com risco de divergência. |
| MEDIUM | Queries N+1 | `routes/task_routes.py:41-56`, `routes/report_routes.py:56,163` | Busca de relação (usuário/categoria) feita dentro de loop por item em vez de JOIN/agregação. |
| MEDIUM | `except:` genérico silenciando erros reais | `routes/task_routes.py:62,236`, `routes/user_routes.py:130,149`, `routes/report_routes.py:186,207,221` | Bugs de programação viram "erro genérico" sem log, difícil de diagnosticar. |
| LOW | Dependências declaradas e nunca usadas (`marshmallow`, `requests`, `python-dotenv`) | `requirements.txt:4-6` | `python-dotenv` é exatamente a ferramenta que resolveria o segredo hardcoded, mas nunca é importada. |
| LOW | `datetime.utcnow()` (API deprecated desde Python 3.12) usado de forma pervasiva | `models/task.py:15,16,52`, `models/user.py:14`, várias rotas | Warnings hoje, quebra garantida quando o método for removido. |

Relatório completo (18 findings): [`reports/audit-project-3.md`](reports/audit-project-3.md).

## B) Construção da Skill

A skill vive em `.claude/skills/refactor-arch/` (criada dentro de `code-smells-project/` e copiada, sem alterações, para os outros dois projetos).

**Decisões de design do `SKILL.md`:** o arquivo principal é deliberadamente curto — ele só orquestra as 3 fases e aponta para os 5 arquivos de referência, sem duplicar conhecimento de domínio neles. Cada fase tem uma seção própria com um checklist de saída (o formato exato do bloco impresso, quando aplicável) para reduzir ambiguidade sobre "o que significa terminar a fase 1/2/3". A pausa de confirmação da Fase 2 é descrita como uma regra inquebrável tanto no `SKILL.md` quanto no `report-template.md`, para que não dependa de uma única instrução isolada.

**Arquivos de referência e por quê:**
- `project-analysis.md` — heurísticas mecânicas (manifesto de dependência → framework; import de driver → banco; pastas `models/routes/controllers` → nível de arquitetura) para que a Fase 1 não dependa de "achismo".
- `anti-patterns-catalog.md` — 13 anti-patterns (acima do mínimo de 8), cobrindo as 4 severidades, com uma tabela dedicada de APIs/padrões deprecated (driver `sqlite3` callback-only, `datetime.utcnow()`, MD5 para senha, `debug=True` em produção, CORS aberto). Cada anti-pattern tem um "sinal de detecção" objetivo (ex.: "concatenação de string/f-string em `cursor.execute`") em vez de descrição vaga, incluindo uma nota explícita de falso-positivo (f-string dentro de `.like()` do SQLAlchemy não é SQLi).
- `report-template.md` — formato exato do relatório (o mesmo do exemplo do enunciado) e as regras de preenchimento (ordenação por severidade, arquivo:linha exatos, não resumir em categorias vagas).
- `architecture-guidelines.md` — regras do MVC alvo descritas por responsabilidade de camada, não por nome de pasta específico de um framework, com notas específicas de Flask (Blueprints) e Express (Router) só no final. Inclui uma seção explícita de "adaptação ao nível de organização existente" — para o projeto 3, que já tinha `models/routes/services/utils`.
- `refactoring-playbook.md` — 13 padrões de transformação (acima do mínimo de 8) com exemplos antes/depois em Python **e** JavaScript lado a lado, para deixar claro que o padrão é conceitual, não ligado a uma sintaxe.

**Como garanti agnosticismo de tecnologia:** nenhum arquivo de referência cita nome de arquivo específico de um projeto; as heurísticas são baseadas em sinais genéricos (manifesto de dependência, import de driver, nome de pasta) e os exemplos de código cobrem as duas linguagens dos 3 projetos-alvo (Python e JavaScript) lado a lado em cada padrão do playbook. A prova real de agnosticismo foi prática: a mesma cópia literal da skill (sem nenhuma edição) foi usada para auditar e refatorar um monolito Flask, uma API Express com callback hell, e um Flask parcialmente organizado — com resultados corretos nos 3.

**Desafios encontrados:**
1. *Severidade do "God Class" em `models.py` do projeto 1*: a definição do enunciado liga CRITICAL a "banco de dados + lógica + roteamento no mesmo arquivo". `models.py` mistura banco+lógica mas não roteamento (que está em `app.py`). Resolvi classificando como HIGH e documentando a diferença no próprio catálogo, para a skill aplicar o critério com rigor em vez de copiar cegamente o exemplo do enunciado.
2. *Checkout público no projeto 2*: o achado inicial listava `/api/checkout` junto com as 2 rotas administrativas como "sem autenticação". Na Fase 3, decidi **não** exigir login no checkout (é um fluxo de auto-atendimento de compra, como um e-commerce real) e, em vez disso, endureci validação de entrada, removi o log de dados sensíveis e adicionei transação — mantendo `requireAdmin` só nas 2 rotas genuinamente administrativas. Documentei essa adaptação explicitamente para não parecer que um finding foi ignorado sem motivo.
3. *Datas aware vs. naive no projeto 3*: substituir `datetime.utcnow()` (deprecated) por `datetime.now(timezone.utc)` quebra comparações com `due_date` (armazenado naive via `strptime`). Resolvido com um helper único `utcnow_naive()` em `utils/helpers.py`, usado em todo o projeto — elimina a chamada deprecated sem mudar o comportamento observável.

## C) Resultados

### Resumo dos relatórios de auditoria

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|---|---|---|
| 1 — code-smells-project | 7 | 4 | 4 | 3 | 18 |
| 2 — ecommerce-api-legacy | 5 | 4 | 4 | 3 | 16 |
| 3 — task-manager-api | 4 | 4 | 6 | 4 | 18 |

### Estrutura antes/depois

**Projeto 1** — de 4 arquivos (`app.py`, `controllers.py`, `models.py`, `database.py`) sem nenhuma separação, para:
```
config/settings.py, database.py, models/{produto,usuario,pedido}_model.py,
services/{pedido,relatorio,notification}_service.py, utils/validators.py,
controllers/{produto,usuario,pedido,sistema}_controller.py, views/routes.py,
middlewares/error_handler.py, app.py (composition root)
```
Os endpoints `/admin/reset-db` e `/admin/query` (execução de SQL arbitrário sem auth) foram **removidos** — eram vulnerabilidades CRITICAL sem uso legítimo em produção, não "funcionalidade a preservar".

**Projeto 2** — de 3 arquivos (`app.js`, `AppManager.js` como God Class, `utils.js`) para:
```
src/config/settings.js, src/database/db.js (sqlite3 promisificado),
src/models/{user,course,enrollment,payment,report}Model.js,
src/services/{checkout,report,cache,paymentGateway}Service.js,
src/controllers/{checkout,report,user}Controller.js,
src/middlewares/{errorHandler,requireAdmin}.js, src/routes/index.js, src/app.js
```
Mesmas 3 rotas da API original preservadas (contrato observável intacto); `financial-report` e `DELETE /users/:id` agora exigem header `X-Admin-Token`.

**Projeto 3** — manteve `models/`, `routes/`, `services/`, `utils/` já existentes (não foram destruídos), **adicionando** a camada de `controllers/` que faltava e um `config/` e `middlewares/` novos:
```
config/settings.py (novo), controllers/{task,user,category,report,sistema}_controller.py (novo),
middlewares/{auth,error_handler}.py (novo), models/ (corrigido), routes/ (emagrecidas,
delegam para controllers/), services/notification_service.py (conectado, antes era código morto)
```

### Checklist de validação

**Fase 1 — Análise** (3/3 projetos)
- [x] Linguagem detectada corretamente (Python nos projetos 1 e 3, JavaScript/Node no projeto 2)
- [x] Framework detectado corretamente (Flask 3.1.1 / Express 4.18.2 / Flask 3.0.0+SQLAlchemy)
- [x] Domínio descrito corretamente (E-commerce / LMS com checkout / Task Manager)
- [x] Número de arquivos analisados condiz com a realidade (4 / 3 / 16)

**Fase 2 — Auditoria** (3/3 projetos)
- [x] Relatório segue o template de `report-template.md`
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings (18 / 16 / 18)
- [x] Detecção de APIs deprecated incluída (driver `sqlite3` callback-only no projeto 2; `datetime.utcnow()` no projeto 3)
- [x] Skill pausou e pediu confirmação explícita antes da Fase 3 nos 3 projetos

**Fase 3 — Refatoração** (3/3 projetos)
- [x] Estrutura de diretórios segue padrão MVC
- [x] Configuração extraída para módulo de config, sem hardcoded
- [x] Models criados/corrigidos para abstrair dados
- [x] Views/Routes separadas e finas
- [x] Controllers concentram o fluxo
- [x] Error handling centralizado
- [x] Entry point claro
- [x] Aplicação inicia sem erros (3/3, boot logs abaixo)
- [x] Endpoints originais respondem corretamente (3/3, chamadas reais via curl)

### Logs de validação (saída real capturada durante a Fase 3)

**Projeto 1** — boot + bypass de SQLi corrigido:
```
2026-10-07 18:30:03 INFO __main__ Servidor iniciado em http://0.0.0.0:5000
 * Debug mode: off
$ curl -X POST /login -d '{"email":"'\'' OR '\''1'\''='\''1","senha":"x"}'
{"erro":"Email ou senha inválidos","sucesso":false}
$ curl -X POST /admin/reset-db   →  404 (endpoint removido)
```

**Projeto 2** — checkout, relatório admin e cascade delete:
```
LMS API rodando na porta 3000...
$ curl -X POST /api/checkout (cartão "4...")  → {"msg":"Sucesso","enrollment_id":2}
$ curl /api/admin/financial-report  (sem token)  → 401
$ curl /api/admin/financial-report  (com X-Admin-Token)
  → [{"course":"Clean Architecture","revenue":997,...},{"course":"Docker","revenue":497,...}]
$ curl -X DELETE /api/users/1 (com token) → matrícula/pagamento de Leonan removidos em cascata
```

**Projeto 3** — autenticação real e controle de papéis:
```
Servidor iniciado em http://0.0.0.0:5000
$ curl /tasks (sem token)  → 401
$ curl -X POST /login {"email":"joao@email.com","password":"1234"}
  → token assinado (itsdangerous), role "admin"
$ curl /users (com token de usuário comum "maria")  → 403
$ curl /users (com token de admin)  → lista completa, SEM campo "password"
```

### Observações sobre o comportamento em stacks diferentes

A mesma skill, copiada sem nenhuma edição, funcionou nos 3 projetos. A principal diferença de comportamento entre eles foi na **Fase 3**, exatamente como esperado pelas guidelines de arquitetura: no projeto 1 (monolito) a skill criou a estrutura de pastas do zero; no projeto 2 (Node/Express) ela promisificou o driver `sqlite3` e isolou o "mock" de gateway de pagamento como peça substituível; no projeto 3 (Flask parcialmente organizado) ela **não recriou** `models/routes/services/utils`, apenas adicionou a camada de `controllers/` que faltava e religou código já existente mas morto (`is_overdue()`, `process_task_data()`, `NotificationService`). Isso confirma que o catálogo de anti-patterns e o playbook, por serem descritos em termos de sinais e princípios (não de sintaxe), generalizam entre Python e JavaScript sem adaptação manual.

## D) Como Executar

**Pré-requisitos:** Claude Code instalado e autenticado; Python 3.11+ e `pip`; Node.js 18+ e `npm`.

**Ordem de execução sugerida** (a mesma usada nesta entrega):

```bash
# Projeto 1 — Python/Flask
cd code-smells-project
pip install -r requirements.txt
claude "/refactor-arch"

# Projeto 2 — Node.js/Express (copie a skill antes, se ainda não estiver lá)
cd ../ecommerce-api-legacy
npm install
claude "/refactor-arch"

# Projeto 3 — Python/Flask parcialmente organizado
cd ../task-manager-api
pip install -r requirements.txt
claude "/refactor-arch"
```

Em cada projeto, a skill: imprime o resumo da Fase 1, gera e salva o relatório de auditoria da Fase 2 em `reports/audit-project-N.md` e **pausa pedindo confirmação explícita** antes de tocar em qualquer arquivo — responda `y`/afirmativo para prosseguir à Fase 3.

**Como validar que a refatoração funcionou**, após a Fase 3 de cada projeto:

```bash
# Projeto 1
cd code-smells-project && python app.py &
curl http://localhost:5000/health
curl http://localhost:5000/produtos

# Projeto 2
cd ecommerce-api-legacy && npm start &
curl -X POST http://localhost:3000/api/checkout -H "Content-Type: application/json" \
  -d '{"usr":"Teste","eml":"teste@x.com","c_id":1,"card":"4111222233334444"}'

# Projeto 3
cd task-manager-api && python seed.py && python app.py &
TOKEN=$(curl -s -X POST http://localhost:5000/login -H "Content-Type: application/json" \
  -d '{"email":"joao@email.com","password":"1234"}' | python -c "import sys,json;print(json.load(sys.stdin)['token'])")
curl http://localhost:5000/tasks -H "Authorization: Bearer $TOKEN"
```

Se a aplicação sobe sem erro e os endpoints acima respondem com `200`, a refatoração está íntegra.

---

# Enunciado Original do Desafio

Ao longo do curso você aprendeu o que são Skills e como elas permitem que um agente de IA atue como um especialista em tarefas específicas. Agora imagine o seguinte cenário: você herdou 3 projetos legados com problemas de arquitetura, segurança e qualidade de código. Revisar e corrigir tudo manualmente levaria dias.

Neste desafio, você vai criar uma Skill que automatiza esse processo — analisando, auditando e refatorando qualquer projeto para o padrão MVC, independente da tecnologia.

## Objetivo

Você deve entregar uma Skill capaz de:

- Analisar uma codebase detectando linguagem, framework e arquitetura atual
- Identificar anti-patterns e code smells, classificando por severidade com arquivo e linha exatos
- Gerar um relatório de auditoria estruturado com todos os achados
- Refatorar o projeto para o padrão MVC (Model-View-Controller), eliminando os problemas encontrados
- Validar o resultado garantindo que a aplicação continua funcionando após as mudanças

A skill deve ser agnóstica de tecnologia, funcionando com diferentes linguagens e frameworks.

## Contexto

### Definição de Severidades

Para padronizar a sua auditoria e os relatórios gerados pela IA, utilize a seguinte escala de classificação baseada em problemas de MVC e SOLID:

- **CRITICAL:** Falhas graves de arquitetura ou segurança que impedem o funcionamento correto, expõem dados sensíveis (ex: credenciais hardcoded, SQL Injection) ou violam completamente a separação de responsabilidades (ex: "God Class" contendo banco de dados, lógicas complexas e roteamento no mesmo arquivo).
- **HIGH:** Fortes violações do padrão MVC ou princípios SOLID que dificultam muito a manutenção e testes (ex: lógicas de negócio pesadas presas dentro de Controllers, forte acoplamento sem Injeção de Dependência, ou uso de estado global mutável em toda a aplicação).
- **MEDIUM:** Problemas de padronização, duplicação de código ou gargalos de performance moderada (ex: Queries N+1 no banco de dados, uso inadequado de middlewares, validações ausentes nas rotas).
- **LOW:** Melhorias de legibilidade, nomenclatura de variáveis ruins, ou "magic numbers" soltos pelo código.

### Exemplo de Uso no CLI

```bash
# Executar a skill no projeto com problemas
cd code-smells-project
claude "/refactor-arch"
```

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:      Flask 3.1.1
Dependencies:  flask-cors
Domain:        E-commerce API (produtos, pedidos, usuários)
Architecture:  Monolítica — tudo em 4 arquivos, sem separação de camadas
Source files:  4 files analyzed
DB tables:     produtos, usuarios, pedidos, itens_pedido
================================
```

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask
Files:   4 analyzed | ~800 lines of code

## Summary
CRITICAL: 4 | HIGH: 5 | MEDIUM: 2 | LOW: 3

## Findings

### [CRITICAL] God Class / God Method
File: models.py:1-350
Description: Arquivo único contém toda lógica de negócio, queries SQL, validação e formatação para 4 domínios diferentes.
Impact: Impossível testar em isolamento, qualquer mudança afeta tudo.
Recommendation: Separar em models e controllers por domínio.

### [CRITICAL] Hardcoded Credentials
File: app.py:8
Description: SECRET_KEY hardcoded como 'minha-chave-super-secreta-123'
...

================================
Total: 14 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y
```

```
[... refatoração executada ...]

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
src/
├── config/settings.py
├── models/
│   ├── produto_model.py
│   └── usuario_model.py
├── views/
│   └── routes.py
├── controllers/
│   ├── produto_controller.py
│   └── pedido_controller.py
├── middlewares/error_handler.py
└── app.py (composition root)

## Validation
  ✓ Application boots without errors
  ✓ All endpoints respond correctly
  ✓ Zero anti-patterns remaining
================================
```

## Tecnologias obrigatórias

- **Ferramenta:** uma das três opções abaixo (não são aceitas outras ferramentas):
  - Claude Code
  - Gemini CLI
  - OpenAI Codex
- **Recurso:** Custom Skills (ou o equivalente na ferramenta escolhida)
- **Formato dos arquivos de referência:** Markdown
- **Projetos-alvo:** Python/Flask (2 projetos) e Node.js/Express (1 projeto) (fornecidos no repositório base)

> **Nota sobre a ferramenta:** Os exemplos deste documento usam o Claude Code (`.claude/skills/`) como referência, pois é a ferramenta utilizada no curso. Se você optar por Gemini CLI ou Codex, adapte o nome da pasta e o comando de invocação conforme a convenção dela — o conceito de skill e a estrutura interna (SKILL.md + arquivos de referência) permanecem os mesmos.

## Requisitos

### 1. Análise Manual dos Projetos

Antes de criar a skill, você deve entender os problemas que ela vai resolver.

**Tarefas:**

- Analisar o projeto `code-smells-project/` (Python/Flask — API de E-commerce)
- Analisar o projeto `ecommerce-api-legacy/` (Node.js/Express — LMS API com fluxo de checkout)
- Analisar o projeto `task-manager-api/` (Python/Flask — API de Task Manager)

Para cada projeto, identificar e documentar no mínimo 5 problemas, incluindo pelo menos:

- 1 de severidade CRITICAL ou HIGH
- 2 de severidade MEDIUM
- 2 de severidade LOW

Documentar os achados na seção "Análise Manual" do seu `README.md`

> **Dica:** Não precisa encontrar todos os problemas — foque nos que têm maior impacto arquitetural. Use os projetos como insumo para entender quais padrões sua skill precisa detectar.

> **Por que 3 projetos?** Dois são Python/Flask (com níveis de organização diferentes) e um é Node.js/Express. Sua skill precisa funcionar nos 3 para provar que é verdadeiramente agnóstica de tecnologia — lidando tanto com código completamente desestruturado quanto com projetos que já possuem alguma separação de camadas.

### 2. Criação da Skill

Agora que você conhece os problemas, crie uma skill que os detecte, gere um relatório de auditoria e corrija automaticamente.

**Tarefas:**

Criar a skill dentro do projeto `code-smells-project/` e implementar o SKILL.md com 3 fases sequenciais:

- **Fase 1 — Análise:** Detectar stack, mapear arquitetura atual, imprimir resumo
- **Fase 2 — Auditoria:** Cruzar código contra catálogo de anti-patterns, gerar relatório, pedir confirmação
- **Fase 3 — Refatoração:** Reestruturar para o padrão MVC, validar que funciona

Criar arquivos de referência em Markdown que forneçam à skill o conhecimento necessário para executar as 3 fases. Os arquivos devem cobrir **obrigatoriamente** as seguintes áreas de conhecimento:

| Área de conhecimento | O que deve conter |
|---|---|
| Análise de projeto | Heurísticas para detecção de linguagem, framework, banco de dados e mapeamento de arquitetura |
| Catálogo de anti-patterns | Anti-patterns com sinais de detecção e classificação de severidade |
| Template de relatório | Formato padronizado do relatório de auditoria (Fase 2) |
| Guidelines de arquitetura | Regras do padrão MVC alvo (camadas Models, Views/Routes e Controllers, responsabilidades de cada uma) |
| Playbook de refatoração | Padrões concretos de transformação para cada anti-pattern (com exemplos de código) |

> **Nota:** Você tem liberdade para organizar os arquivos de referência como preferir — pode usar os nomes e a quantidade de arquivos que fizer sentido para sua skill. O importante é que todas as 5 áreas de conhecimento estejam cobertas. O nome da skill (`refactor-arch`) e o arquivo `SKILL.md` são obrigatórios e não devem ser alterados. O path da skill segue a convenção da ferramenta escolhida (no Claude Code, por exemplo, é `.claude/skills/refactor-arch/`).

**Requisitos da skill:**

- Deve ser agnóstica de tecnologia — deve funcionar corretamente nos 3 projetos fornecidos, independente da stack ou nível de organização
- O catálogo de anti-patterns deve conter no mínimo 8 anti-patterns com severidade distribuída (CRITICAL, HIGH, MEDIUM, LOW)
- O catálogo deve incluir detecção de APIs deprecated — identificar uso de APIs obsoletas e recomendar o equivalente moderno
- O playbook deve ter no mínimo 8 padrões de transformação com exemplos de código antes/depois
- A Fase 2 deve pausar e pedir confirmação antes de modificar qualquer arquivo
- A Fase 3 deve validar o resultado (boot da aplicação + endpoints funcionando)

### 3. Execução da Skill

Execute sua skill nos 3 projetos e valide que ela funciona em todas as stacks.

#### Projeto 1 — code-smells-project (Python/Flask)

Invocar a skill no Claude Code:

```bash
claude "/refactor-arch"
```

> **Nota:** O comando acima é o exemplo com Claude Code. Se você estiver usando Gemini CLI ou Codex, utilize o comando equivalente para invocar uma skill na sua ferramenta.

- Verificar que a Fase 1 detecta corretamente a stack e imprime o resumo
- Verificar que a Fase 2 encontra no mínimo 5 dos problemas documentados na sua análise manual
- Confirmar a execução da Fase 3
- Verificar que a Fase 3:
  - Cria a estrutura de diretórios baseada em MVC
  - A aplicação inicia sem erros
  - Os endpoints originais continuam respondendo
- Salvar o relatório de auditoria (output da Fase 2) em `reports/audit-project-1.md`
- Commitar o código refatorado do projeto no repositório

#### Projeto 2 — ecommerce-api-legacy (Node.js/Express)

Prove que sua skill é reutilizável em outro projeto de backend, mas com stack diferente.

- Copiar a pasta `.claude/skills/refactor-arch/` para dentro de `ecommerce-api-legacy/`
- Invocar a skill:

```bash
cd ../ecommerce-api-legacy
claude "/refactor-arch"
```

- Verificar que as 3 fases executam corretamente neste projeto
- Salvar o relatório em `reports/audit-project-2.md`
- Commitar o código refatorado do projeto no repositório

#### Projeto 3 — task-manager-api (Python/Flask)

Agora o teste com um projeto Python/Flask que já possui alguma organização de camadas (models, routes, services, utils).

- Copiar a pasta `.claude/skills/refactor-arch/` para dentro de `task-manager-api/`
- Invocar a skill:

```bash
cd ../task-manager-api
claude "/refactor-arch"
```

- Verificar que:
  - A Fase 1 detecta corretamente Python/Flask como stack e identifica o domínio de Task Manager
  - A Fase 2 identifica problemas mesmo em um projeto parcialmente organizado
  - A Fase 3 melhora a estrutura sem quebrar a aplicação (todos os endpoints devem continuar respondendo)
- Salvar o relatório em `reports/audit-project-3.md`
- Commitar o código refatorado do projeto no repositório

> **Nota:** Este projeto já possui alguma separação de camadas, mas isso não significa que a arquitetura está adequada. A skill deve identificar tanto problemas de código (segurança, performance, qualidade) quanto oportunidades de melhoria arquitetural. Se houver mudanças estruturais necessárias, a skill deve propô-las e executá-las.

#### Validação

Para cada projeto refatorado, valide o seguinte checklist:

```markdown
## Checklist de Validação

### Fase 1 — Análise
- [ ] Linguagem detectada corretamente
- [ ] Framework detectado corretamente
- [ ] Domínio da aplicação descrito corretamente
- [ ] Número de arquivos analisados condiz com a realidade

### Fase 2 — Auditoria
- [ ] Relatório segue o template definido nos arquivos de referência
- [ ] Cada finding tem arquivo e linhas exatos
- [ ] Findings ordenados por severidade (CRITICAL → LOW)
- [ ] Mínimo de 5 findings identificados
- [ ] Detecção de APIs deprecated incluída (se aplicável)
- [ ] Skill pausa e pede confirmação antes da Fase 3

### Fase 3 — Refatoração
- [ ] Estrutura de diretórios segue padrão MVC
- [ ] Configuração extraída para módulo de config (sem hardcoded)
- [ ] Models criados para abstrair dados
- [ ] Views/Routes separadas para visualização ou roteamento
- [ ] Controllers concentram o fluxo da aplicação
- [ ] Error handling centralizado
- [ ] Entry point claro
- [ ] Aplicação inicia sem erros
- [ ] Endpoints originais respondem corretamente
```

> **Dica:** Se a skill não detectou problemas suficientes ou a refatoração falhou, ajuste os arquivos de referência e execute novamente. É normal precisar de 2-4 iterações.

## Entregável

Repositório público no GitHub (fork do repositório base) contendo:

- Skill completa em `.claude/skills/refactor-arch/` (dentro dos 3 projetos)
- Código refatorado dos 3 projetos (resultado da execução da Fase 3, commitado no repositório)
- Relatórios de auditoria em `reports/` (3 arquivos)
- `README.md` atualizado

### Estrutura do repositório

Faça um fork do repositório base contendo os três projetos com code smells.

> **Nota:** A estrutura abaixo usa Claude Code como exemplo (`.claude/skills/`). Se estiver usando outra ferramenta, adapte os caminhos conforme a convenção dela.

```
desafio-skills/
├── README.md                              # Sua documentação
│
├── code-smells-project/                   # Projeto 1 — Python/Flask (API de E-commerce)
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/             # ← SUA SKILL AQUI
│   │           ├── SKILL.md
│   │           └── (arquivos de referência)
│   ├── app.py
│   ├── controllers.py
│   ├── models.py
│   ├── database.py
│   └── requirements.txt
│
├── ecommerce-api-legacy/                  # Projeto 2 — Node.js/Express (LMS API com checkout)
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/             # ← CÓPIA DA SKILL
│   │           └── ...
│   ├── src/
│   │   ├── app.js
│   │   ├── AppManager.js
│   │   └── utils.js
│   ├── api.http
│   └── package.json
│
├── task-manager-api/                      # Projeto 3 — Python/Flask (API de Task Manager)
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/             # ← CÓPIA DA SKILL
│   │           └── ...
│   ├── app.py
│   ├── database.py
│   ├── seed.py
│   ├── requirements.txt
│   ├── models/
│   ├── routes/
│   ├── services/
│   └── utils/
│
└── reports/                               # Relatórios gerados
    ├── audit-project-1.md                 # Saída da Fase 2 no projeto 1
    ├── audit-project-2.md                 # Saída da Fase 2 no projeto 2
    └── audit-project-3.md                 # Saída da Fase 2 no projeto 3
```

**O que você vai criar:**

- `.claude/skills/refactor-arch/` — A skill completa (SKILL.md + arquivos de referência)
- Código refatorado dos 3 projetos — resultado da execução da Fase 3, commitado no repositório
- `reports/audit-project-{1,2,3}.md` — Relatório de auditoria de cada projeto
- `README.md` — Documentação do seu processo

**O que já vem pronto:**

- `code-smells-project/` — API de E-commerce Python/Flask com code smells intencionais
- `ecommerce-api-legacy/` — LMS API Node.js/Express (com fluxo de checkout) e problemas de implementação
- `task-manager-api/` — API de Task Manager Python/Flask com organização parcial e problemas de segurança/qualidade

> **Dica:** Cada projeto contém problemas intencionais de diferentes severidades (CRITICAL, HIGH, MEDIUM, LOW), incluindo falhas de segurança, violações arquiteturais e problemas de qualidade de código. Parte do desafio é identificá-los por conta própria através da análise manual do código.

### README.md deve conter

**A) Seção "Análise Manual":**

- Lista dos problemas identificados manualmente em cada projeto
- Classificação por severidade
- Justificativa de por que cada problema é relevante

**B) Seção "Construção da Skill":**

- Decisões de design: como estruturou o SKILL.md e os arquivos de referência
- Quais anti-patterns incluiu no catálogo e por quê
- Como garantiu que a skill é agnóstica de tecnologia
- Desafios encontrados e como resolveu

**C) Seção "Resultados":**

- Resumo dos relatórios de auditoria dos 3 projetos (quantos findings por severidade em cada)
- Comparação antes/depois da estrutura de cada projeto
- Checklist de validação preenchido para cada projeto
- Screenshots ou logs mostrando as aplicações rodando após refatoração
- Observações sobre como a skill se comportou em stacks diferentes

**D) Seção "Como Executar":**

- Pré-requisitos (a ferramenta escolhida — Claude Code, Gemini CLI ou Codex — instalada e configurada)
- Comandos para executar a skill em cada projeto
- Como validar que a refatoração funcionou

### Ordem de execução sugerida

**1. Analisar os projetos manualmente**

Leia o código dos três projetos e documente os problemas encontrados.

**2. Criar a skill**

Escreva o SKILL.md e os arquivos de referência.

**3. Executar nos 3 projetos**

```bash
# Projeto 1
cd code-smells-project
claude "/refactor-arch"

# Projeto 2
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3
cd ../task-manager-api
claude "/refactor-arch"
```

Salve a saída da Fase 2 de cada projeto em `reports/audit-project-{1,2,3}.md`.

**4. Iterar**

Se a skill não detectou problemas suficientes ou a refatoração falhou, ajuste os arquivos de referência e execute novamente. É normal precisar de 2-4 iterações.

## Critérios de Aceite

A skill deve atingir os seguintes mínimos em **todos os 3 projetos**:

| Critério | Requisito |
|---|---|
| Fase 1 detecta stack corretamente | OBRIGATÓRIO (3/3 projetos) |
| Fase 2 encontra >= 5 findings | OBRIGATÓRIO (3/3 projetos) |
| Fase 2 inclui pelo menos 1 CRITICAL ou HIGH | OBRIGATÓRIO (3/3 projetos) |
| Fase 3 aplicação funciona após refatoração | OBRIGATÓRIO (3/3 projetos) |

**IMPORTANTE:** Todos os critérios devem ser atingidos nos 3 projetos, não apenas em um!

> **Sobre o projeto 3 (task-manager-api):** Este projeto já possui alguma organização. "aplicação funciona" significa que a API inicia sem erros e todos os endpoints continuam respondendo corretamente.

## Referências

- [Claude Code: Skills](https://docs.anthropic.com/en/docs/claude-code/skills) — Documentação oficial sobre como criar e estruturar Skills
- [Claude Code: Overview](https://docs.anthropic.com/en/docs/claude-code/overview) — Visão geral do Claude Code e suas capacidades
- [The Complete Guide to Building Skills for Claude (PDF)](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf) — Guia completo da Anthropic sobre construção de Skills
- [Equipping Agents for the Real World with Agent Skills](https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills) — Blog oficial da Anthropic sobre Agent Skills

---

## Dicas Finais

- **Comece pela análise manual** — entender os problemas profundamente é essencial para criar uma skill que os detecte.
- **O SKILL.md é um prompt** — ele instrui o agente sobre o que fazer, enquanto os arquivos de referência fornecem o conhecimento de domínio.
- **Seja específico nos sinais de detecção** — "código ruim" não ajuda; "query SQL dentro de loop for" é acionável.
- **Teste incrementalmente** — não tente criar a skill perfeita de primeira.
- **A skill deve ser copiável** — se ela só funciona em um projeto específico, está acoplada demais. Teste nos 3 projetos para validar.
- **Projetos diferentes exigem adaptação** — a Fase 3 de um projeto já parcialmente organizado não vai ter as mesmas transformações de um monolito. Sua skill deve se adaptar ao contexto.
- **Pedir confirmação na Fase 2 é obrigatório** — o humano deve revisar o relatório antes de qualquer modificação.
- **Consulte as referências do curso** — revise a documentação oficial da ferramenta escolhida e os materiais das aulas para relembrar a estrutura e anatomia de uma skill.