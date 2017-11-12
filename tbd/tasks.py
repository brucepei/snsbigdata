from __future__ import absolute_import, unicode_literals
from celery import shared_task
import time

@shared_task
def add(x, y):
    for i in range(3):
        print("cbd do job for {}".format(i))
        time.sleep(1)
    return x + y