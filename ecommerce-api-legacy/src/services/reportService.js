const reportModel = require('../models/reportModel');

async function getFinancialReport() {
    const rows = await reportModel.fetchFinancialRows();
    const byCourse = new Map();

    for (const row of rows) {
        if (!byCourse.has(row.course_id)) {
            byCourse.set(row.course_id, { course: row.course_title, revenue: 0, students: [] });
        }
        const entry = byCourse.get(row.course_id);
        if (row.enrollment_id) {
            if (row.status === 'PAID') {
                entry.revenue += row.amount;
            }
            entry.students.push({ student: row.student_name || 'Unknown', paid: row.amount || 0 });
        }
    }

    return Array.from(byCourse.values());
}

module.exports = { getFinancialReport };
