const authService = require('../services/authService');

async function login(req, res, next) {
    const { eml: email, pwd: password } = req.body;

    if (!email || !password) {
        return res.status(400).json({ erro: 'Campos obrigatórios: eml, pwd' });
    }

    try {
        const resultado = await authService.login(email, password);
        return res.status(200).json(resultado);
    } catch (err) {
        next(err);
    }
}

module.exports = { login };
