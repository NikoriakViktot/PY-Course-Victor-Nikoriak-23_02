import os
from celery import Celery
# Встановлюємо дефолтні налаштування Django для celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
app = Celery('myproject')
# Налаштування будуть зчитуватися з settings.py з префіксом CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')
# Автоматично шукаємо завдання в файлах tasks.py додатків
app.autodiscover_tasks()