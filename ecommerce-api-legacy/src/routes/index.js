const express = require('express');

const authController = require('../controllers/authController');
const checkoutController = require('../controllers/checkoutController');
const reportController = require('../controllers/reportController');
const userController = require('../controllers/userController');
const requireAdmin = require('../middlewares/requireAdmin');
const resolveUser = require('../middlewares/resolveUser');

const router = express.Router();

router.post('/api/login', authController.login);
// `resolveUser` é auth OPCIONAL: mantém o checkout público para quem cria conta,
// mas identifica o chamador quando há token (necessário para recompra).
router.post('/api/checkout', resolveUser, checkoutController.checkout);
router.get('/api/admin/financial-report', requireAdmin, reportController.financialReport);
router.delete('/api/users/:id', requireAdmin, userController.remove);

module.exports = router;
