import logging
import smtplib

from config.settings import Settings
from utils.helpers import utcnow_naive

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self):
        self.notifications = []

    def send_email(self, to, subject, body):
        try:
            server = smtplib.SMTP(Settings.SMTP_HOST, Settings.SMTP_PORT, timeout=3)
            server.starttls()
            server.login(Settings.SMTP_USER, Settings.SMTP_PASSWORD)
            message = f"Subject: {subject}\n\n{body}"
            server.sendmail(Settings.SMTP_USER, to, message)
            server.quit()
            logger.info('email.enviado destinatario=%s', to)
            return True
        except Exception:
            logger.exception('email.falhou destinatario=%s', to)
            return False

    def notify_task_assigned(self, user, task):
        subject = f"Nova task atribuída: {task.title}"
        body = (
            f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n\n"
            f"Prioridade: {task.priority}\nStatus: {task.status}"
        )
        self.send_email(user.email, subject, body)
        self.notifications.append({
            'type': 'task_assigned',
            'user_id': user.id,
            'task_id': task.id,
            'timestamp': utcnow_naive(),
        })

    def notify_task_overdue(self, user, task):
        subject = f"Task atrasada: {task.title}"
        body = f"Olá {user.name},\n\nA task '{task.title}' está atrasada!\n\nData limite: {task.due_date}"
        self.send_email(user.email, subject, body)

    def get_notifications(self, user_id):
        return [n for n in self.notifications if n['user_id'] == user_id]
