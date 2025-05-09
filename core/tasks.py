from celery import shared_task
from core.processing import process_excel_data
from core.utils import DatabaseLogger

@shared_task(bind=True)
def process_excel_file_task(self, file_path):
    """
    Celery task to process Excel file in the background
    """
    task_id = self.request.id
    DatabaseLogger.log(
        level="INFO",
        message=f"Starting background processing of file: {file_path}",
        task_name=f"celery-task-{task_id}"
    )
    
    try:
        result = process_excel_data(file_path)
        return result
    except Exception as e:
        DatabaseLogger.log(
            level="ERROR",
            message=f"Background task failed for file: {file_path}",
            task_name=f"celery-task-{task_id}",
            error=e
        )
        raise