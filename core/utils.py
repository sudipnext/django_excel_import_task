import traceback
from core.models import Logs

class DatabaseLogger:
    @staticmethod
    def log(level, message, task_name, error=None):
        traceback_text = None
        if error:
            traceback_text = ''.join(traceback.format_exception(type(error), error, error.__traceback__))

        Logs.objects.create(
            level=level,
            message=message,
            task_name=task_name,
            traceback=traceback_text
        )

    @staticmethod
    def get_logs():
        return Logs.objects.all()
