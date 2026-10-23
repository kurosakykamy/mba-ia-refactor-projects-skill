================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0 / Flask-SQLAlchemy 3.1.1
Files:   16 analyzed | ~1177 lines of code

## Summary
CRITICAL: 4 | HIGH: 4 | MEDIUM: 6 | LOW: 4

## Findings

### [CRITICAL] Nenhuma Rota Valida Autenticação/Autorização
File: routes/user_routes.py:185-211 (emissão do token), todas as rotas em routes/task_routes.py, routes/user_routes.py, routes/report_routes.py (ausência de verificação)
Description: `login` emite `'fake-jwt-token-' + str(user.id)` (linha 210), mas nenhuma rota do projeto verifica esse token (confirmado por busca textual — zero checagens de `Authorization`/`token` fora do próprio login). Toda rota de CRUD está, na prática, totalmente aberta.
Impact: Qualquer chamador anônimo pode listar/criar/editar/apagar usuários e tarefas de qualquer pessoa, inclusive promover papéis (`role`) e ver o hash de senha de qualquer usuário.
Recommendation: Implementar um middleware real de autenticação (JWT assinado de verdade) e aplicá-lo como decorator obrigatório nas rotas sensíveis (playbook #3).

### [CRITICAL] Hash de Senha com MD5 Sem Salt
File: models/user.py:29, 31-32
Description: `set_password`/`check_password` usam `hashlib.md5(pwd.encode()).hexdigest()` — MD5 é criptograficamente quebrado para senhas (rápido de forçar por força bruta, vulnerável a rainbow tables), e não há salt.
Impact: Vazamento do banco expõe virtualmente todas as senhas em minutos/segundos de cracking.
Recommendation: Migrar para `werkzeug.security.generate_password_hash`/`check_password_hash` (playbook #6).

### [CRITICAL] Segredos Hardcoded no Código-Fonte
File: app.py:13, services/notification_service.py:9-10
Description: `SECRET_KEY = 'super-secret-key-123'` e credenciais SMTP (`email_user`, `email_password = 'senha123'`) estão fixos no código, apesar de `python-dotenv` já constar no `requirements.txt` (não utilizado).
Impact: Qualquer pessoa com acesso ao repositório tem a chave de sessão Flask e a senha de uma conta de e-mail real.
Recommendation: Carregar via variável de ambiente em um módulo de config, efetivamente usando o `python-dotenv` já declarado (playbook #1).

### [CRITICAL] Debug Mode Habilitado em Servidor Vinculado a Todas as Interfaces
File: app.py:34
Description: `app.run(debug=True, host='0.0.0.0', port=5000)` expõe o debugger interativo do Werkzeug a qualquer rede acessível.
Impact: Se exposto além de localhost, permite execução arbitrária de código Python via o debugger interativo acionado por qualquer erro 500.
Recommendation: `debug=False` fora de ambiente local; usar servidor WSGI de produção.

### [HIGH] Hash de Senha Vazado nas Respostas da API
File: models/user.py:16-25 (`to_dict` inclui `password`), exposto em routes/user_routes.py:33, 85-86, 129, 209
Description: `to_dict()` do model `User` inclui o campo `password` (linha 21), e é usado diretamente nas respostas de `get_user`, `create_user`, `update_user` e `login`. Curiosamente `get_users` (lista, `user_routes.py:15-24`) monta o dict manualmente sem o campo — uma inconsistência que mostra que o vazamento não é intencional.
Impact: Qualquer chamada a essas 4 rotas devolve o hash MD5 da senha do usuário no corpo da resposta JSON.
Recommendation: Remover `password` de `to_dict()` (ou criar um `to_public_dict()` separado) e usar esse método em todas as rotas, inclusive `get_users`.

### [HIGH] Queries N+1
File: routes/task_routes.py:41-46, 50-56; routes/report_routes.py:56, 163
Description: `get_tasks` busca `User`/`Category` individualmente dentro do loop por tarefa (uma query por relação por tarefa); `summary_report` busca tarefas de cada usuário dentro de um loop (`report_routes.py:56`); `get_categories` conta tarefas por categoria dentro do loop (`report_routes.py:163`).
Impact: Número de queries cresce linearmente com o volume de dados em vez de usar `join`/`joinedload` ou uma única query agregada.
Recommendation: Usar `db.session.query(...).join(...)` ou `selectinload`/`joinedload` do SQLAlchemy para eliminar os loops (playbook #7).

### [HIGH] Duplicação Massiva de Lógica — Métodos Corretos Existem mas Nunca São Chamados
File: models/task.py:38-60 (`validate_status`, `validate_priority`, `is_overdue` nunca chamados); utils/helpers.py (praticamente todo o arquivo, exceto `format_date`/`calculate_percentage`, nunca importado pelas rotas)
Description: A lógica de "overdue" é copiada manualmente, com o mesmo aninhamento de `if`, em pelo menos 5 lugares: `routes/task_routes.py:30-39`, `routes/task_routes.py:71-80`, `routes/task_routes.py:283-287`, `routes/user_routes.py:171-180`, `routes/report_routes.py:34-37` e `routes/report_routes.py:132-135` — em vez de chamar `Task.is_overdue()`, que já existe e faz exatamente isso. O mesmo vale para validação de status/prioridade (`task_routes.py:96-100,110,113,167-170,177,182-183`) que duplica `process_task_data()` de `utils/helpers.py:57-108`, nunca importado em `task_routes.py`.
Impact: Qualquer correção na regra de "atrasado" ou de validação precisa ser replicada manualmente em 5-6 lugares, com alto risco de divergência silenciosa — e o próprio código já "correto" (`is_overdue`, `process_task_data`) vira código morto.
Recommendation: Chamar `task.is_overdue()` e `process_task_data()`/helpers existentes em vez de reimplementar (playbook #8).

### [HIGH] Serviço de Notificação Morto, Nunca Conectado ao Fluxo
File: services/notification_service.py:1-48 (classe inteira), não referenciada em routes/task_routes.py:85-154 (`create_task`, onde uma notificação de "task atribuída" faria sentido)
Description: `NotificationService` e seu método `notify_task_assigned` existem e estão implementados, mas `NotificationService` nunca é instanciado em lugar nenhum do projeto (confirmado por busca textual).
Impact: Funcionalidade aparentemente pronta (notificar usuário ao receber uma tarefa) nunca executa de fato — expectativa de comportamento que o código não cumpre.
Recommendation: Instanciar o serviço no controller/service de criação de tarefa e chamá-lo quando `user_id` for definido (playbook #5), ou remover o código morto se a funcionalidade não for mais necessária (playbook #13).

### [MEDIUM] `except:` Genérico Silenciando Erros
File: routes/task_routes.py:62, 236; routes/user_routes.py:130, 149; routes/report_routes.py:186, 207, 221
Description: Vários handlers usam `except:` sem especificar o tipo de exceção e sem logar o erro real, apenas devolvendo uma mensagem genérica.
Impact: Bugs de programação (não apenas falhas de banco) são mascarados como "erro ao processar", dificultando o diagnóstico em produção.
Recommendation: Capturar exceções específicas e logar com `logging.exception` antes de responder (playbook #9).

### [MEDIUM] Validação Ausente/Erros Não Tratados em Rotas Numéricas
File: routes/task_routes.py:113, 182 (fora do bloco try, `TypeError` não tratado se `priority` vier como string); routes/task_routes.py:240-271 (`search_tasks`, sem try/except algum; `int(priority)` linha 261 e `int(user_id)` linha 264 levantam `ValueError` não tratado); routes/report_routes.py:196-197 (`update_category` sem guarda `if not data`, diferente de todo o resto do arquivo)
Description: Entradas malformadas (prioridade como string, `search` com `priority`/`user_id` não numéricos, corpo vazio em `update_category`) derrubam a rota com erro não tratado (500 HTML do Flask) em vez do contrato JSON do resto da API.
Impact: Comportamento inconsistente da API sob entrada inválida — alguns endpoints retornam JSON `400` limpo, outros quebram.
Recommendation: Validar tipo antes de comparar/castear, e padronizar o guard `if not data` em todas as rotas de escrita.

### [MEDIUM] Ausência de Paginação
File: routes/task_routes.py:14 (`Task.query.all()`)
Description: O endpoint principal de listagem de tarefas devolve a tabela inteira sem paginação — o próprio dado de seed já documenta essa lacuna (`seed.py:70`: "Adicionar paginação na API... Endpoints retornam todos os registros").
Impact: Resposta cresce sem limite conforme o volume de tarefas aumenta, degradando performance e uso de memória.
Recommendation: Adicionar parâmetros `page`/`per_page` com `Task.query.paginate(...)`.

### [MEDIUM] `db.create_all()` Executado como Efeito Colateral de Import
File: app.py:30-31
Description: `with app.app_context(): db.create_all()` roda no nível de módulo (fora de `if __name__ == '__main__':`), portanto é disparado novamente sempre que outro script importa `app` (como `seed.py:2` faz).
Impact: Acoplamento indesejado — importar o módulo `app` para reaproveitar `app`/`db` sempre recria tabelas como efeito colateral, dificultando testes e scripts auxiliares.
Recommendation: Mover `db.create_all()` para dentro de uma função `create_app()`/bloco `if __name__ == '__main__':`, chamada explicitamente.

### [MEDIUM] Uso de API Deprecated — `datetime.utcnow()`
File: models/task.py:15, 16, 52; models/user.py:14; routes/task_routes.py:31, 72, 215; routes/report_routes.py:35, 45, 71, 133; services/notification_service.py:35
Description: `datetime.utcnow()` está depreciado desde Python 3.12 (gera `DeprecationWarning`, será removido em versão futura) em favor de `datetime.now(timezone.utc)`; o projeto usa o padrão antigo de forma pervasiva.
Impact: Warnings em execução em runtimes mais novos hoje; quebra garantida quando o método for removido.
Recommendation: Substituir por `datetime.now(timezone.utc)` em todos os usos (ver tabela de APIs deprecated no catálogo).

### [LOW] Imports Não Utilizados
File: app.py:7 (`os, sys, json`); routes/task_routes.py:7 (`json, os, sys, time`); routes/user_routes.py:6 (`hashlib, json`); utils/helpers.py:3-7 (`os, sys, json, math, hashlib`)
Description: Vários módulos são importados e nunca referenciados no arquivo correspondente.
Impact: Ruído de manutenção, engana o leitor sobre dependências reais do módulo.
Recommendation: Remover os imports não utilizados (playbook #13).

### [LOW] Dependências Declaradas e Nunca Usadas
File: requirements.txt:4-6 (`marshmallow`, `requests`, `python-dotenv`)
Description: Nenhuma delas é importada em lugar nenhum do código — confirmado por busca textual — apesar de `python-dotenv` ser exatamente a ferramenta que resolveria o finding de segredo hardcoded acima.
Impact: Dependências fantasmas aumentam a superfície de instalação/auditoria de segurança sem benefício real.
Recommendation: Remover as não utilizadas, ou efetivamente adotar `python-dotenv` para configuração (playbook #1) e `marshmallow` para validação de schema.

### [LOW] `print()` ao Invés de Logging Estruturado
File: routes/task_routes.py:149, 153, 219, 234; routes/user_routes.py:83, 89, 147
Description: Eventos de criação/atualização/erro são registrados via `print()` em vez do módulo `logging`.
Impact: Sem nível de log, sem destino configurável; inútil para observabilidade em produção.
Recommendation: Substituir por `logging` (playbook #12).

### [LOW] Padrão Verboso de Retorno Booleano
File: models/task.py:38-60 (`validate_status`, `validate_priority`, `is_overdue`); models/user.py:34-38 (`is_admin`)
Description: Métodos escrevem `if condição: return True else: return False` em vez de `return condição`.
Impact: Apenas legibilidade/estilo — sem efeito funcional, mas aumenta ruído de leitura.
Recommendation: Simplificar para `return condição` diretamente.

================================
Total: 18 findings
================================

================================
NOTA DE CORREÇÃO
================================
Origem: reauditoria sistemática disparada pela segunda revisão do professor. Depois de
corrigir o caso que ele apontou no projeto 2 (cache sem limite), reauditei **todos** os
findings dos 3 projetos com um critério único: *o `Impact` descrito no relatório deixou de
ser reproduzível no código, ou só a estrutura mudou?* Este projeto era o que tinha mais
resíduos.

### Findings que estavam FORM-ONLY (Impact intacto)

**[MEDIUM] Ausência de Paginação** — `controllers/task_controller.py` ainda terminava em
`.all()`; busca textual por `paginate` no projeto retornava **0 ocorrências**. O endpoint
continuava carregando a tabela inteira.
*Correção:* `list_tasks(page, per_page)` usa `paginate()` real com `DEFAULT_PAGE_SIZE=20` e
teto `MAX_PAGE_SIZE=100`; a rota aceita `?page=&per_page=` e valida tipo.
*Evidência:* `?page=1&per_page=3` → 3 itens, `total:10`, `pages:4`; `?page=2&per_page=3` →
ids `[4,5,6]` (página diferente de fato); `?per_page=9999` → `per_page` efetivo `100`;
`?page=abc` → 400.

**[MEDIUM] `db.create_all()` como efeito colateral de import** — a chamada tinha sido movida
para dentro de `create_app()`, mas `app.py` executava `app = create_app()` no escopo de
módulo, fora do `if __name__`. Importar `app` (como `seed.py` faz) continuava criando as
tabelas — o Impact era byte-a-byte o mesmo, só uma função mais fundo.
*Correção:* `create_all()` extraído para `init_db(app)`, chamado explicitamente pelo
`__main__` e pelo `seed.py`.
*Evidência:* com o banco apagado, `python -c "import app"` **não** cria o arquivo; só
`python seed.py` / `python app.py` criam.

### Findings PARCIAIS (Impact reduzido, resíduo vivo)

**[CRITICAL] Autenticação/Autorização** — o relatório declara no Impact "promover papéis" e
"alterar estado de outro usuário". A autenticação real foi implementada, mas duas brechas
dentro desse mesmo Impact sobreviveram:
- `POST /users` não tinha decorator e aceitava `role` do corpo validado contra `VALID_ROLES`
  (que inclui `admin`) → **qualquer anônimo se auto-promovia a admin**.
- `update_user` era só `@login_required`, sem checagem de dono → **qualquer usuário logado
  trocava a senha de qualquer outro**.
*Correção:* cadastro público ignora `role` (sempre `'user'`); definir papel exige token de
admin; `update_user`/`delete_user` passam por `_can_act_on()` (só a si mesmo, ou admin).
*Evidência:* `POST /users {"role":"admin"}` anônimo → **403**; cadastro normal anônimo → 201
com `role: "user"`; Maria (user) tentando `PUT /users/1 {"password":...}` → **403**; Maria
alterando o próprio nome → 200; admin criando usuário com `role=admin` → 201.

**[MEDIUM] N+1** — 3 dos 4 locais foram corrigidos, mas `controllers/user_controller.py`
mantinha `len(user.tasks)` dentro do loop (backref lazy = 1 query por usuário) — o corpo
original de `get_users` copiado sem alteração para o controller.
*Correção:* uma query agregada `group_by` (mesmo padrão já usado em `category_controller`).

**[MEDIUM] `datetime.utcnow()` deprecated** — `models/category.py:11` ficou de fora da
substituição.
*Correção:* passou a usar `utcnow_naive()`. *Evidência:* `grep -rn "datetime.utcnow"` → **0**.

**[MEDIUM] `except:` genérico** — os bare excepts foram removidos, mas o handler central de
`ValueError` devolvia 400 **sem logar**. Como `ValueError` costuma ser bug de programação,
isso reintroduzia "bugs mascarados sem rastro" de forma centralizada.
*Correção:* `logger.exception(...)` antes de responder 400.

### Validação final
Aplicação sobe sem erros; `/tasks` (paginado), `/tasks/stats`, `/tasks/search`, `/users`,
`/reports/summary`, `/categories`, `/health` e `/login` todos respondendo; autorização por
papel e por propriedade testada com tokens reais de admin e de usuário comum.
================================

================================
NOTA DE CORREÇÃO (ITERAÇÃO 4)
================================
Origem: terceira revisão do professor.

Problema reportado: o finding "[CRITICAL] Segredos Hardcoded no Código-Fonte" (acima) foi dado
como corrigido, mas `config/settings.py:9` ainda usava
`os.environ.get("SECRET_KEY", "dev-only-insecure-key-change-me")` — **sem bloquear o boot**.
Como a iteração 3 passou a usar essa mesma chave para assinar os tokens de autenticação
(`middlewares/auth.py:12,21`, `URLSafeTimedSerializer`), qualquer pessoa que lesse o
repositório podia gerar offline `serializer.dumps({'user_id': 1})` e autenticar como o admin
João — sem login, sem rede, sem rate limit.

Causa raiz: **não foi lacuna da skill.** O padrão #1 do playbook já estava correto desde a
iteração 3, com bloco "Nunca faça isto" descrevendo exatamente este caso e checklist exigindo
"nenhum literal de segredo... nem como default usado fora de desenvolvimento". O padrão foi
aplicado no `code-smells-project` e **não** nos outros dois projetos. Falha de execução:
corrigiu-se a instância que o finding nomeava, não a classe inteira — mesmo com a auditoria da
iteração 3 tendo marcado este item como "PARTIAL (fail-open fallback)".

Agravante documentado: a iteração 3 **aumentou** a severidade deste fallback sem reavaliá-lo.
Antes de existir autenticação, a chave com default público era quase inócua; ao introduzir
assinatura de token, o mesmo default virou "qualquer leitor do repo é admin".

### Inventário completo de segredos deste projeto (varredura exaustiva)

| Valor | Arquivo:linha | Antes | Consumido em | Ação |
|---|---|---|---|---|
| `SECRET_KEY` | `config/settings.py` | FAIL-OPEN | `middlewares/auth.py:12,21` (assina/valida token) | **FAIL-CLOSED** via `_required_secret()` |
| `SMTP_PASSWORD` | `config/settings.py` | FAIL-OPEN | `services/notification_service.py:18` | **FAIL-CLOSED** via `_required_secret()` |
| `SMTP_USER` | `config/settings.py` | — | `notification_service.py:18` | NÃO-É-SEGREDO (e-mail/usuário) |
| `SMTP_HOST`, `SMTP_PORT` | `config/settings.py` | — | idem | NÃO-É-SEGREDO |
| `DATABASE_URL` | `config/settings.py` | — | SQLAlchemy | NÃO-É-SEGREDO neste projeto (sqlite local, sem credencial embutida) |
| `FLASK_DEBUG`, `HOST`, `PORT`, `CORS_ORIGINS` | `config/settings.py` | — | `app.py` | NÃO-É-SEGREDO |
| Senhas de seed | `seed.py:21,28,35` | literais | dados de demonstração | Mantidas — hasheadas via `werkzeug.security`, esperadas num projeto didático; registradas aqui para constar que foram avaliadas |

Correção aplicada: introduzido `APP_ENV` e o helper `_required_secret(name, dev_default)`
**idêntico ao do `code-smells-project/config/settings.py`** (mesma assinatura, mesmo
`RuntimeError`, mesmo gate `APP_ENV != "development"`), aplicado a `SECRET_KEY` e
`SMTP_PASSWORD`.

### Evidência executada

| Verificação | Resultado |
|---|---|
| `APP_ENV=production python -c "from config.settings import Settings"` | `RuntimeError: SECRET_KEY é obrigatório quando APP_ENV=production` |
| idem, com `SECRET_KEY` definida | `RuntimeError: SMTP_PASSWORD é obrigatório...` (o segundo segredo também é guardado) |
| idem, com ambos definidos | carrega normalmente |
| Fluxo dev documentado (`python seed.py` + `python app.py`) | intacto — seed popula, app sobe |
| `/tasks` sem token / com token | 401 / 200 |
| `/users` (admin), `/reports/summary`, `/health` | 200 |
| `grep os.environ.get` com palavras de segredo | 0 ocorrências com default |

Status: **finding fechado** — nenhum segredo deste projeto sobe com valor visível no
repositório fora de desenvolvimento.
================================
