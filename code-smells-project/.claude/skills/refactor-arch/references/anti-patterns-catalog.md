# Catálogo de Anti-Patterns (Fase 2)

Cada anti-pattern abaixo tem: **sinal de detecção objetivo** (o que procurar no código, não opinião), **severidade** fixa (ou faixa, quando depende do contexto) e **por que importa**. Use isto como checklist — percorra o catálogo inteiro em todo projeto, mesmo que ele já pareça organizado: organização de pastas não implica ausência desses problemas.

Escala de severidade (fixada no enunciado do desafio):
- **CRITICAL** — falha grave de arquitetura/segurança: impede funcionamento correto, expõe dados sensíveis, ou quebra completamente a separação de responsabilidades.
- **HIGH** — forte violação de MVC/SOLID que dificulta muito manutenção/testes.
- **MEDIUM** — padronização, duplicação, performance moderada.
- **LOW** — legibilidade, nomenclatura, magic numbers.

---

### 1. Hardcoded Credentials / Secrets — CRITICAL
**Sinal:** literais de string atribuídos a variáveis/campos chamados (ou contendo) `secret`, `key`, `password`, `senha`, `pass`, `token`, `api_key`, `*_pass`, diretamente no código-fonte (não via `os.environ`/`process.env`).
**Por quê:** qualquer pessoa com acesso ao repositório tem a credencial de produção; não há como revogar sem trocar o código e fazer deploy.
**Exemplo real encontrado:** `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"`.

### 2. SQL / NoSQL Injection — CRITICAL
**Sinal:** montagem de query por **concatenação de string ou f-string** com dado vindo de request (`+ variavel +`, `f"... {var} ..."`, template literals `` `...${var}...` `` passados a `cursor.execute`/`db.run`), em vez de placeholders (`?`, `%s`, `$1`) ou métodos do ORM.
**Por quê:** permite ao atacante alterar a query, ler/alterar/apagar dados fora do escopo pretendido, ou (no pior caso) burlar autenticação.
**Não é SQLi (falso positivo comum):** uso de f-string **dentro de métodos do ORM** que fazem bind automático (ex.: `Model.query.filter(Model.campo.like(f"%{termo}%"))` do SQLAlchemy) — o ORM parametriza a chamada; sinalize como nota de estilo (LOW) por confundir revisores, não como CRITICAL.

### 3. Missing Authentication / Authorization — CRITICAL
**Sinal:** rota que executa ação sensível (deletar recurso, relatório financeiro/admin, alterar estado de outro usuário, executar SQL arbitrário) sem nenhuma checagem de identidade/permissão antes do corpo da função. Também conta um fluxo de login que **emite** um token/sessão mas que **nenhuma outra rota verifica** (grep pelo nome da variável do token em todo o projeto — se só aparece no login, a autenticação é decorativa).
**Por quê:** qualquer chamador anônimo tem acesso total à ação protegida.

### 4. God Class / God Module — CRITICAL (se um único arquivo cobre >2 domínios de negócio + acesso a dados + rotas) ou HIGH (se cobre 1 domínio mas mistura camadas)
**Sinal:** um arquivo que contém, ao mesmo tempo: definição de rotas, queries/acesso a dados e regra de negócio para múltiplas entidades diferentes. Medida prática: >200 linhas misturando essas responsabilidades, ou um único arquivo do qual dependem todas as rotas da aplicação.
**Por quê:** impossível testar em isolamento; qualquer mudança tem raio de impacto imprevisível.

### 5. Business Logic Leaking into Controllers/Routes — HIGH
**Sinal:** dentro de uma view/rota/controller: cálculos de negócio (totais, descontos, validação de regras de domínio), loops sobre dados para aplicar regras, ou chamadas diretas de "efeitos colaterais" (enviar e-mail/SMS simulado) — em vez de delegar a uma camada de model/service.
**Por quê:** a mesma regra de negócio não pode ser reusada/testada fora do contexto HTTP; duplica-se quando outra rota precisa da mesma regra.

### 6. Broken/Weak Cryptography for Passwords — CRITICAL
**Sinal:** senha armazenada em texto puro, ou hash com `md5`/`sha1` sem salt, ou função de "hash" caseira (loop manual de encode/base64) em vez de `bcrypt`/`werkzeug.security.generate_password_hash`/`argon2`.
**Por quê:** qualquer vazamento do banco expõe senhas reais em texto puro ou quebráveis em segundos.

### 7. N+1 Queries — MEDIUM (HIGH se aninhado em 2+ níveis, ex. N×M+1)
**Sinal:** uma query que retorna uma lista, seguida de **outra query dentro do loop** sobre essa lista para buscar dados relacionados (em vez de JOIN, `select_related`/`joinedload`, ou batch fetch com `IN (...)`).
**Por quê:** número de round-trips ao banco cresce linearmente (ou pior) com o volume de dados; degradação de performance que só aparece em produção com dados reais.

### 8. Duplicated Logic / Copy-Paste Functions — MEDIUM
**Sinal:** duas funções com >70% de linhas idênticas, ou a mesma validação/transformação reescrita manualmente em 3+ lugares quando já existe uma função/helper equivalente **não utilizada** em algum módulo de utils/model (grep para confirmar que a função "correta" existe mas não é chamada).
**Por quê:** correções e regras de negócio divergem silenciosamente entre as cópias ao longo do tempo.

### 9. Generic/Swallowed Error Handling — MEDIUM
**Sinal:** `except:` ou `except Exception as e: return jsonify({"erro": str(e)}), 500` genérico repetido rota a rota, sem logging estruturado, sem distinguir erro de validação (4xx) de erro interno (5xx), e frequentemente vazando a mensagem de exceção crua ao cliente.
**Por quê:** falhas reais passam despercebidas (sem log) e detalhes internos (stack trace, nomes de coluna, paths) vazam para o cliente.

### 10. Mutable Global State — HIGH
**Sinal:** variável no escopo do módulo, fora de qualquer classe/função, que é **reatribuída** em tempo de execução (`global x` em Python; `let`/objeto solto reatribuído em JS) e compartilhada entre requests, sem nenhum mecanismo de concorrência.
**Por quê:** em um servidor com múltiplas requisições concorrentes (ou múltiplos workers), o estado de uma requisição vaza/corrompe o de outra.

### 11. Magic Numbers / Hardcoded Business Constants — LOW
**Sinal:** literais numéricos ou de string (faixas de desconto, limites de validação, listas de categorias válidas, status válidos) embutidos inline em uma função, sem constante nomeada, especialmente quando o mesmo valor se repete em mais de um lugar.
**Por quê:** o significado do número não é óbvio para quem lê depois, e mudar a regra exige caçar todas as ocorrências.

### 12. Print-based / Ad-hoc Logging — LOW
**Sinal:** uso de `print(...)`/`console.log(...)` para registrar eventos de aplicação (incluindo dados sensíveis como email/cartão) em vez do módulo de logging padrão da linguagem/framework.
**Por quê:** sem nível de log, sem destino configurável, sem estrutura — inútil em produção, e risco de vazar dado sensível no stdout.

### 13. Dead / Unused Code and Dependencies — LOW
**Sinal:** imports nunca referenciados no arquivo; funções/serviços definidos mas nunca chamados em todo o projeto (grep confirma zero call sites); dependências no manifesto (`requirements.txt`/`package.json`) nunca importadas no código.
**Por quê:** aumenta superfície de manutenção e engana o leitor sobre o que o sistema realmente faz.

---

## Detecção de APIs / Padrões Deprecated

Verifique a versão declarada do framework/driver (Fase 1) contra esta lista e recomende o substituto moderno. Classifique como **MEDIUM** (funciona mas está obsoleto/será removido) ou **HIGH** (já removido/quebra em versões recentes, ou é uma prática insegura conhecida):

| API / padrão deprecated | Onde aparece | Substituto moderno | Severidade |
|---|---|---|---|
| `sqlite3` (driver Node, callback-only) | `require('sqlite3')` em projetos Node | `node:sqlite` (nativo, Node ≥22) ou `better-sqlite3` (API síncrona) | MEDIUM |
| `app.before_first_request` (Flask) | removido no Flask 2.3+ | inicialização no composition root, antes de `app.run()` | HIGH (quebra o boot se presente) |
| `flask.Markup` | removido no Flask 2.3+ | `markupsafe.Markup` | MEDIUM |
| `datetime.utcnow()` / `datetime.utcfromtimestamp()` (Python) | deprecated desde Python 3.12 | `datetime.now(timezone.utc)` | MEDIUM |
| Hash de senha com `hashlib.md5`/`sha1` | qualquer `models/user.py`-like | `werkzeug.security.generate_password_hash` (Flask) ou `bcrypt` | CRITICAL (tratado também como item 6 acima) |
| `app.run(debug=True)` exposto como servidor de produção | qualquer `app.py` sem WSGI server | `gunicorn`/`waitress` atrás de proxy, `debug=False` | CRITICAL |
| Callbacks aninhados sem `Promise`/`async-await` (Node) | `db.get(..., function(err, row) {...})` encadeado | `async/await` com wrapper baseado em Promise, ou driver com API de Promise nativa | MEDIUM |
| CORS totalmente aberto (`CORS(app)` sem origem) | Flask-CORS / `cors()` Express sem opções | `CORS(app, origins=[...])` / `cors({ origin: [...] })` explícito | MEDIUM |

Esta tabela não é exaustiva — ao encontrar uma versão de dependência real, confirme no changelog oficial se há aviso de deprecação antes de classificar.

## Mínimo de cobertura

Este catálogo contém 13 anti-patterns numerados (acima do mínimo de 8 exigido), cobrindo as 4 faixas de severidade, mais a tabela dedicada de APIs deprecated. Ao gerar o relatório de auditoria (Fase 2), **todo finding deve referenciar o número do anti-pattern deste catálogo** (ex.: "Anti-pattern #2 — SQL Injection") além de severidade, arquivo e linha.
