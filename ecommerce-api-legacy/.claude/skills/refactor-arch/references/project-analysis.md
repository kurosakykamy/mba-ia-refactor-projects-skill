# Project Analysis — Heurísticas (Fase 1)

Objetivo da Fase 1: produzir um resumo factual e verificável do projeto **antes** de julgar qualidade. Nada aqui deve exigir opinião — são checagens mecânicas sobre arquivos reais.

## 1. Detecção de linguagem

Olhe para extensões de arquivo predominantes na raiz e em subpastas de código (ignore `node_modules/`, `venv/`, `.git/`, `__pycache__/`, `dist/`, `build/`):

| Extensão dominante | Linguagem |
|---|---|
| `.py` | Python |
| `.js` / `.mjs` / `.cjs` | JavaScript (Node.js) |
| `.ts` | TypeScript |
| `.java` | Java |
| `.rb` | Ruby |
| `.go` | Go |
| `.php` | PHP |

Confirme com o arquivo de manifesto correspondente (ver tabela abaixo) — a extensão sozinha pode enganar em projetos mistos.

## 2. Detecção de framework e dependências

Leia o manifesto de dependências do ecossistema identificado:

| Manifesto | Ecossistema | Onde olhar |
|---|---|---|
| `requirements.txt`, `Pipfile`, `pyproject.toml` | Python | linhas `flask`, `django`, `fastapi`, `bottle` |
| `package.json` | Node.js | chave `dependencies`/`devDependencies`: `express`, `fastify`, `koa`, `nestjs` |
| `pom.xml` / `build.gradle` | Java | `spring-boot-starter`, `javax.servlet` |
| `Gemfile` | Ruby | `rails`, `sinatra` |
| `go.mod` | Go | `gin-gonic`, `labstack/echo` |

Capture a **versão exata** declarada (ex.: `flask==3.1.1`, `"express": "^4.18.2"`) — ela é necessária para a checagem de APIs deprecated no catálogo de anti-patterns.

Liste junto as dependências "chamativas" (ex.: `flask-cors`, `sqlite3`, `bcrypt`) — elas ajudam a entender integrações (CORS, banco, criptografia) sem abrir cada arquivo.

## 3. Detecção de banco de dados

Procure, nessa ordem:
1. Import de driver/ORM no código: `sqlite3`, `psycopg2`, `pymongo`, `sqlalchemy`, `mongoose`, `sequelize`, `prisma`.
2. String de conexão ou path de arquivo (`.db`, `.sqlite3`, `DATABASE_URL`, `mongodb://`, `postgres://`).
3. Comandos DDL (`CREATE TABLE`, `db.define`, classes de modelo com `Column(...)`).

A partir disso extraia:
- **Tipo de banco** (SQLite / Postgres / MongoDB / MySQL / em memória).
- **Tabelas/coleções** — via `CREATE TABLE <nome>` ou nomes de classes de modelo/ORM.

## 4. Mapeamento da arquitetura atual

Conte arquivos de código-fonte (exclua testes, configs, lockfiles) e observe a estrutura de pastas:

- **Monolítica / sem camadas**: poucos arquivos (tipicamente ≤5) na raiz, cada um concentrando rotas + lógica + acesso a dados. Sinal: um único arquivo com `app.run(...)` **e** queries SQL **e** definição de rotas.
- **Parcialmente organizada**: existem pastas como `models/`, `routes/`, `controllers/`, `services/`, `utils/`, mas pelo menos uma camada está ausente, inconsistente ou "furada" (ex.: regra de negócio pesada dentro de `routes/`, ou uma `services/` que existe mas não é chamada por ninguém — grep por uso real, não só por existência do arquivo).
- **MVC bem formado**: as 3 camadas (Model / View·Routes / Controller) existem, cada arquivo tem responsabilidade única, há módulo de config e error handling centralizado.

Regra prática: não confie apenas na existência de pastas — **grep cada função de "camada correta" (ex: `services/`, helpers de validação) para confirmar se ela é realmente importada/chamada em algum lugar**. Código morto não conta como organização.

## 5. Detecção de domínio de negócio

Sem ler toda a lógica, infira o domínio a partir de:
- Nomes de rotas (`/produtos`, `/pedidos`, `/courses`, `/enrollments`, `/tasks`).
- Nomes de tabelas/modelos (`produtos`, `usuarios`, `pedidos`, `courses`, `payments`, `tasks`, `categories`).
- Nome do pacote/descrição em `package.json`/`README.md`.

Descreva o domínio em uma frase curta (ex.: "E-commerce API (produtos, pedidos, usuários)", "LMS com fluxo de checkout", "Task Manager API").

## 6. Saída da Fase 1

Imprima exatamente neste formato (valores substituídos pelos reais):

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem>
Framework:     <framework + versão>
Dependencies:  <libs relevantes, separadas por vírgula>
Domain:        <frase curta do domínio>
Architecture:  <Monolítica | Parcialmente organizada | MVC> — <justificativa de 1 linha>
Source files:  <N> files analyzed
DB tables:     <lista de tabelas/coleções>
================================
```

Não avance para a Fase 2 sem ter todos os campos preenchidos com valores reais (nunca "N/A" sem investigar antes).
