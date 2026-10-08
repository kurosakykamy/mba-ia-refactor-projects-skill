const settings = {
    port: parseInt(process.env.PORT || '3000', 10),
    dbUser: process.env.DB_USER || 'dev_user',
    dbPass: process.env.DB_PASS || 'dev_pass_change_me',
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || 'pk_test_dev_key_change_me',
    smtpUser: process.env.SMTP_USER || 'no-reply@example.com',
    adminToken: process.env.ADMIN_TOKEN || 'dev-admin-token-change-me',
    bcryptSaltRounds: parseInt(process.env.BCRYPT_SALT_ROUNDS || '10', 10),
};

module.exports = settings;
