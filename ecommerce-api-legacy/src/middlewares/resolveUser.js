const authService = require('../services/authService');
const userModel = require('../models/userModel');

/**
 * Autenticação OPCIONAL.
 *
 * Popula `req.currentUser` quando há um token válido e **não rejeita** quando
 * não há. É isso que mantém o checkout público para quem está criando conta,
 * enquanto permite exigir prova de posse para agir sobre uma conta existente.
 */
async function resolveUser(req, res, next) {
    const header = req.headers.authorization || '';
    if (!header.startsWith('Bearer ')) {
        req.currentUser = null;
        return next();
    }

    try {
        const userId = authService.verifyToken(header.slice('Bearer '.length));
        req.currentUser = userId ? await userModel.findById(userId) : null;
        next();
    } catch (err) {
        next(err);
    }
}

module.exports = resolveUser;
