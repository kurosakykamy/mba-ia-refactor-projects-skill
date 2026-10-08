const sqlite3 = require('sqlite3').verbose();

const db = new sqlite3.Database(':memory:');
db.run('PRAGMA foreign_keys = ON');

function run(sql, params = []) {
    return new Promise((resolve, reject) => {
        db.run(sql, params, function callback(err) {
            if (err) return reject(err);
            resolve({ lastID: this.lastID, changes: this.changes });
        });
    });
}

function get(sql, params = []) {
    return new Promise((resolve, reject) => {
        db.get(sql, params, (err, row) => {
            if (err) return reject(err);
            resolve(row);
        });
    });
}

function all(sql, params = []) {
    return new Promise((resolve, reject) => {
        db.all(sql, params, (err, rows) => {
            if (err) return reject(err);
            resolve(rows);
        });
    });
}

module.exports = { run, get, all };
