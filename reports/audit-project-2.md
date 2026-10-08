================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   Node.js + Express 4.18.2
Files:   3 analyzed | ~180 lines of code

## Summary
CRITICAL: 5 | HIGH: 4 | MEDIUM: 4 | LOW: 3

## Findings

### [CRITICAL] Hardcoded Credentials & Secrets
File: src/utils.js:2-6
Description: `dbUser`, `dbPass` ("senha_super_secreta_prod_123"), `paymentGatewayKey` ("pk_live_1234567890abcdef") e `smtpUser` estão todos embutidos como literais no código-fonte, versionados no repositório.
Impact: Qualquer pessoa com acesso ao código tem a chave de gateway de pagamento e a senha de banco de "produção" — sem rotação possível sem novo deploy.
Recommendation: Mover para variáveis de ambiente via módulo de config (playbook #1).

### [CRITICAL] Missing Authentication/Authorization em 3 Rotas
File: src/AppManager.js:28, 80, 131
Description: `POST /api/checkout` (cria usuário e processa pagamento), `GET /api/admin/financial-report` (relatório financeiro completo) e `DELETE /api/users/:id` (deleta qualquer usuário) não possuem nenhuma checagem de identidade/permissão.
Impact: Qualquer chamador anônimo pode criar contas, ver receita e dados de todos os alunos, e apagar qualquer usuário do sistema.
Recommendation: Adicionar middleware de autenticação exigido nas rotas sensíveis, com checagem de papel (admin) no relatório financeiro (playbook #3).

### [CRITICAL] Vazamento de Dado Sensível via Log (Cartão de Crédito + Chave de Pagamento)
File: src/AppManager.js:45
Description: `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)` imprime o número completo do cartão informado pelo cliente e a chave secreta do gateway de pagamento em todo checkout.
Impact: Dado de cartão (PAN) e segredo de gateway ficam expostos em texto puro em qualquer destino de log (console, arquivo, agregador), uma violação direta de PCI-DSS.
Recommendation: Nunca logar PAN completo (mascarar) nem segredos; usar logging estruturado sem dado sensível (playbook #12).

### [CRITICAL] Criptografia Falsa para Senha
File: src/utils.js:17-23, usada em src/AppManager.js:68
Description: `badCrypto` não é um hash — repete `Buffer.from(pwd).toString('base64')` 10.000 vezes (cada iteração produz o mesmo resultado, laço sem efeito) e trunca para 10 caracteres; base64 é trivialmente reversível e sem salt.
Impact: Senhas de usuários criados via checkout podem ser recuperadas instantaneamente a partir do "hash" armazenado.
Recommendation: Substituir por `bcrypt.hash`/`bcrypt.compare` (playbook #6).

### [CRITICAL] Lógica de Pagamento Falsa / Bypass Trivial
File: src/AppManager.js:46
Description: `let status = cc.startsWith("4") ? "PAID" : "DENIED";` — qualquer número de cartão que apenas comece com "4" é aprovado, sem validação de Luhn, expiração, CVV ou chamada real a um gateway.
Impact: Qualquer pessoa "aprova" o próprio pagamento enviando um número de cartão fictício começando com 4; typicamente seria um vetor de fraude em produção.
Recommendation: Integrar com um gateway de pagamento real (ou mock explícito de teste isolado do fluxo de produção).

### [HIGH] God Class — Schema, Rotas, Regra de Negócio e Validação no Mesmo Arquivo
File: src/AppManager.js:1-141
Description: Uma única classe concentra criação de schema (`initDb`, linhas 10-23), as 3 rotas da API (`setupRoutes`, linhas 25-138), toda a regra de negócio de checkout, validação de entrada e formatação de resposta.
Impact: Impossível testar qualquer parte isoladamente; qualquer mudança de rota arrisca quebrar lógica de outro domínio no mesmo arquivo.
Recommendation: Separar em `models/` (acesso a dados), `controllers/` (orquestração) e `views/routes` (mapeamento HTTP) por domínio (playbook #4).

### [HIGH] Callback Hell Sem Transação — Risco de Dado Inconsistente
File: src/AppManager.js:37-77
Description: Até 5 níveis de callbacks aninhados (`db.get`/`db.run`) para: buscar curso → buscar usuário → opcionalmente criar usuário → criar matrícula → criar pagamento → registrar auditoria — sem transação alguma; se o insert de pagamento (linha 54) falhar após a matrícula (linha 50) já ter sido criada, não há rollback.
Impact: Matrícula "pendurada" sem pagamento correspondente, inconsistência de dados silenciosa.
Recommendation: Envolver os inserts relacionados numa transação explícita (`BEGIN`/`COMMIT`/`ROLLBACK`) ou usar `async/await` com uma única unidade de trabalho (playbook #7/#9).

### [HIGH] Ausência de Integridade Referencial / Unicidade
File: src/AppManager.js:12-16
Description: Nenhuma tabela declara `FOREIGN KEY`, e `users.email` não tem `UNIQUE`, apesar de ser usado como chave de busca (linha 40) antes de um insert condicional (linha 69) — race condition de e-mail duplicado sob concorrência.
Impact: Dados órfãos possíveis em qualquer tabela filha; e-mails duplicados sob carga concorrente.
Recommendation: Declarar `FOREIGN KEY` nas tabelas filhas e `UNIQUE` em `users.email`.

### [HIGH] Estado Global Mutável
File: src/utils.js:9-10
Description: `globalCache` (objeto de módulo, nunca limpo, crescendo a cada checkout via `logAndCache`) e `totalRevenue` (declarado e exportado, mas nunca atualizado em lugar nenhum — estado morto e enganoso).
Impact: `globalCache` é um vazamento de memória não limitado; `totalRevenue` sugere uma funcionalidade que não existe de fato.
Recommendation: Remover `totalRevenue` morto; substituir `globalCache` por um cache com TTL/tamanho máximo encapsulado em uma classe (playbook #10).

### [MEDIUM] N+1 (N×M+1) Nested Queries no Relatório Financeiro
File: src/AppManager.js:83-126
Description: 1 query para cursos, depois 1 query de matrículas por curso (linha 92), depois 2 queries (usuário + pagamento) por matrícula (linhas 104, 106) — para C cursos e E matrículas/curso isso é `1 + C + 2·C·E` round-trips.
Impact: Degradação severa de performance conforme a base de alunos/matrículas cresce.
Recommendation: Substituir por uma única query com JOIN entre `courses`, `enrollments`, `users` e `payments` (playbook #7).

### [MEDIUM] Contagem Manual de Concorrência Mascarando Erros
File: src/AppManager.js:86, 93, 97-98, 117-121
Description: Em vez de `Promise.all`, o código decrementa contadores (`coursesPending`, `enrPending`) manualmente para saber quando todas as queries assíncronas terminaram; os `err` de `db.get` nas linhas 104 e 106 são capturados mas nunca checados, falhas silenciosamente viram `'Unknown'`/`0`.
Impact: Erros reais de banco de dados desaparecem sem log; o relatório final pode conter dados incompletos sem qualquer sinal de falha.
Recommendation: Converter para `async/await` com `Promise.all`, propagando erros corretamente.

### [MEDIUM] Validação de Entrada Ausente/Incompleta
File: src/AppManager.js:35, 132
Description: O checkout não exige senha (`p`) nem valida formato de e-mail/tipo de `cid`; o delete de usuário usa `req.params.id` sem checar que é numérico antes de ir ao banco.
Impact: Dados malformados chegam até a camada de banco sem erro claro ao cliente (400), e o `DELETE` pode ser chamado com IDs inválidos sem feedback apropriado.
Recommendation: Validar tipo e presença de cada campo na camada de rota antes de repassar ao controller (ver `architecture-guidelines.md`).

### [MEDIUM] Delete Deixa Dados Órfãos Sem Checar Linhas Afetadas
File: src/AppManager.js:131-137
Description: `DELETE FROM users` roda sem transação e sem checar `this.changes`; a resposta já avisa textualmente que "matrículas e pagamentos ficaram sujos no banco" (linha 135), confirmando que o comportamento incorreto é conhecido e não corrigido.
Impact: Dados órfãos em `enrollments`/`payments`/`audit_logs`, sem meio de saber se o delete de fato afetou alguma linha.
Recommendation: Fazer cascade de exclusão explícito (ou `FOREIGN KEY ... ON DELETE CASCADE` após corrigir o finding anterior) e checar `this.changes` antes de responder sucesso.

### [LOW] Números Mágicos em `badCrypto`
File: src/utils.js:19, 22
Description: `10000` (iterações do laço) e `10` (tamanho do truncamento) são literais sem nome/constante — além de, como já apontado, o próprio algoritmo ser inseguro.
Impact: Dificulta entender a intenção do código e ajustar parâmetros com segurança.
Recommendation: Eliminado junto com a troca para `bcrypt` (playbook #6/#11).

### [LOW] Nomes de Variáveis Pouco Descritivos
File: src/AppManager.js:29-33
Description: Campos do corpo da requisição são desestruturados em nomes de 1-2 letras (`u`, `e`, `p`, `cid`, `cc`), reduzindo a legibilidade do fluxo de checkout.
Impact: Aumenta o tempo de revisão/manutenção do código, maior chance de troca acidental de variável.
Recommendation: Renomear para `usuario`, `email`, `senha`, `cursoId`, `cartao`.

### [LOW] Driver de Banco Callback-Only / Contrato de Resposta Inconsistente
File: package.json:9-11; src/AppManager.js:35, 38, 48, 84, 131-136
Description: `sqlite3` (^5.1.6) só expõe API baseada em callback (raiz do "callback hell" acima); as respostas de erro misturam `res.status(400).send("texto")` (texto puro) com `res.json({...})` (JSON) sem padrão único, e não há middleware de erro central em `src/app.js`.
Impact: Força o estilo de código aninhado reportado como HIGH acima; clientes da API não podem confiar em um content-type/formato de erro único.
Recommendation: Migrar para `better-sqlite3` (API síncrona) ou `node:sqlite`, e centralizar respostas de erro em um middleware `(err, req, res, next)` (ver tabela de APIs deprecated e playbook #9).

================================
Total: 16 findings
================================
