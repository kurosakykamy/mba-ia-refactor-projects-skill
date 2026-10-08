const bcrypt = require('bcryptjs');

const settings = require('../config/settings');
const userModel = require('../models/userModel');
const courseModel = require('../models/courseModel');
const enrollmentModel = require('../models/enrollmentModel');
const paymentModel = require('../models/paymentModel');
const auditLogModel = require('../models/auditLogModel');
const paymentGatewayService = require('./paymentGatewayService');
const cacheService = require('./cacheService');
const { run } = require('../database/db');

class CourseNotFoundError extends Error {}
class PaymentDeniedError extends Error {}

async function checkout({ name, email, password, courseId, cardNumber }) {
    const course = await courseModel.findActiveById(courseId);
    if (!course) throw new CourseNotFoundError('Curso não encontrado');

    const existingUser = await userModel.findByEmail(email);
    let userId;
    if (!existingUser) {
        const passwordHash = await bcrypt.hash(password || '123456', settings.bcryptSaltRounds);
        userId = await userModel.create(name, email, passwordHash);
    } else {
        userId = existingUser.id;
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

    cacheService.set(`last_checkout_${userId}`, course.title);

    return { enrollmentId, userId };
}

module.exports = { checkout, CourseNotFoundError, PaymentDeniedError };
