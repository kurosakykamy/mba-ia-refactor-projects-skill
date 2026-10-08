const { run } = require('../database/db');

async function record(action) {
    await run("INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))", [action]);
}

module.exports = { record };
