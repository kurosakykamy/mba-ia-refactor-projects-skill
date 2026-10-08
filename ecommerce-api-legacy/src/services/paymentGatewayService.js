/**
 * Mock de gateway de pagamento para fins de teste/desenvolvimento.
 * Substituir por uma integração real (Stripe/Pagar.me/etc.) antes de produção.
 * Nunca logar o número do cartão nem a chave do gateway (ver middlewares/errorHandler.js
 * e services/checkoutService.js — nenhum dos dois imprime esses valores).
 */
function charge(cardNumber) {
    const status = cardNumber.startsWith('4') ? 'PAID' : 'DENIED';
    return { status };
}

module.exports = { charge };
