const { run, get } = require('../database/db');

function toPublic(row) {
    if (!row) return null;
    return { id: row.id, name: row.name, email: row.email };
}

async function findByEmail(email) {
    return get('SELECT * FROM users WHERE email = ?', [email]);
}

async function create(name, email, passwordHash) {
    const { lastID } = await run(
        'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
        [name, email, passwordHash],
    );
    return lastID;
}

async function remove(id) {
    const { changes } = await run('DELETE FROM users WHERE id = ?', [id]);
    return changes > 0;
}

module.exports = { findByEmail, create, remove, toPublic };
