import logging

logger = logging.getLogger(__name__)


def notificar_novo_pedido(pedido_id, usuario_id):
    logger.info("notificacao.pedido_criado pedido_id=%s usuario_id=%s", pedido_id, usuario_id)


def notificar_status_pedido(pedido_id, status):
    logger.info("notificacao.status_atualizado pedido_id=%s status=%s", pedido_id, status)
