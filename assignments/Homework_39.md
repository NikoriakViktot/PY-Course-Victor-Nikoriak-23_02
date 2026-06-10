### 📂 Структура проєкту

Plaintext

```
🗂️ project/
│
├── 📂 static/
│   └── 📄 style.css
│
├── 📂 templates/
└── 📄 index.html

```

### 1. 📄 HTML-сторінка (`templates/index.html`)

Головна сторінка, яка приймає масив нотаток і динамічно виводить їх на екран. Спочатку підключаємо CSS із папки `static`.

HTML

```
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Мої Нотатки</title>
    <link rel="stylesheet" href="../static/style.css">
</head>
<body>

    <header>
        <h1>📝 Додаток для нотаток</h1>
    </header>

    <main class="container">
        <div class="notes-grid">
            
            <div class="note-card">
                <h3 class="note-title">Купити продукти</h3>
                <p class="note-text">Молоко, хліб, кава, куряче філе та овочі на вечерю.</p>
                <span class="note-date">10.06.2026</span>
            </div>

            <div class="note-card">
                <h3 class="note-title">Проєкт на Arch Linux</h3>
                <p class="note-text">Налаштувати резервне копіювання конфігів та оновити пакети в системі.</p>
                <span class="note-date">09.06.2026</span>
            </div>

            <div class="note-card">
                <h3 class="note-title">Тренування</h3>
                <p class="note-text">Комплекс вправ із гумовими петлями (YTW та розведення на грудні м'язи).</p>
                <span class="note-date">08.06.2026</span>
            </div>

        </div>
        </main>

</body>
</html>
```

### 2. 📄 Стилі CSS (`static/style.css`)

Прості сучасні стилі з використанням Grid Layout, щоб нотатки красиво розміщувалися на екрані (адаптивно під мобільні та ПК).

CSS

```
/* Базові налаштування */
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background-color: #f4f6f9;
    color: #333;
    margin: 0;
    padding: 0;
}

header {
    background-color: #2c3e50;
    color: #fff;
    padding: 20px;
    text-align: center;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

.container {
    max-width: 1200px;
    margin: 30px auto;
    padding: 0 20px;
}

/* Сітка для нотаток */
.notes-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 20px;
}

/* Карточка нотатки */
.note-card {
    background: #fff;
    border-left: 5px solid #3498db;
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.note-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
}

.note-title {
    margin-top: 0;
    margin-bottom: 10px;
    color: #2c3e50;
    font-size: 1.2rem;
}

.note-text {
    color: #555;
    font-size: 0.95rem;
    line-height: 1.5;
    margin-bottom: 15px;
}

.note-date {
    display: block;
    font-size: 0.8rem;
    color: #999;
    text-align: right;
}
```
