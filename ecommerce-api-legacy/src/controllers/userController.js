const userModel = require('../models/userModel');

async function remove(req, res, next) {
    const id = Number(req.params.id);
    if (!Number.isInteger(id)) {
        return res.status(400).json({ erro: 'id inválido' });
    }

    try {
        const removed = await userModel.remove(id);
        if (!removed) {
            return res.status(404).json({ erro: 'Usuário não encontrado' });
        }
        res.json({ msg: 'Usuário removido (matrículas e pagamentos associados são removidos em cascata pelo banco)' });
    } catch (err) {
        next(err);
    }
}

module.exports = { remove };
