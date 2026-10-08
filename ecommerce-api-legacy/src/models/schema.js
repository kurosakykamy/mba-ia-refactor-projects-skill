const bcrypt = require('bcryptjs');

const { run } = require('../database/db');
const settings = require('../config/settings');

async function initSchema() {
    await run(`CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        pass TEXT NOT NULL
    )`);
    await run(`CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        price REAL NOT NULL,
        active INTEGER DEFAULT 1
    )`);
    await run(`CREATE TABLE IF NOT EXISTS enrollments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        course_id INTEGER NOT NULL REFERENCES courses(id)
    )`);
    await run(`CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        enrollment_id INTEGER NOT NULL REFERENCES enrollments(id) ON DELETE CASCADE,
        amount REAL NOT NULL,
        status TEXT NOT NULL
    )`);
    await run(`CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )`);
}

async function seed() {
    const passwordHash = await bcrypt.hash('123', settings.bcryptSaltRounds);
    const { lastID: userId } = await run(
        'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
        ['Leonan', 'leonan@fullcycle.com.br', passwordHash],
    );

    const { lastID: cleanArchId } = await run(
        'INSERT INTO courses (title, price, active) VALUES (?, ?, 1)',
        ['Clean Architecture', 997.0],
    );
    await run('INSERT INTO courses (title, price, active) VALUES (?, ?, 1)', ['Docker', 497.0]);

    const { lastID: enrollmentId } = await run(
        'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
        [userId, cleanArchId],
    );
    await run(
        'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
        [enrollmentId, 997.0, 'PAID'],
    );
}

module.exports = { initSchema, seed };
