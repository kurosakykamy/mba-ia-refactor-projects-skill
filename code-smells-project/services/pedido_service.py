from database import get_db
from middlewares.error_handler import AppError
from models import pedido_model, produto_model
from services import notification_service


class PedidoServiceError(AppError):
    """Erro de regra de negócio de pedido — vira resposta HTTP no handler central."""


class ProdutoNaoEncontradoError(PedidoServiceError):
    status_code = 404


class EstoqueInsuficienteError(PedidoServiceError):
    status_code = 400


class ItemInvalidoError(PedidoServiceError):
    status_code = 400


def _validar_item(item):
    if "produto_id" not in item or "quantidade" not in item:
        raise ItemInvalidoError("Cada item precisa de 'produto_id' e 'quantidade'")
    try:
        quantidade = int(item["quantidade"])
    except (TypeError, ValueError):
        raise ItemInvalidoError("Quantidade deve ser numérica")
    if quantidade < 1:
        # Sem esta checagem, uma quantidade negativa AUMENTA o estoque
        # e produz um total negativo.
        raise ItemInvalidoError("Quantidade deve ser maior que zero")
    return quantidade


def criar_pedido(usuario_id, itens):
    """Fluxo completo de criação de pedido, incluindo a notificação.

    Chamável fora do contexto HTTP (script/job) com o mesmo comportamento.
    """
    db = get_db()
    total = 0
    produtos_info = {}
    quantidades = {}

    for item in itens:
        quantidade = _validar_item(item)
        produto = produto_model.get_por_id(item["produto_id"])
        if produto is None:
            raise ProdutoNaoEncontradoError(f"Produto {item['produto_id']} não encontrado")
        if produto["estoque"] < quantidade:
            raise EstoqueInsuficienteError(f"Estoque insuficiente para {produto['nome']}")
        produtos_info[item["produto_id"]] = produto
        quantidades[item["produto_id"]] = quantidade
        total += produto["preco"] * quantidade

    pedido_id = pedido_model.criar(usuario_id, total, commit=False)
    for produto_id, quantidade in quantidades.items():
        produto = produtos_info[produto_id]
        pedido_model.adicionar_item(
            pedido_id, produto_id, quantidade, produto["preco"], commit=False
        )
        produto_model.decrementar_estoque(produto_id, quantidade, commit=False)

    db.commit()

    notification_service.notificar_novo_pedido(pedido_id, usuario_id)
    return {"pedido_id": pedido_id, "total": total}
