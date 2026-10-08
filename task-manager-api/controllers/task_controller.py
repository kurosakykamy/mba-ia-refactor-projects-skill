from sqlalchemy.orm import joinedload

from database import db
from models.category import Category
from models.task import Task
from models.user import User
from services.notification_service import NotificationService
from utils.helpers import process_task_data

notification_service = NotificationService()


def list_tasks():
    tasks = Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()
    result = []
    for task in tasks:
        data = task.to_dict()
        data['user_name'] = task.user.name if task.user else None
        data['category_name'] = task.category.name if task.category else None
        result.append(data)
    return result


def get_task(task_id):
    task = Task.query.get(task_id)
    return task.to_dict() if task else None


def create_task(data):
    if not data.get('title'):
        return None, 'Título é obrigatório', 400

    result, error = process_task_data(data)
    if error:
        return None, error, 400

    user_id = data.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        if not user:
            return None, 'Usuário não encontrado', 404

    category_id = data.get('category_id')
    if category_id:
        category = Category.query.get(category_id)
        if not category:
            return None, 'Categoria não encontrada', 404

    task = Task(
        title=result['title'],
        description=result.get('description', ''),
        status=result.get('status', 'pending'),
        priority=result.get('priority', 3),
        user_id=user_id,
        category_id=category_id,
        due_date=result.get('due_date'),
        tags=result.get('tags'),
    )

    db.session.add(task)
    db.session.commit()

    if task.user:
        notification_service.notify_task_assigned(task.user, task)

    return task.to_dict(), None, 201


def update_task(task_id, data):
    task = Task.query.get(task_id)
    if not task:
        return None, 'Task não encontrada', 404

    result, error = process_task_data(data)
    if error:
        return None, error, 400

    for field in ('title', 'description', 'status', 'priority', 'due_date', 'tags'):
        if field in result:
            setattr(task, field, result[field])

    if 'user_id' in data:
        if data['user_id']:
            user = User.query.get(data['user_id'])
            if not user:
                return None, 'Usuário não encontrado', 404
        task.user_id = data['user_id']

    if 'category_id' in data:
        if data['category_id']:
            category = Category.query.get(data['category_id'])
            if not category:
                return None, 'Categoria não encontrada', 404
        task.category_id = data['category_id']

    db.session.commit()
    return task.to_dict(), None, 200


def delete_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return False
    db.session.delete(task)
    db.session.commit()
    return True


def search_tasks(query, status, priority, user_id):
    tasks = Task.query

    if query:
        tasks = tasks.filter(
            db.or_(Task.title.like(f'%{query}%'), Task.description.like(f'%{query}%'))
        )
    if status:
        tasks = tasks.filter(Task.status == status)
    if priority is not None:
        tasks = tasks.filter(Task.priority == priority)
    if user_id is not None:
        tasks = tasks.filter(Task.user_id == user_id)

    return [t.to_dict() for t in tasks.all()]


def task_stats():
    total = Task.query.count()
    pending = Task.query.filter_by(status='pending').count()
    in_progress = Task.query.filter_by(status='in_progress').count()
    done = Task.query.filter_by(status='done').count()
    cancelled = Task.query.filter_by(status='cancelled').count()
    overdue = sum(1 for t in Task.query.all() if t.is_overdue())

    return {
        'total': total,
        'pending': pending,
        'in_progress': in_progress,
        'done': done,
        'cancelled': cancelled,
        'overdue': overdue,
        'completion_rate': round((done / total) * 100, 2) if total > 0 else 0,
    }
