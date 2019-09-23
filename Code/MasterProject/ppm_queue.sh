sudo systemctl start redis
celery worker -A MasterProject -Q PaperManagerQueue --concurrency=4 --loglevel=debug