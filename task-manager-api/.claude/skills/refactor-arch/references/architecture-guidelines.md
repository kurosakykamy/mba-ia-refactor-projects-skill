# Guidelines de Arquitetura MVC Alvo (Fase 3)

Estas regras são **agnósticas de linguagem**. Aplique os princípios; adapte nomes de arquivo/pasta à convenção idiomática do framework (notas específicas no final).

## Camadas e responsabilidades

### Models (`models/`)
- Representam dados e regras **intrínsecas aos dados** (validação de formato do próprio campo, serialização `to_dict`/`to_json`, relacionamentos).
- Concentram **todo** acesso a dados (queries/ORM). Nenhuma outra camada deve montar SQL ou chamar o driver de banco diretamente.
- Um arquivo de model por entidade/domínio (ex.: `produto_model.py`, `pedido_model.py`), nunca um único arquivo cobrindo múltiplas entidades não relacionadas.
- **Não** contêm: parsing de request HTTP, formatação de resposta HTTP, regras de negócio que cruzam múltiplas entidades (isso é Controller/Service).

### Views / Routes (`views/` ou `routes/`)
- Única responsabilidade: mapear método HTTP + path → função de controller, e extrair/validar o **formato** básico do payload (presença de campos, tipos primitivos).
- Não contêm lógica de negócio, não acessam o banco diretamente, não calculam nada além do estritamente necessário para montar a chamada ao controller.
- Devem ser "finas" — se uma rota tem mais de ~15-20 linhas de lógica própria, provavelmente há regra de negócio vazando para essa camada (ver anti-pattern #5 do catálogo).

### Controllers (`controllers/`)
- Orquestram o fluxo: recebem dados já validados da rota, chamam o(s) model(s)/service(s) necessários, aplicam regra de negócio que não é exclusiva de uma única entidade, decidem o status HTTP e a forma da resposta.
- Um controller por domínio (ex.: `produto_controller.py`, `pedido_controller.py`), não um único controller genérico para tudo.
- Podem delegar para uma camada de `services/` quando a regra de negócio for complexa o suficiente para merecer testes isolados da camada HTTP — não é obrigatório criar `services/` para regras triviais, mas é obrigatório **não deixar a regra de negócio pesada dentro da rota**.

### Config (`config/`)
- Único lugar onde `SECRET_KEY`, string de conexão de banco, chaves de API, flags de debug são lidos — sempre de variável de ambiente (`os.environ`/`process.env`), nunca hardcoded.
- Fornece valores default seguros para desenvolvimento local, mas nunca credenciais reais.

### Error handling centralizado
- Um único ponto (error handler Flask via `@app.errorhandler`, middleware de erro Express via `(err, req, res, next)`) que traduz exceções em respostas HTTP consistentes (mesmo formato de JSON de erro em toda a API).
- Controllers/rotas lançam/propagam exceções específicas; não fazem `try/except` genérico individualmente em cada função a menos que precisem tratar um caso particular.

### Composition root / entry point
- Um único arquivo (`app.py`/`main.py`/`src/app.js`) responsável por: criar a aplicação, carregar config, registrar rotas/blueprints/routers, registrar o error handler, e iniciar o servidor.
- Não deve conter lógica de negócio nem definição de rota inline além do registro.

## Checklist estrutural de saída (Fase 3 deve satisfazer todos os itens)

- [ ] Estrutura de diretórios segue o padrão MVC (Model / View-Route / Controller claramente separados em pastas ou módulos distintos)
- [ ] Configuração extraída para módulo de config, sem segredo hardcoded no código
- [ ] Um model por entidade/domínio relevante
- [ ] Rotas finas, sem lógica de negócio
- [ ] Controllers concentram o fluxo de orquestração
- [ ] Error handling centralizado (não um `try/except` genérico copiado em cada função)
- [ ] Entry point único e claro (composition root)
- [ ] Aplicação sobe sem erros
- [ ] Endpoints originais continuam respondendo com o mesmo contrato observável (mesmo path, mesmo método, mesmo formato de resposta — mudanças internas não devem quebrar clientes existentes)

## Notas específicas por framework

**Flask**: use Blueprints (`Blueprint('produtos', __name__)`) como a unidade de "Views/Routes"; `@app.errorhandler(Exception)` / `@app.errorhandler(404)` para error handling centralizado; `app.register_blueprint(...)` no composition root.

**Express**: use `express.Router()` por domínio como "Views/Routes"; middleware de erro com assinatura `(err, req, res, next)` registrado **por último** em `app.js` como error handling centralizado; controllers como módulos de função exportados, não classes "manager" genéricas.

## Adaptação ao nível de organização existente

- Projeto **monolítico** (tudo em poucos arquivos): a Fase 3 cria a estrutura de pastas do zero e migra o código, domínio por domínio.
- Projeto **parcialmente organizado** (já tem `models/`, `routes/`, `services/`, `utils/`): não refaça o que já está correto — identifique especificamente o que viola as regras acima (ex.: lógica duplicada que deveria estar em `services/` e usar `utils/helpers.py` já existente, camada de rota fazendo acesso direto a dado, serviço morto nunca chamado) e corrija esses pontos pontualmente, preservando a estrutura de pastas que já faz sentido.
