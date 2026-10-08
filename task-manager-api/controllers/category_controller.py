from sqlalchemy import func

from database import db
from models.category import Category
from models.task import Task
from utils.helpers import is_valid_color


def list_categories():
    counts = dict(
        db.session.query(Task.category_id, func.count(Task.id)).group_by(Task.category_id).all()
    )
    result = []
    for category in Category.query.all():
        data = category.to_dict()
        data['task_count'] = counts.get(category.id, 0)
        result.append(data)
    return result


def create_category(data):
    name = data.get('name')
    if not name:
        return None, 'Nome é obrigatório', 400

    color = data.get('color', '#000000')
    if not is_valid_color(color):
        return None, 'Cor inválida. Use o formato #RRGGBB', 400

    category = Category(name=name, description=data.get('description', ''), color=color)
    db.session.add(category)
    db.session.commit()
    return category.to_dict(), None, 201


def update_category(cat_id, data):
    category = Category.query.get(cat_id)
    if not category:
        return None, 'Categoria não encontrada', 404

    if 'name' in data:
        category.name = data['name']
    if 'description' in data:
        category.description = data['description']
    if 'color' in data:
        if not is_valid_color(data['color']):
            return None, 'Cor inválida. Use o formato #RRGGBB', 400
        category.color = data['color']

    db.session.commit()
    return category.to_dict(), None, 200


def delete_category(cat_id):
    category = Category.query.get(cat_id)
    if not category:
        return False
    db.session.delete(category)
    db.session.commit()
    return True
