from datetime import datetime
import django_rq
from video_flix_app.api.tasks import export_userwatchhistory_task


def register_watchhistory_export_job():
    """
    Register a periodic job that exports all UserWatchHistory records to S3.
    The job is scheduled to run every hour (interval in seconds).
    If the job already exists, it will not be registered again.
    """
    scheduler = django_rq.get_scheduler('default')
    for job in scheduler.get_jobs():
        if job.func_name == export_userwatchhistory_task.__qualname__:
            return
    scheduler.schedule(
        scheduled_time=datetime.utcnow(),  # Start immediately
        func=export_userwatchhistory_task,
        interval=1,  # every hour
        repeat=None,
        result_ttl=600
    )
