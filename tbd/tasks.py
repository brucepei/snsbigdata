from __future__ import absolute_import, unicode_literals
from celery import shared_task
from celery.signals import task_postrun
import time

@shared_task(bind=True)
def query_issue_frequency(self, issue_id):
    pass
    
@task_postrun.connect
def done_task(sender=None, task=None, task_id=None, retval=None, **kwargs):
    print('worker {0!r} task {1!s} is done with result: {2}'.format(task.app.Worker, task_id, retval))
