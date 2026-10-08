const { run } = require('../database/db');

async function create(userId, courseId) {
    const { lastID } = await run(
        'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
        [userId, courseId],
    );
    return lastID;
}

module.exports = { create };
