const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');

const settings = require('../config/settings');
const userModel = require('../models/userModel');

class InvalidCredentialsError extends Error {}

/** Token assinado (HS256) com expiração — nunca um identificador em texto puro. */
function generateToken(user) {
    return jwt.sign({ sub: user.id }, settings.authTokenSecret, {
        expiresIn: settings.authTokenExpiresIn,
    });
}

/** Retorna o id do usuário se o token for válido e não expirado; null caso contrário. */
function verifyToken(token) {
    try {
        const payload = jwt.verify(token, settings.authTokenSecret);
        return payload.sub;
    } catch {
        return null;
    }
}

async function login(email, password) {
    const user = await userModel.findByEmail(email);
    // Mesma resposta para usuário inexistente e senha errada: não serve de
    // oráculo para descobrir quais e-mails estão cadastrados.
    if (!user || !(await bcrypt.compare(password, user.pass))) {
        throw new InvalidCredentialsError('Credenciais inválidas');
    }
    return { token: generateToken(user), user: userModel.toPublic(user) };
}

module.exports = { generateToken, verifyToken, login, InvalidCredentialsError };
