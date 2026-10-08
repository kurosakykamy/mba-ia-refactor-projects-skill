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

---

13 padrões cobertos (acima do mínimo de 8 exigido). Ao aplicar cada um, confirme que o finding correspondente no relatório de auditoria é fechado, e rode a validação de boot + endpoints (ver `SKILL.md`, Fase 3) antes de considerar a transformação concluída.
