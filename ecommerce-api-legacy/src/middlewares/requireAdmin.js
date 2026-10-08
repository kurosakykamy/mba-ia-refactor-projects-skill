const settings = require('../config/settings');

function requireAdmin(req, res, next) {
    const token = req.headers['x-admin-token'];
    if (!token || token !== settings.adminToken) {
        return res.status(401).json({ erro: 'unauthorized' });
    }
    next();
}

module.exports = requireAdmin;
