from datetime import datetime, timezone


def health():
    return {'status': 'ok', 'timestamp': str(datetime.now(timezone.utc))}


def index():
    return {'message': 'Task Manager API', 'version': '1.0'}
