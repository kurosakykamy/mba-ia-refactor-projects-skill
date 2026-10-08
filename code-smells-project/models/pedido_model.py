from database import get_db


def criar(usuario_id, total, status="pendente", commit=True):
    db = get_db()
    cursor = db.execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
        (usuario_id, status, total),
    )
    if commit:
        db.commit()
    return cursor.lastrowid


def adicionar_item(pedido_id, produto_id, quantidade, preco_unitario, commit=True):
    db = get_db()
    db.execute(
        "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
        (pedido_id, produto_id, quantidade, preco_unitario),
    )
    if commit:
        db.commit()


def existe(pedido_id):
    db = get_db()
    row = db.execute("SELECT 1 FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
    return row is not None


def atualizar_status(pedido_id, novo_status):
    db = get_db()
    db.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
    db.commit()


def get_por_usuario(usuario_id):
    return _montar_pedidos(usuario_id=usuario_id)


def get_todos():
    return _montar_pedidos()


def _montar_pedidos(usuario_id=None):
    """Monta pedidos + itens com uma única query de JOIN (elimina N+1)."""
    db = get_db()
    if usuario_id is not None:
        pedidos_rows = db.execute(
            "SELECT * FROM pedidos WHERE usuario_id = ?", (usuario_id,)
        ).fetchall()
    else:
        pedidos_rows = db.execute("SELECT * FROM pedidos").fetchall()

    pedido_ids = [row["id"] for row in pedidos_rows]
    itens_por_pedido = {pid: [] for pid in pedido_ids}

    if pedido_ids:
        placeholders = ",".join("?" * len(pedido_ids))
        itens_rows = db.execute(
            f"""
            SELECT ip.pedido_id, ip.produto_id, ip.quantidade, ip.preco_unitario,
                   p.nome AS produto_nome
            FROM itens_pedido ip
            JOIN produtos p ON p.id = ip.produto_id
            WHERE ip.pedido_id IN ({placeholders})
            """,
            pedido_ids,
        ).fetchall()
        for item in itens_rows:
            itens_por_pedido[item["pedido_id"]].append(
                {
                    "produto_id": item["produto_id"],
                    "produto_nome": item["produto_nome"],
                    "quantidade": item["quantidade"],
                    "preco_unitario": item["preco_unitario"],
                }
            )

    return [
        {
            "id": row["id"],
            "usuario_id": row["usuario_id"],
            "status": row["status"],
            "total": row["total"],
            "criado_em": row["criado_em"],
            "itens": itens_por_pedido[row["id"]],
        }
        for row in pedidos_rows
    ]
