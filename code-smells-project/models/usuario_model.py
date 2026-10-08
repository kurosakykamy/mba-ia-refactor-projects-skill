from werkzeug.security import check_password_hash, generate_password_hash

from database import get_db


def _to_dict_publico(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }


def get_todos():
    db = get_db()
    rows = db.execute("SELECT id, nome, email, tipo, criado_em FROM usuarios").fetchall()
    return [_to_dict_publico(row) for row in rows]


def get_por_id(usuario_id):
    db = get_db()
    row = db.execute(
        "SELECT id, nome, email, tipo, criado_em FROM usuarios WHERE id = ?",
        (usuario_id,),
    ).fetchone()
    return _to_dict_publico(row) if row else None


def criar(nome, email, senha, tipo="cliente"):
    db = get_db()
    senha_hash = generate_password_hash(senha)
    cursor = db.execute(
        "INSERT INTO usuarios (nome, email, senha_hash, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, senha_hash, tipo),
    )
    db.commit()
    return cursor.lastrowid


def autenticar(email, senha):
    db = get_db()
    row = db.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
    if row and check_password_hash(row["senha_hash"], senha):
        return {
            "id": row["id"],
            "nome": row["nome"],
            "email": row["email"],
            "tipo": row["tipo"],
        }
    return None
