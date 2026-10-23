# Playbook de Refatoração (Fase 3)

Cada padrão abaixo mapeia 1:1 para um ou mais anti-patterns do catálogo. Use o exemplo antes/depois como referência de estilo, adaptando nomes/sintaxe à linguagem real do projeto-alvo.

## 1. Extrair segredos hardcoded para config via variável de ambiente
*(corrige anti-pattern #1)*

**Antes**
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
```

**Nunca faça isto** (erro comum: mover o literal para um módulo de config com *fallback* silencioso é fail-**open** — sem a variável de ambiente a aplicação sobe usando a chave que está commitada no repositório, exatamente o Impact original):
```python
class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-insecure-key")  # ainda hardcoded no caminho default
```

**Depois** — fail-**closed**: fora de desenvolvimento, a ausência do segredo impede o boot:
```python
# config/settings.py
import os

ENV = os.environ.get("APP_ENV", "development")


def _required_secret(name, dev_default):
    value = os.environ.get(name)
    if value:
        return value
    if ENV != "development":
        raise RuntimeError(
            f"{name} é obrigatório quando APP_ENV={ENV}. "
            "Configure a variável de ambiente antes de subir a aplicação."
        )
    return dev_default


class Settings:
    ENV = ENV
    SECRET_KEY = _required_secret("SECRET_KEY", "dev-only-insecure-key")
    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")

# app.py
app.config.from_object(Settings)
```

**Checklist para considerar este finding resolvido:**
- [ ] Nenhum literal de segredo permanece no código — nem como valor direto, nem como default usado fora de desenvolvimento.
- [ ] Subir com `APP_ENV=production` (ou equivalente) **sem** a variável definida falha explicitamente; testado de verdade, não presumido.
- [ ] O segredo que estava commitado foi considerado comprometido (rotacionar no ambiente real; anotar isso no relatório mesmo que o exercício não permita rotacionar).
- [ ] **Varredura exaustiva feita**: este checklist foi aplicado a **todos** os segredos/tokens do projeto, não só aos que algum finding nomeou. Um único default silencioso remanescente reabre o finding inteiro. (Ver "VARREDURA DE SEGREDOS" na Fase 3 do `SKILL.md`.)
- [ ] **Reavaliação por consumo**: se esta refatoração introduziu assinatura de token/sessão ou autenticação, os segredos já existentes foram reclassificados — um fallback antes inócuo vira CRITICAL quando passa a assinar credencial.
- [ ] **Config morta removida**: segredo sem nenhum consumidor no projeto foi **deletado** da config (padrão #13), não guardado — guardar o que ninguém lê só obriga o operador a configurar variável inútil.

## 2. Parametrizar queries SQL (eliminar concatenação)
*(corrige anti-pattern #2)*

**Antes**
```python
query = "SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"
cursor.execute(query)
```

**Depois**
```python
cursor.execute(
    "SELECT * FROM usuarios WHERE email = ? AND senha_hash = ?",
    (email, senha_hash),
)
```

## 3. Adicionar autenticação/autorização a rotas sensíveis
*(corrige anti-pattern #3)*

**Antes**
```python
@app.route("/admin/reset-db", methods=["POST"])
def reset_db():
    ...  # sem checagem nenhuma
```

**Nunca faça isto** (erro comum: delegar a decisão de segurança a uma função que não existe, ou a uma comparação trivial — um token previsível é o anti-pattern #14 aplicado à autenticação):
```python
def require_admin(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if request.headers.get("Authorization") != "admin":   # token adivinhável, sem assinatura
            return jsonify({"erro": "unauthorized"}), 401
        return fn(*args, **kwargs)
    return wrapper
```

**Depois** — token assinado e com expiração, verificado de verdade, com 401 (não autenticado) distinto de 403 (sem permissão):
```python
# middlewares/auth.py
from functools import wraps

from flask import current_app, jsonify, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

TOKEN_MAX_AGE_SECONDS = 60 * 60 * 24


def generate_token(user):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return serializer.dumps({"user_id": user.id})


def _resolve_user():
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        data = serializer.loads(header[len("Bearer "):], max_age=TOKEN_MAX_AGE_SECONDS)
    except (BadSignature, SignatureExpired):
        return None
    return User.query.get(data.get("user_id"))


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = _resolve_user()
        if not user:
            return jsonify({"erro": "unauthorized"}), 401
        request.current_user = user
        return fn(*args, **kwargs)
    return wrapper


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = _resolve_user()
        if not user:
            return jsonify({"erro": "unauthorized"}), 401      # não autenticado
        if not user.is_admin():
            return jsonify({"erro": "forbidden"}), 403          # autenticado, sem permissão
        request.current_user = user
        return fn(*args, **kwargs)
    return wrapper
```

**Autorização não é só autenticação.** Depois de exigir login, verifique também *quem* pode agir sobre *qual recurso*:
```python
# o usuário só altera a si mesmo; admin altera qualquer um
if target_user_id != request.current_user.id and not request.current_user.is_admin():
    return jsonify({"erro": "forbidden"}), 403

# campos que elevam privilégio nunca vêm do cliente em rota pública
role = "user" if not request.current_user.is_admin() else data.get("role", "user")
```

**Checklist para considerar este finding resolvido:**
- [ ] O token é **assinado e expira** — não é um valor previsível nem um identificador em texto puro.
- [ ] **Todas** as rotas sensíveis têm o decorator (percorra a lista de rotas uma a uma; a que ficar de fora é o furo).
- [ ] Existe checagem de **propriedade do recurso**, não só de login — testar que o usuário A não consegue alterar/apagar o recurso do usuário B.
- [ ] Nenhuma rota pública aceita campo que concede privilégio (`role`, `is_admin`) vindo do corpo da requisição — testar `POST` anônimo com `{"role": "admin"}` e confirmar que não cria admin.
- [ ] 401 e 403 são distinguidos.

## 4. Separar God-module por domínio
*(corrige anti-pattern #4)*

**Antes:** `models.py` (314 linhas) com funções de produto, usuário e pedido misturadas.

**Depois:**
```
models/
├── produto_model.py     # get_produto_por_id, criar_produto, atualizar_produto...
├── usuario_model.py      # criar_usuario, login_usuario...
└── pedido_model.py        # criar_pedido, get_pedidos_usuario...
```
Cada módulo só conhece sua própria tabela; funções que cruzam domínios (ex.: `criar_pedido` precisa checar estoque de produto) chamam a função pública do outro model em vez de acessar a tabela diretamente.

**Nunca faça isto**: dividir o arquivo só por domínio, deixando cada pedaço ainda misturando camadas. Três arquivos de 100 linhas que cada um define rota + monta SQL + aplica regra de negócio não resolvem o finding — trocam um CRITICAL por três HIGH (ver a gradação no catálogo, anti-pattern #4).

**Checklist para considerar este finding resolvido:**
- [ ] Separação por **domínio** (produto/usuário/pedido) **e** por **camada** (dados/negócio/HTTP) — as duas, não só a primeira.
- [ ] Nenhum arquivo em `models/` registra rota ou importa o objeto de request.
- [ ] Nenhum arquivo em `controllers/`/`views/` monta SQL ou chama o driver de banco diretamente.
- [ ] Nenhum model acessa tabela de outro domínio direto — passa pela função pública do model dono daquela tabela.

## 5. Mover regra de negócio do controller/rota para model ou service
*(corrige anti-pattern #5)*

**Antes**
```python
def criar_pedido():
    dados = request.get_json()
    total = 0
    for item in dados["itens"]:
        produto = buscar_produto_no_banco(item["produto_id"])
        total += produto["preco"] * item["quantidade"]
    print("ENVIANDO EMAIL...")
    print("ENVIANDO SMS...")
    ...
```

**Nunca faça isto** (erro comum: mover só o *cálculo* e deixar o **efeito colateral** ainda sendo disparado de dentro do controller — quem chamar o service fora do contexto HTTP continua sem a notificação, que é o Impact do finding):
```python
# controllers/pedido_controller.py
def criar_pedido():
    resultado = pedido_service.criar_pedido(...)
    notification_service.notificar_novo_pedido(resultado)   # efeito colateral ainda na camada HTTP
    return jsonify(resultado), 201
```

**Depois** — o controller só traduz HTTP; o fluxo de negócio completo (cálculo **e** efeitos) vive no service:
```python
# controllers/pedido_controller.py
def criar_pedido():
    dados = request.get_json()
    resultado = pedido_service.criar_pedido(dados["usuario_id"], dados["itens"])
    return jsonify(resultado), 201

# services/pedido_service.py
def criar_pedido(usuario_id, itens):
    total = sum(produto_model.get_preco(i["produto_id"]) * i["quantidade"] for i in itens)
    pedido = pedido_model.criar(usuario_id, itens, total)
    notification_service.notificar_novo_pedido(pedido)   # efeito colateral junto da regra que o dispara
    return pedido
```

**Checklist para considerar este finding resolvido:**
- [ ] O service pode ser chamado de um script/CLI/job (sem `request`) e o comportamento de negócio é **completo** — incluindo efeitos colaterais.
- [ ] O controller não contém cálculo de domínio, loop sobre dados para aplicar regra, nem disparo de efeito colateral.
- [ ] Nenhum módulo de `services/` importa `request`/`jsonify` (ou equivalente do framework).

## 6. Hash seguro de senha
*(corrige anti-pattern #6)*

**Antes**
```python
usuario["senha"] = senha  # texto puro
```
```javascript
function badCrypto(pwd) { /* base64 repetido, reversível */ }
```

**Depois**
```python
from werkzeug.security import generate_password_hash, check_password_hash

senha_hash = generate_password_hash(senha)
# login:
check_password_hash(usuario["senha_hash"], senha_informada)
```
```javascript
const bcrypt = require("bcrypt");
const hash = await bcrypt.hash(pwd, 10);
const ok = await bcrypt.compare(pwd, hash);
```

## 7. Resolver N+1 com join/eager-load ou batch fetch
*(corrige anti-pattern #7)*

**Antes**
```python
pedidos = get_todos_pedidos()
for pedido in pedidos:
    itens = get_itens_do_pedido(pedido["id"])          # 1 query por pedido
    for item in itens:
        produto = get_produto_por_id(item["produto_id"])  # 1 query por item
```

**Depois**
```sql
SELECT p.*, ip.produto_id, ip.quantidade, pr.nome AS produto_nome
FROM pedidos p
JOIN itens_pedido ip ON ip.pedido_id = p.id
JOIN produtos pr ON pr.id = ip.produto_id;
```
(uma única query; agrupar os resultados em memória por `pedido.id`)

## 8. Deduplicar lógica repetida em helper/service único
*(corrige anti-pattern #8)*

**Antes:** `get_pedidos_usuario` e `get_todos_pedidos` repetem ~25 linhas idênticas de montagem de resultado.

**Depois**
```python
def _montar_pedidos(cursor_pedidos):
    # lógica única de montagem, chamada pelas duas funções públicas
    ...

def get_pedidos_usuario(usuario_id):
    cur = db.execute("SELECT * FROM pedidos WHERE usuario_id = ?", (usuario_id,))
    return _montar_pedidos(cur)

def get_todos_pedidos():
    cur = db.execute("SELECT * FROM pedidos")
    return _montar_pedidos(cur)
```

## 9. Centralizar error handling
*(corrige anti-pattern #9)*

**Antes**
```python
try:
    ...
except Exception as e:
    return jsonify({"erro": str(e)}), 500   # repetido em toda rota
```

**Depois**
```python
# errors.py
class ValidationError(Exception): ...

@app.errorhandler(ValidationError)
def handle_validation(e):
    return jsonify({"erro": str(e)}), 400

@app.errorhandler(Exception)
def handle_unexpected(e):
    app.logger.exception("unhandled error")
    return jsonify({"erro": "internal_server_error"}), 500
```
Rotas passam a apenas `raise ValidationError("campo obrigatório")` quando aplicável, sem `try/except` próprio.

## 10. Remover estado global mutável
*(corrige anti-pattern #10)*

**Antes**
```javascript
let globalCache = {};
function logAndCache(key, data) { globalCache[key] = data; }
```

**Nunca faça isto** (erro comum: o Impact é *crescimento ilimitado de memória*, e envolver o mesmo objeto em uma classe não coloca limite nenhum):
```javascript
class RequestCache {
  constructor() { this.store = new Map(); }   // continua crescendo para sempre
  set(key, data) { this.store.set(key, data); }
  get(key) { return this.store.get(key); }
}
module.exports = new RequestCache();          // e continua sendo singleton de módulo
```
Mencionar TTL/lru-cache em um **comentário** também não conta — o limite tem que estar no código.

### Antes de escolher o "Depois": o valor é lido por alguém?

Faça esta checagem primeiro, com grep real no projeto inteiro:

```bash
grep -rn "cacheService\." src/     # ou o nome do seu cache/estado global
```

Se aparecem só chamadas de **escrita** (`.set(...)`) e nenhuma de **leitura** (`.get(...)`), o cache é *write-only*: ele não acelera nada, só consome memória. Nesse caso a correção certa é **remover**, não limitar.

**Depois (a) — valor nunca lido → remover**
```javascript
// cacheService.js: arquivo deletado.
// checkoutService.js: import e chamada removidos.
// -  const cacheService = require('./cacheService');
// -  cacheService.set(`last_checkout_${userId}`, course.title);
```
É impossível vazar memória em código que não existe — este é o fechamento mais forte possível do finding.

**Depois (b) — valor realmente lido → cache com limite de tamanho E expiração**
```javascript
const DEFAULT_MAX_ENTRIES = 500;
const DEFAULT_TTL_MS = 5 * 60 * 1000;

class BoundedCache {
    constructor(maxEntries = DEFAULT_MAX_ENTRIES, ttlMs = DEFAULT_TTL_MS) {
        this.maxEntries = maxEntries;
        this.ttlMs = ttlMs;
        this.store = new Map();          // Map preserva ordem de inserção → LRU barato
    }

    set(key, value) {
        if (this.store.has(key)) this.store.delete(key);
        this.store.set(key, { value, expiresAt: this.now() + this.ttlMs });
        // evicção por tamanho: descarta a entrada mais antiga
        while (this.store.size > this.maxEntries) {
            this.store.delete(this.store.keys().next().value);
        }
    }

    get(key) {
        const entry = this.store.get(key);
        if (!entry) return undefined;
        if (entry.expiresAt <= this.now()) {   // evicção por TTL
            this.store.delete(key);
            return undefined;
        }
        this.store.delete(key);                 // refresh da ordem LRU
        this.store.set(key, entry);
        return entry.value;
    }

    now() { return Date.now(); }   // sobrescrevível em teste, sem depender de relógio real
}
```
Equivalente em Python: `functools.lru_cache(maxsize=N)` para funções puras, ou `cachetools.TTLCache(maxsize=N, ttl=S)` para cache de dados.

**Depois (c) — estado que é por requisição → não deve ser singleton de módulo**
```python
# Antes: variável de módulo mutada via `global`, compartilhada entre requests concorrentes
# Depois: escopo da requisição (Flask `g`), criado e destruído a cada request
from flask import g

def get_request_cache():
    if "cache" not in g:
        g.cache = {}
    return g.cache
```

**Checklist para considerar este finding resolvido:**
- [ ] Grep confirma se o valor é lido em algum lugar — se não é, o cache foi **removido**, não "melhorado".
- [ ] Se o cache permaneceu: existe um **limite superior de entradas** no código (não em comentário), e a evicção foi testada inserindo `maxEntries + 1` itens.
- [ ] Se o cache permaneceu: entradas **expiram** por TTL, verificado com um relógio controlado no teste.
- [ ] Nenhum estado mutável compartilhado entre requisições concorrentes sobrou no escopo de módulo (`global x` em Python, `let` solto em JS) — ou ele é imutável, ou é por requisição, ou tem limite explícito.

## 11. Substituir magic numbers por constantes nomeadas
*(corrige anti-pattern #11)*

**Antes**
```python
if total > 10000:
    desconto = 0.10
elif total > 5000:
    desconto = 0.05
```

**Depois**
```python
# config/business_rules.py
DESCONTO_FAIXA_ALTA = 0.10
LIMITE_FAIXA_ALTA = 10_000
DESCONTO_FAIXA_MEDIA = 0.05
LIMITE_FAIXA_MEDIA = 5_000

if total > LIMITE_FAIXA_ALTA:
    desconto = DESCONTO_FAIXA_ALTA
elif total > LIMITE_FAIXA_MEDIA:
    desconto = DESCONTO_FAIXA_MEDIA
```

## 12. Trocar print/console.log por logging estruturado
*(corrige anti-pattern #12)*

**Antes**
```python
print(f"Login attempt: {email}")
```

**Nunca faça isto** (erro comum: trocar `print` por `logger.info` sem configurar handler/formatter — o formatter padrão **descarta** os campos de `extra`, então a saída continua sendo uma linha solta, sem nível útil nem destino configurável):
```python
logger.info("login attempt", extra={"email_hash": hash_email(email)})  # o extra some na saída
```

**Depois** — logging configurado no composition root, com nível e formato explícitos, e sem dado sensível no texto:
```python
# app.py (composition root) — configurar UMA vez
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

# controllers/usuario_controller.py
import logging
logger = logging.getLogger(__name__)

# identifica o evento sem expor PII: use o id, não o email/cartão/senha
logger.info("login.sucesso usuario_id=%s", usuario["id"])
logger.info("login.falhou")   # não logar qual email falhou — serve de oráculo para enumeração
```

**Checklist para considerar este finding resolvido:**
- [ ] `print`/`console.log` não aparecem mais no código de aplicação (`grep -rn "print(" src/` — scripts CLI isolados são aceitáveis).
- [ ] Existe configuração central de logging com nível e formato; a saída foi conferida de fato rodando a aplicação.
- [ ] Nenhum dado sensível (senha, cartão, token, email em fluxo de autenticação) aparece na saída de log.

## 13. Remover código/dependências mortas
*(corrige anti-pattern #13)*

**Antes:** `import sqlite3` não usado em `models.py`; `marshmallow`/`requests` no `requirements.txt` nunca importados.

**Depois:** remover o import e as linhas correspondentes do manifesto de dependências; se a função/serviço morto tiver utilidade real (ex.: `notification_service.py` bem escrito mas nunca chamado), **conectá-lo** ao fluxo correto em vez de apagar, quando isso resolver uma lacuna real (ex.: notificar usuário ao criar tarefa).

**Nunca faça isto**: religar código morto sem antes verificar se ele **funciona** e se ele próprio não é um anti-pattern. Conectar ao fluxo de produção um serviço que só simula o efeito (um "envio de email" que faz `print`, um "gateway" que aprova por heurística trivial) troca um LOW por um achado do anti-pattern #14 — e agora no caminho real da aplicação, o que é pior do que o código estar morto.

**Checklist para considerar este finding resolvido:**
- [ ] Para cada trecho morto: a decisão entre **remover** e **religar** foi explícita — não ficou nem apagado por engano nem religado por inércia.
- [ ] Se foi religado: o código funciona de verdade (não é simulação), e isso foi verificado executando o fluxo.
- [ ] Se foi religado: o novo caminho não introduz efeito colateral indesejado (ex.: chamada de rede bloqueante dentro do request sem timeout).
- [ ] `grep` confirma que o que ficou no projeto tem pelo menos um call site real.

## 14. Substituir regra de negócio crítica simulada por validação real + mock isolado do fluxo de produção
*(corrige anti-pattern #14)*

**Nunca faça isto** (erro comum: tratar o finding como um problema de organização e só mudar o código de lugar):
```javascript
// services/paymentGatewayService.js — "corrigido" só na localização, não no comportamento
function charge(cardNumber) {
    const status = cardNumber.startsWith('4') ? 'PAID' : 'DENIED';  // ainda fraudável
    return { status };
}
```

**Antes** (regra fraudável, decide por prefixo do input)
```javascript
function charge(cardNumber) {
    const status = cardNumber.startsWith('4') ? 'PAID' : 'DENIED';
    return { status };
}
```

**Depois** — validação real (Luhn) sempre aplicada; a parte simulada só aprova um conjunto fixo e documentado de valores de teste (mesma convenção de sandboxes reais como Stripe), habilitada só em modo explícito de desenvolvimento/teste, com falha explícita (fail-closed) se usada fora dele:
```javascript
// utils/cardValidation.js
function luhnCheck(cardNumber) {
    const digits = String(cardNumber).replace(/\D/g, '');
    if (digits.length < 12) return false;
    let sum = 0, shouldDouble = false;
    for (let i = digits.length - 1; i >= 0; i--) {
        let digit = parseInt(digits[i], 10);
        if (shouldDouble && (digit *= 2) > 9) digit -= 9;
        sum += digit;
        shouldDouble = !shouldDouble;
    }
    return sum % 10 === 0;
}
module.exports = { luhnCheck };

// config/settings.js — fail-closed: a config recusa carregar em config insegura
const settings = {
    nodeEnv: process.env.NODE_ENV || 'development',
    paymentGatewayMode: process.env.PAYMENT_GATEWAY_MODE || 'mock',
    // ...
};
if (settings.nodeEnv === 'production' && settings.paymentGatewayMode === 'mock') {
    throw new Error('PAYMENT_GATEWAY_MODE=mock não é permitido com NODE_ENV=production.');
}
module.exports = settings;

// services/paymentGatewayService.js
const settings = require('../config/settings');
const { luhnCheck } = require('../utils/cardValidation');

const MOCK_APPROVED_TEST_CARDS = new Set(['4242424242424242']); // nunca "começa com 4"

class PaymentGatewayNotConfiguredError extends Error {}

function charge(cardNumber) {
    if (!luhnCheck(cardNumber)) return { status: 'DENIED', reason: 'invalid_card_number' };
    if (settings.paymentGatewayMode !== 'mock') {
        throw new PaymentGatewayNotConfiguredError('Nenhum gateway de pagamento real integrado.');
    }
    const status = MOCK_APPROVED_TEST_CARDS.has(cardNumber) ? 'PAID' : 'DENIED';
    return { status, reason: status === 'DENIED' ? 'card_not_in_test_set' : undefined };
}
module.exports = { charge, PaymentGatewayNotConfiguredError };
```

**Equivalente em Python** (ex.: verificação de desconto/autorização simulada por valor hardcoded):
```python
# Antes — "autorização" decide por um token fixo no código
def autorizar_reembolso(token):
    return token == "qualquer-coisa-123"  # qualquer um que descubra o literal passa

# Depois — validação real (assinatura/expiração) + modo de teste isolado e fail-closed
import os

MODO_PAGAMENTO = os.environ.get("PAYMENT_GATEWAY_MODE", "mock")
if os.environ.get("ENV") == "production" and MODO_PAGAMENTO == "mock":
    raise RuntimeError("PAYMENT_GATEWAY_MODE=mock não é permitido em produção")

def autorizar_reembolso(token):
    if not validar_assinatura_real(token):
        return False
    if MODO_PAGAMENTO != "mock":
        raise GatewayNaoConfiguradoError("Nenhum provedor real integrado")
    return token in TOKENS_DE_TESTE_DOCUMENTADOS
```

**Checklist para considerar este finding resolvido** (não basta compilar/rodar):
- [ ] A validação real (ex.: Luhn, assinatura, checksum) é aplicada **sempre**, antes de qualquer branch de simulação.
- [ ] A aprovação simulada só acontece para um conjunto fixo, pequeno e documentado de valores — nunca por prefixo/sufixo/padrão do input do usuário.
- [ ] Rodar com a flag de modo real desligada (ou `NODE_ENV=production`) falha explicitamente, em vez de silenciosamente aprovar.
- [ ] Testar manualmente um input que antes passava pela heurística trivial (ex.: `4111111111111111`, que começa com "4" mas não está no conjunto de teste) e confirmar que agora é rejeitado.

---

14 padrões cobertos (acima do mínimo de 8 exigido). Ao aplicar cada um, confirme que o finding correspondente no relatório de auditoria é fechado, e rode a validação de boot + endpoints (ver `SKILL.md`, Fase 3) antes de considerar a transformação concluída.

## O que significa "fechado" — vale para TODOS os padrões

Um finding só está fechado quando o **`Impact` descrito no relatório deixa de ser reproduzível no código gerado**. Mudar a forma — mover para outro arquivo, envolver em classe/função, renomear, criar a pasta certa — **não** fecha finding nenhum por si só.

Teste mental, padrão a padrão: *"se eu reexecutar exatamente a situação descrita no campo `Impact`, ela ainda acontece?"*

| Impact no relatório | Pergunta de fechamento |
|---|---|
| "memória cresce sem limite" | Existe um teto de entradas **no código**? Inserir `max+1` itens evicta? |
| "qualquer um aprova o próprio pagamento" | O input que antes passava pela heurística trivial agora é rejeitado? |
| "chave fica exposta no repositório" | Subir sem a variável de ambiente **falha**, em vez de usar o default? |
| "N+1 queries" | Contei as queries? Sobrou alguma dentro de loop? |
| "endpoint retorna a tabela inteira" | O endpoint aceita `page`/`per_page` e o limite é aplicado de fato? |
| "qualquer anônimo apaga/promove" | Testei a chamada anônima e ela foi recusada? |
| "erros somem sem rastro" | O handler **loga** antes de responder? |
| "serviço nunca é chamado" | `grep` mostra um call site real, e o fluxo foi executado? |

Se a resposta exigir "bom, na prática a pessoa não faria isso" ou "está documentado no comentário", o finding **não** está fechado.
