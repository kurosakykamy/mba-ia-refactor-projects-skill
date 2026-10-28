const checkoutService = require('../services/checkoutService');

async function checkout(req, res, next) {
    const { usr: name, eml: email, pwd: password, c_id: courseIdRaw, card: cardNumber } = req.body;
    const courseId = Number(courseIdRaw);
    const authenticatedUserId = req.currentUser ? req.currentUser.id : null;

    if (!name || !email || !cardNumber || !Number.isInteger(courseId)) {
        return res.status(400).json({ erro: 'Campos obrigatórios: usr, eml, c_id (numérico), card' });
    }
    // A senha só é necessária para criar conta nova; quem já está autenticado
    // não precisa reenviá-la para recomprar.
    if (!authenticatedUserId && !password) {
        return res.status(400).json({ erro: 'Campo obrigatório: pwd (ou autentique-se em POST /api/login)' });
    }

    try {
        const resultado = await checkoutService.checkout({
            name, email, password, courseId, cardNumber, authenticatedUserId,
        });
        return res.status(200).json({ msg: 'Sucesso', enrollment_id: resultado.enrollmentId });
    } catch (err) {
        next(err);
    }
}

module.exports = { checkout };
