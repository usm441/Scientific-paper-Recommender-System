from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MasterProject.settings')

app = Celery('MasterProject', include=['PaperManager.celery_tasks'])

# Using a string here means the worker don't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
# This is not required, but as you can have more than one app
# with tasks it’s better to do the autoload than declaring all tasks
# in this same file.
app.autodiscover_tasks()


# if we ever need periodic task then uncomment this code
# app.conf.beat_schedule = {
#     'add-every-10-seconds': {
#         'task': 'PaperManager.tasks.periodic_task',
#         'schedule': 10.0,
#         'args': ()
#     },
# }