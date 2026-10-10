const settings = require('../config/settings');
const { luhnCheck } = require('../utils/cardValidation');

/**
 * Números de teste documentados (mesma convenção de sandboxes reais, ex. Stripe) — a
 * aprovação NUNCA é decidida por prefixo/padrão do número informado pelo cliente.
 * Fora do modo mock, não existe aprovação simulada: a chamada falha explicitamente
 * até um provedor real ser integrado (ver anti-pattern #14 / playbook #14 da skill).
 */
const MOCK_APPROVED_TEST_CARDS = new Set(['4242424242424242']);

class PaymentGatewayNotConfiguredError extends Error {}

function charge(cardNumber) {
    if (!luhnCheck(cardNumber)) {
        return { status: 'DENIED', reason: 'invalid_card_number' };
    }

    if (settings.paymentGatewayMode !== 'mock') {
        throw new PaymentGatewayNotConfiguredError(
            'Nenhum gateway de pagamento real integrado. Configure PAYMENT_GATEWAY_MODE=mock ' +
            'apenas para desenvolvimento/teste, ou implemente um provedor real antes de aceitar pagamentos.',
        );
    }

    const status = MOCK_APPROVED_TEST_CARDS.has(cardNumber) ? 'PAID' : 'DENIED';
    return { status, reason: status === 'DENIED' ? 'card_not_in_test_set' : undefined };
}

module.exports = { charge, PaymentGatewayNotConfiguredError };
