const nodeEnv = process.env.NODE_ENV || 'development';

/**
 * Fail-closed: fora de desenvolvimento, segredo ausente impede o boot.
 *
 * Um fallback silencioso faria a aplicação subir com o valor que está
 * commitado no repositório — exatamente o problema que extrair para
 * variável de ambiente deveria resolver. Como `adminToken` é a única
 * autenticação da API, um default público daria acesso às rotas
 * administrativas a qualquer leitor do repositório.
 */
function requiredSecret(name, devDefault) {
    const value = process.env[name];
    if (value) return value;
    if (nodeEnv !== 'development') {
        throw new Error(
            `${name} é obrigatório quando NODE_ENV=${nodeEnv}. ` +
            'Defina a variável de ambiente antes de subir a aplicação.',
        );
    }
    return devDefault;
}

const settings = {
    port: parseInt(process.env.PORT || '3000', 10),
    nodeEnv,
    paymentGatewayMode: process.env.PAYMENT_GATEWAY_MODE || 'mock',
    adminToken: requiredSecret('ADMIN_TOKEN', 'dev-admin-token-change-me'),
    authTokenSecret: requiredSecret('AUTH_TOKEN_SECRET', 'dev-only-auth-secret-change-me'),
    authTokenExpiresIn: process.env.AUTH_TOKEN_EXPIRES_IN || '24h',
    bcryptSaltRounds: parseInt(process.env.BCRYPT_SALT_ROUNDS || '10', 10),
};

if (settings.nodeEnv === 'production' && settings.paymentGatewayMode === 'mock') {
    throw new Error(
        'Configuração insegura: PAYMENT_GATEWAY_MODE=mock não é permitido quando NODE_ENV=production. ' +
        'Configure um provedor de pagamento real (ex.: Stripe/Pagar.me) antes de subir em produção.',
    );
}

module.exports = settings;
