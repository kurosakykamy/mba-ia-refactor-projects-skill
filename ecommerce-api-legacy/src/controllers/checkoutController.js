const checkoutService = require('../services/checkoutService');

async function checkout(req, res, next) {
    const { usr: name, eml: email, pwd: password, c_id: courseIdRaw, card: cardNumber } = req.body;
    const courseId = Number(courseIdRaw);

    if (!name || !email || !cardNumber || !Number.isInteger(courseId)) {
        return res.status(400).json({ erro: 'Campos obrigatórios: usr, eml, c_id (numérico), card' });
    }

    try {
        const resultado = await checkoutService.checkout({ name, email, password, courseId, cardNumber });
        return res.status(200).json({ msg: 'Sucesso', enrollment_id: resultado.enrollmentId });
    } catch (err) {
        next(err);
    }
}

module.exports = { checkout };
