from database import get_db
from models import pedido_model, produto_model


class PedidoServiceError(Exception):
    pass


class ProdutoNaoEncontradoError(PedidoServiceError):
    pass


class EstoqueInsuficienteError(PedidoServiceError):
    pass


def criar_pedido(usuario_id, itens):
    db = get_db()
    total = 0
    produtos_info = {}

    for item in itens:
        produto = produto_model.get_por_id(item["produto_id"])
        if produto is None:
            raise ProdutoNaoEncontradoError(f"Produto {item['produto_id']} não encontrado")
        if produto["estoque"] < item["quantidade"]:
            raise EstoqueInsuficienteError(f"Estoque insuficiente para {produto['nome']}")
        produtos_info[item["produto_id"]] = produto
        total += produto["preco"] * item["quantidade"]

    pedido_id = pedido_model.criar(usuario_id, total, commit=False)
    for item in itens:
        produto = produtos_info[item["produto_id"]]
        pedido_model.adicionar_item(
            pedido_id, item["produto_id"], item["quantidade"], produto["preco"], commit=False
        )
        produto_model.decrementar_estoque(item["produto_id"], item["quantidade"], commit=False)

    db.commit()
    return {"pedido_id": pedido_id, "total": total}
