from django.db import models


class Note(models.Model):
    """
    Модель = Python-клас що описує таблицю в базі даних.

    Django ORM автоматично:
        - створює таблицю 'hello_app_note' в db.sqlite3
        - генерує поле id (PRIMARY KEY AUTOINCREMENT) автоматично
        - дає API: Note.objects.all(), Note.objects.create(...) тощо
    """

    # CharField → VARCHAR в SQL, обмежена довжина рядка
    title = models.CharField(
        max_length=200,          # максимум 200 символів
        verbose_name='Заголовок' # назва поля в адмін-панелі
    )

    # TextField → TEXT в SQL, необмежений текст
    content = models.TextField(
        blank=True,              # поле необов'язкове у формі
        verbose_name='Текст'
    )

    # DateTimeField з auto_now_add=True → TIMESTAMP
    # автоматично записує час створення запису
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Створено'
    )

    def __str__(self):
        # Це рядкове представлення об'єкта.
        # Відображається в адмін-панелі замість "Note object (1)"
        return self.title

    class Meta:
        verbose_name = 'Нотатка'
        verbose_name_plural = 'Нотатки'
        ordering = ['-created_at']  # нові нотатки — першими