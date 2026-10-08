const { CourseNotFoundError, PaymentDeniedError } = require('../services/checkoutService');

function errorHandler(err, req, res, next) { // eslint-disable-line no-unused-vars
    if (err instanceof CourseNotFoundError) {
        return res.status(404).json({ erro: err.message });
    }
    if (err instanceof PaymentDeniedError) {
        return res.status(400).json({ erro: err.message });
    }
    console.error(err);
    return res.status(500).json({ erro: 'Erro interno do servidor' });
}

module.exports = errorHandler;
