"""
app/config/__init__.py — Публічний API пакету конфігурації.

Реекспортує об'єкт config, щоб інші модулі могли імпортувати коротко:
    from app.config import config   ← з цього __init__.py

замість довгого:
    from app.config.settings import config   ← напряму з файлу

__all__ визначає що буде доступно при:
    from app.config import *
"""
from .settings import config  # реекспорт singleton конфігурації

# __all__ — явний список публічного API цього пакету
__all__ = ["config"]
