const settings = {
    port: parseInt(process.env.PORT || '3000', 10),
    nodeEnv: process.env.NODE_ENV || 'development',
    paymentGatewayMode: process.env.PAYMENT_GATEWAY_MODE || 'mock',
    dbUser: process.env.DB_USER || 'dev_user',
    dbPass: process.env.DB_PASS || 'dev_pass_change_me',
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || 'pk_test_dev_key_change_me',
    smtpUser: process.env.SMTP_USER || 'no-reply@example.com',
    adminToken: process.env.ADMIN_TOKEN || 'dev-admin-token-change-me',
    bcryptSaltRounds: parseInt(process.env.BCRYPT_SALT_ROUNDS || '10', 10),
};

if (settings.nodeEnv === 'production' && settings.paymentGatewayMode === 'mock') {
    throw new Error(
        'Configuração insegura: PAYMENT_GATEWAY_MODE=mock não é permitido quando NODE_ENV=production. ' +
        'Configure um provedor de pagamento real (ex.: Stripe/Pagar.me) antes de subir em produção.',
    );
}

module.exports = settings;
