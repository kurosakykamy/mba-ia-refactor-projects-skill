const express = require('express');

const checkoutController = require('../controllers/checkoutController');
const reportController = require('../controllers/reportController');
const userController = require('../controllers/userController');
const requireAdmin = require('../middlewares/requireAdmin');

const router = express.Router();

router.post('/api/checkout', checkoutController.checkout);
router.get('/api/admin/financial-report', requireAdmin, reportController.financialReport);
router.delete('/api/users/:id', requireAdmin, userController.remove);

module.exports = router;
