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
