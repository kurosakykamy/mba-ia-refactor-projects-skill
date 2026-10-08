from config.settings import Settings
from database import get_db


def gerar_relatorio_vendas():
    db = get_db()

    total_pedidos = db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
    faturamento = db.execute("SELECT SUM(total) FROM pedidos").fetchone()[0] or 0
    pendentes = db.execute(
        "SELECT COUNT(*) FROM pedidos WHERE status = ?", ("pendente",)
    ).fetchone()[0]
    aprovados = db.execute(
        "SELECT COUNT(*) FROM pedidos WHERE status = ?", ("aprovado",)
    ).fetchone()[0]
    cancelados = db.execute(
        "SELECT COUNT(*) FROM pedidos WHERE status = ?", ("cancelado",)
    ).fetchone()[0]

    desconto = 0
    if faturamento > Settings.LIMITE_FAIXA_ALTA:
        desconto = faturamento * Settings.DESCONTO_FAIXA_ALTA
    elif faturamento > Settings.LIMITE_FAIXA_MEDIA:
        desconto = faturamento * Settings.DESCONTO_FAIXA_MEDIA
    elif faturamento > Settings.LIMITE_FAIXA_BAIXA:
        desconto = faturamento * Settings.DESCONTO_FAIXA_BAIXA

    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": pendentes,
        "pedidos_aprovados": aprovados,
        "pedidos_cancelados": cancelados,
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
    }
