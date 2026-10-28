const bcrypt = require('bcryptjs');

const settings = require('../config/settings');
const userModel = require('../models/userModel');
const courseModel = require('../models/courseModel');
const enrollmentModel = require('../models/enrollmentModel');
const paymentModel = require('../models/paymentModel');
const auditLogModel = require('../models/auditLogModel');
const paymentGatewayService = require('./paymentGatewayService');
const { run } = require('../database/db');

class CourseNotFoundError extends Error {}
class PaymentDeniedError extends Error {}
class AuthenticationRequiredError extends Error {}

/**
 * Checkout com autenticação OPCIONAL:
 * - e-mail não cadastrado  → cria a conta (compra anônima, fluxo de autoatendimento);
 * - e-mail cadastrado e o chamador É o dono → recompra legítima;
 * - e-mail cadastrado sem token do dono → 401. Sem isso, qualquer anônimo que
 *   soubesse o e-mail da vítima geraria matrícula e pagamento no nome dela.
 */
async function checkout({ name, email, password, courseId, cardNumber, authenticatedUserId }) {
    const course = await courseModel.findActiveById(courseId);
    if (!course) throw new CourseNotFoundError('Curso não encontrado');

    const existingUser = await userModel.findByEmail(email);
    let userId;
    if (!existingUser) {
        // Sem default: criar conta com senha conhecida ('123456') deixaria uma
        // credencial válida e pública para a conta recém-criada.
        const passwordHash = await bcrypt.hash(password, settings.bcryptSaltRounds);
        userId = await userModel.create(name, email, passwordHash);
    } else if (authenticatedUserId && authenticatedUserId === existingUser.id) {
        userId = existingUser.id;
    } else {
        throw new AuthenticationRequiredError(
            'Este e-mail já possui conta. Autentique-se em POST /api/login para comprar com ele.',
        );
    }

    const { status } = paymentGatewayService.charge(cardNumber);
    if (status === 'DENIED') throw new PaymentDeniedError('Pagamento recusado');

    let enrollmentId;
    await run('BEGIN TRANSACTION');
    try {
        enrollmentId = await enrollmentModel.create(userId, courseId);
        await paymentModel.create(enrollmentId, course.price, status);
        await auditLogModel.record(`Checkout curso ${courseId} por ${userId}`);
        await run('COMMIT');
    } catch (err) {
        await run('ROLLBACK');
        throw err;
    }

    return { enrollmentId, userId };
}

module.exports = { checkout, CourseNotFoundError, PaymentDeniedError, AuthenticationRequiredError };
