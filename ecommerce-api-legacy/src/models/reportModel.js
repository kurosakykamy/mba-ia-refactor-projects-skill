const { all } = require('../database/db');

/** Uma única query com JOIN — substitui o N+1 (N×M+1) original. */
async function fetchFinancialRows() {
    return all(`
        SELECT c.id AS course_id, c.title AS course_title,
               e.id AS enrollment_id, u.name AS student_name,
               p.amount AS amount, p.status AS status
        FROM courses c
        LEFT JOIN enrollments e ON e.course_id = c.id
        LEFT JOIN users u ON u.id = e.user_id
        LEFT JOIN payments p ON p.enrollment_id = e.id
    `);
}

module.exports = { fetchFinancialRows };
