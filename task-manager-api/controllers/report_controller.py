from datetime import timedelta

from sqlalchemy import func

from database import db
from models.category import Category
from models.task import Task
from models.user import User
from utils.helpers import calculate_percentage, utcnow_naive

PRIORITY_LABELS = {1: 'critical', 2: 'high', 3: 'medium', 4: 'low', 5: 'minimal'}


def _user_task_stats():
    rows = (
        db.session.query(
            Task.user_id,
            func.count(Task.id),
            func.sum(db.case((Task.status == 'done', 1), else_=0)),
        )
        .group_by(Task.user_id)
        .all()
    )
    return {user_id: (total, completed or 0) for user_id, total, completed in rows}


def summary_report():
    total_tasks = Task.query.count()
    total_users = User.query.count()
    total_categories = Category.query.count()

    status_counts = {
        status: Task.query.filter_by(status=status).count()
        for status in ('pending', 'in_progress', 'done', 'cancelled')
    }
    priority_counts = {
        label: Task.query.filter_by(priority=p).count()
        for p, label in PRIORITY_LABELS.items()
    }

    overdue_tasks = [t for t in Task.query.all() if t.is_overdue()]
    overdue_list = [
        {
            'id': t.id,
            'title': t.title,
            'due_date': str(t.due_date),
            'days_overdue': (utcnow_naive() - t.due_date).days,
        }
        for t in overdue_tasks
    ]

    seven_days_ago = utcnow_naive() - timedelta(days=7)
    recent_tasks = Task.query.filter(Task.created_at >= seven_days_ago).count()
    recent_done = Task.query.filter(
        Task.status == 'done', Task.updated_at >= seven_days_ago
    ).count()

    stats_by_user = _user_task_stats()
    user_stats = []
    for user in User.query.all():
        total, completed = stats_by_user.get(user.id, (0, 0))
        user_stats.append({
            'user_id': user.id,
            'user_name': user.name,
            'total_tasks': total,
            'completed_tasks': completed,
            'completion_rate': calculate_percentage(completed, total),
        })

    return {
        'generated_at': str(utcnow_naive()),
        'overview': {
            'total_tasks': total_tasks,
            'total_users': total_users,
            'total_categories': total_categories,
        },
        'tasks_by_status': status_counts,
        'tasks_by_priority': priority_counts,
        'overdue': {'count': len(overdue_list), 'tasks': overdue_list},
        'recent_activity': {
            'tasks_created_last_7_days': recent_tasks,
            'tasks_completed_last_7_days': recent_done,
        },
        'user_productivity': user_stats,
    }


def user_report(user_id):
    user = User.query.get(user_id)
    if not user:
        return None

    tasks = Task.query.filter_by(user_id=user_id).all()
    total = len(tasks)
    done = sum(1 for t in tasks if t.status == 'done')
    pending = sum(1 for t in tasks if t.status == 'pending')
    in_progress = sum(1 for t in tasks if t.status == 'in_progress')
    cancelled = sum(1 for t in tasks if t.status == 'cancelled')
    high_priority = sum(1 for t in tasks if t.priority <= 2)
    overdue = sum(1 for t in tasks if t.is_overdue())

    return {
        'user': {'id': user.id, 'name': user.name, 'email': user.email},
        'statistics': {
            'total_tasks': total,
            'done': done,
            'pending': pending,
            'in_progress': in_progress,
            'cancelled': cancelled,
            'overdue': overdue,
            'high_priority': high_priority,
            'completion_rate': calculate_percentage(done, total),
        },
    }
