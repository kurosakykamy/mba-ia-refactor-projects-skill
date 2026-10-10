# Playbook de Refatoração (Fase 3)

Cada padrão abaixo mapeia 1:1 para um ou mais anti-patterns do catálogo. Use o exemplo antes/depois como referência de estilo, adaptando nomes/sintaxe à linguagem real do projeto-alvo.

## 1. Extrair segredos hardcoded para config via variável de ambiente
*(corrige anti-pattern #1)*

**Antes**
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
```

**Depois**
```python
# config/settings.py
import os

class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-insecure-key")
    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")

# app.py
app.config.from_object(Settings)
```

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

**Depois**
```python
from functools import wraps
from flask import request, jsonify

def require_admin(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not auth_service.is_valid_admin_token(token):
            return jsonify({"erro": "unauthorized"}), 401
        return fn(*args, **kwargs)
    return wrapper

@app.route("/admin/reset-db", methods=["POST"])
@require_admin
def reset_db():
    ...
```

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

**Depois**
```python
# controllers/pedido_controller.py
def criar_pedido():
    dados = request.get_json()
    resultado = pedido_service.criar_pedido(dados["usuario_id"], dados["itens"])
    notification_service.notificar_novo_pedido(resultado)
    return jsonify(resultado), 201

# services/pedido_service.py
def criar_pedido(usuario_id, itens):
    total = sum(produto_model.get_preco(i["produto_id"]) * i["quantidade"] for i in itens)
    return pedido_model.criar(usuario_id, itens, total)
```

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

**Depois**
```javascript
// encapsular em uma instância/serviço com ciclo de vida explícito, ou usar um cache
// com TTL/tamanho máximo (ex.: lru-cache) em vez de objeto solto no módulo
class RequestCache {
  constructor() { this.store = new Map(); }
  set(key, data) { this.store.set(key, data); }
  get(key) { return this.store.get(key); }
}
```

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

**Depois**
```python
import logging
logger = logging.getLogger(__name__)
logger.info("login attempt", extra={"email_hash": hash_email(email)})
```

## 13. Remover código/dependências mortas
*(corrige anti-pattern #13)*

**Antes:** `import sqlite3` não usado em `models.py`; `marshmallow`/`requests` no `requirements.txt` nunca importados.

**Depois:** remover o import e as linhas correspondentes do manifesto de dependências; se a função/serviço morto tiver utilidade real (ex.: `notification_service.py` bem escrito mas nunca chamado), **conectá-lo** ao fluxo correto em vez de apagar, quando isso resolver uma lacuna real (ex.: notificar usuário ao criar tarefa).

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

14 padrões cobertos (acima do mínimo de 8 exigido). Ao aplicar cada um, confirme que o finding correspondente no relatório de auditoria é fechado, e rode a validação de boot + endpoints (ver `SKILL.md`, Fase 3) antes de considerar a transformação concluída. Para o padrão #14 em particular, "fechado" significa que a heurística trivial deixou de decidir o resultado — não apenas que o código mudou de arquivo.
