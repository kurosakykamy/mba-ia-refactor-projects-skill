================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~783 lines of code

## Summary
CRITICAL: 7 | HIGH: 4 | MEDIUM: 4 | LOW: 3

## Findings

### [CRITICAL] Hardcoded Credentials & Secret Leaked via Public Endpoint
File: app.py:7-8, controllers.py:286-289
Description: `SECRET_KEY` é um literal fixo (`"minha-chave-super-secreta-123"`) no código-fonte, e o mesmo valor, junto com `debug=True` e o path do banco, é devolvido no corpo JSON do endpoint público `GET /health`.
Impact: Qualquer pessoa com acesso ao repositório (ou ao endpoint `/health`) obtém a chave usada para assinar sessões/tokens Flask, permitindo forjar cookies de sessão.
Recommendation: Mover para variável de ambiente via módulo de config (playbook #1) e remover `secret_key`/`debug` do payload de `/health`.

### [CRITICAL] Missing Authorization — Destructive Admin Endpoint
File: app.py:47-57
Description: `POST /admin/reset-db` apaga todas as linhas de `itens_pedido`, `pedidos`, `produtos` e `usuarios` sem nenhuma checagem de autenticação/autorização.
Impact: Qualquer chamador anônimo pode apagar o banco de dados inteiro em produção.
Recommendation: Proteger com middleware/decorator de autenticação de admin (playbook #3) antes de qualquer operação destrutiva.

### [CRITICAL] SQL Injection — Arbitrary SQL Execution Endpoint
File: app.py:59-78
Description: `POST /admin/query` recebe uma string SQL arbitrária do corpo da requisição (`dados.get("sql", "")`, linha 62) e a executa diretamente via `cursor.execute(query)` (linha 69), sem validação, allowlist ou autenticação.
Impact: Execução arbitrária de SQL por qualquer cliente — leitura, alteração ou destruição completa dos dados, incluindo bypass de qualquer outra regra de negócio.
Recommendation: Remover este endpoint do código de produção; se uma ferramenta de query administrativa for necessária, restringi-la a um shell interno autenticado, nunca a uma rota HTTP pública.

### [CRITICAL] SQL Injection — Authentication Bypass in Login
File: models.py:105-120 (concatenação nas linhas 109-111)
Description: `login_usuario` monta a query com `"... WHERE email = '" + email + "' AND senha = '" + senha + "'"`, permitindo que um valor como `' OR '1'='1' --` autentique sem credenciais válidas.
Impact: Bypass completo de autenticação; qualquer atacante pode logar como qualquer usuário, incluindo o admin.
Recommendation: Usar query parametrizada (`?`) e comparar hash de senha, não o valor em texto puro (playbook #2 e #6).

### [CRITICAL] SQL Injection — String Concatenation Across Data Layer
File: models.py:28, 48-50, 57-61, 68, 92, 127-129, 140, 148-151, 155, 158-161, 164-166, 174, 188, 192, 206, 220, 224, 280, 291-297
Description: Praticamente toda função de acesso a dados em `models.py` monta SQL por concatenação de strings com valores vindos diretamente de parâmetros de função (que por sua vez vêm do request), em vez de usar placeholders parametrizados.
Impact: Qualquer campo de texto aceito pela API (nome de produto, categoria, termo de busca, status de pedido etc.) é um vetor de injeção SQL — leitura/alteração/exclusão de dados fora do escopo pretendido.
Recommendation: Substituir toda concatenação por queries parametrizadas com `?` (playbook #2); o próprio `database.py:70-73,80-83` já demonstra o padrão correto com `executemany`.

### [CRITICAL] Broken Password Storage (Plaintext)
File: models.py:122-131, database.py:75-79
Description: `criar_usuario` grava `senha` sem qualquer hashing; os dados de seed (`database.py:75-79`) incluem um usuário admin com senha fraca e em texto puro (`"admin123"`).
Impact: Vazamento do banco expõe todas as senhas diretamente, incluindo a de uma conta admin.
Recommendation: Hash com `werkzeug.security.generate_password_hash` na criação e `check_password_hash` no login (playbook #6).

### [CRITICAL] Debug Mode Enabled on Publicly-Bound Server
File: app.py:8, 88
Description: `app.config["DEBUG"] = True` e `app.run(host="0.0.0.0", port=5000, debug=True)` — o servidor de desenvolvimento Flask roda com o debugger interativo do Werkzeug habilitado e vinculado a todas as interfaces de rede.
Impact: Se exposto além de localhost, o debugger interativo permite execução arbitrária de código Python por qualquer visitante que acione um erro 500.
Recommendation: `debug=False` fora de ambiente local, e uso de um servidor WSGI de produção (gunicorn/waitress) atrás de proxy (ver tabela de padrões deprecated/inseguros).

### [HIGH] God Module — Acesso a Dados + Regra de Negócio + Relatório para 3 Domínios
File: models.py:1-315
Description: Um único módulo concentra toda a lógica de dados, validação de estoque/total (`criar_pedido`, linhas 133-169) e geração de relatório (`relatorio_vendas`, linhas 235-273) para produtos, usuários e pedidos — três domínios sem relação direta de dados entre si.
Impact: Impossível testar cada domínio isoladamente; qualquer alteração em um domínio arrisca efeitos colaterais nos outros dois.
Recommendation: Separar em `models/produto_model.py`, `models/usuario_model.py`, `models/pedido_model.py` (playbook #4); mover `criar_pedido`/`relatorio_vendas` para uma camada de `services/`.

### [HIGH] Business Logic & Side-Effects Leaking into Controllers
File: controllers.py:188-220, 237-255
Description: `criar_pedido` e `atualizar_status_pedido` (controllers) imprimem simulações de envio de email/SMS/push e notificações de negócio diretamente no handler HTTP, misturando orquestração de request com regra de domínio.
Impact: A mesma regra de notificação não pode ser reutilizada fora do contexto HTTP (ex.: processamento em lote) e cresce sem limite dentro do controller a cada nova regra.
Recommendation: Extrair para `services/notification_service.py`, chamado pelo controller após o resultado do model (playbook #5).

### [HIGH] Manual Global Mutable Singleton Connection
File: database.py:4, 7-10
Description: `db_connection` é uma variável de módulo mutada via `global`, com `check_same_thread=False` para permitir uso fora da thread que a criou — mascarando a falta de um pool/gestão de conexão adequada sob o servidor multi-thread do Flask dev.
Impact: Corrida de condição entre requisições concorrentes compartilhando a mesma conexão SQLite.
Recommendation: Usar uma conexão por requisição (ou um pool real) em vez de um singleton manual global.

### [HIGH] N+1 (N×M+1) Nested Queries
File: models.py:187-199, 219-231
Description: Para cada pedido, uma query busca os itens; para cada item, outra query busca o nome do produto (`cursor2`/`cursor3` aninhados) — 2 níveis de aninhamento, não apenas 1.
Impact: Para N pedidos com M itens cada, o endpoint executa `1 + N + N×M` queries em vez de uma única consulta com JOIN — degradação severa de performance à medida que o volume cresce.
Recommendation: Substituir por uma única query com JOIN entre `pedidos`, `itens_pedido` e `produtos`, agrupando em memória por `pedido.id` (playbook #7).

### [MEDIUM] Duplicated Logic — `get_todos_pedidos` quase idêntico a `get_pedidos_usuario`
File: models.py:171-201 vs. models.py:203-233
Description: As duas funções repetem ~25 linhas de montagem de resultado e o mesmo padrão de N+1 aninhado, diferindo apenas no filtro inicial da query.
Impact: Qualquer correção (ex.: resolver o N+1 acima) precisa ser replicada manualmente nos dois lugares, com risco de divergência.
Recommendation: Extrair a montagem comum para uma função privada reutilizada pelas duas (playbook #8).

### [MEDIUM] Generic/Swallowed Error Handling Leaking Exception Details
File: controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292
Description: Praticamente toda rota usa `except Exception as e: return jsonify({"erro": str(e)}), 500`, devolvendo a mensagem crua da exceção (podendo incluir erro de SQL/estrutura de tabela) e tratando todo tipo de erro como 500 genérico.
Impact: Vazamento de detalhes internos ao cliente; impossível distinguir erro de validação (4xx) de falha real do servidor (5xx) nos logs.
Recommendation: Centralizar tratamento de erro com `@app.errorhandler` e exceções de domínio específicas (playbook #9).

### [MEDIUM] CORS Totalmente Aberto
File: app.py:9
Description: `CORS(app)` é chamado sem restrição de origem, liberando qualquer domínio a fazer requisições cross-origin à API.
Impact: Facilita ataques de CSRF/exfiltração a partir de sites maliciosos que façam chamadas no navegador de um usuário autenticado.
Recommendation: Restringir `CORS(app, origins=[...])` às origens realmente confiáveis.

### [MEDIUM] Missing Validation — Status Update Sem Checagem de Existência / Coerção Numérica
File: controllers.py:237-255, controllers.py:39-40
Description: `atualizar_status_pedido` nunca confirma que o pedido existe antes de atualizar (sucesso "silencioso" em pedido inexistente); `criar_produto` não valida que `preco`/`estoque` são de fato numéricos antes de repassar ao model.
Impact: Respostas de sucesso enganosas para operações que não fizeram nada, e erros de tipo não tratados que viram 500 genérico em vez de 400 claro.
Recommendation: Checar existência antes de atualizar e validar tipo explicitamente nas rotas antes de chamar o model.

### [LOW] Magic Numbers — Faixas de Desconto
File: models.py:256-262
Description: Limiares de faturamento (`10000`, `5000`, `1000`) e taxas de desconto (`0.1`, `0.05`, `0.02`) estão embutidos inline na função `relatorio_vendas`, sem constante nomeada.
Impact: Regra de negócio importante fica escondida em um `if/elif`, difícil de localizar e ajustar com segurança.
Recommendation: Extrair para constantes nomeadas em um módulo de regras de negócio (playbook #11).

### [LOW] Print-based Logging (incluindo dado sensível)
File: controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250; app.py:56, 83-86
Description: `print(...)` é usado como mecanismo de log em toda a aplicação, incluindo impressão do email do usuário em tentativas de login (`controllers.py:179, 182`).
Impact: Sem nível de log, sem destino configurável; dado potencialmente sensível (email) fica exposto em stdout sem controle.
Recommendation: Substituir por `logging` padrão, evitando logar dado sensível em texto puro (playbook #12).

### [LOW] Dead/Unused Imports
File: models.py:2, database.py:2
Description: `import sqlite3` em `models.py` e `import os` em `database.py` nunca são usados nesses arquivos.
Impact: Ruído de manutenção, confunde o leitor sobre dependências reais do módulo.
Recommendation: Remover os imports não utilizados (playbook #13).

================================
Total: 18 findings
================================
