# CV Maker: генератор CV з HTML у PDF

Цей проєкт — простий Python-інструмент для створення професійного CV/резюме у форматі PDF на основі HTML-шаблону.

Головна ідея:

```text
HTML-шаблон → Python-скрипт → PDF-документ
```

Ти редагуєш своє CV як звичайний HTML-файл, запускаєш Python-скрипт і отримуєш готовий PDF.

---

## 1. Що робить цей проєкт

Проєкт перетворює HTML-файл з CV у PDF-документ.

Його можна використовувати, якщо потрібно:

- створити професійне CV зі своїм дизайном;
- зберігати CV у Git / GitHub;
- редагувати CV як звичайний HTML-документ;
- швидко генерувати PDF після кожного оновлення;
- створювати різні версії CV під різні вакансії;
- у майбутньому використати той самий HTML для персонального сайту, портфоліо, Django-шаблону або Streamlit-додатку.

Замість того щоб вручну оформлювати CV у Word, Canva чи Google Docs, цей підхід робить CV маленьким відтворюваним пайплайном.

---

## 2. Як це працює на високому рівні

Проєкт використовує два основні компоненти:

### `pdfkit`

`pdfkit` — це Python-бібліотека, яка дозволяє з Python-коду викликати зовнішній інструмент для перетворення HTML у PDF.

### `wkhtmltopdf`

`wkhtmltopdf` — це окрема консольна програма, яка рендерить HTML-сторінку і зберігає її як PDF.

Повний ланцюжок виглядає так:

```text
cv_viktor_nikoriak.html
        ↓
generate_cv_pdf.py
        ↓
pdfkit
        ↓
wkhtmltopdf
        ↓
CV_Viktor_Nikoriak_GeoAI.pdf
```

Інакше кажучи:

- HTML відповідає за зміст і вигляд CV.
- Python відповідає за автоматизацію.
- `pdfkit` з'єднує Python із `wkhtmltopdf`.
- `wkhtmltopdf` створює фінальний PDF-файл.

---

## 3. Структура проєкту

Рекомендована структура:

```text
CV_maker/
│
├── cv_viktor_nikoriak.html
├── generate_cv_pdf.py
├── README.md
└── CV_Viktor_Nikoriak_GeoAI.pdf
```

### Призначення файлів

| Файл | Призначення |
|---|---|
| `cv_viktor_nikoriak.html` | Основний HTML-шаблон CV |
| `generate_cv_pdf.py` | Python-скрипт для генерації PDF |
| `README.md` | Інструкція для користувачів |
| `CV_Viktor_Nikoriak_GeoAI.pdf` | Згенерований PDF-файл |

PDF-файл створюється автоматично після запуску скрипта. Його не потрібно створювати вручну.

---

## 4. Що потрібно встановити

Для роботи проєкту потрібно:

- Python 3.10 або новіший;
- віртуальне середовище Python;
- Python-бібліотека `pdfkit`;
- системна програма `wkhtmltopdf`.

Рекомендовано також мати:

- PyCharm, VS Code або інший редактор коду;
- Git для контролю версій;
- браузер для попереднього перегляду HTML-файлу.

---

## 5. Встановлення на Windows

### Крок 1. Завантажити або склонувати проєкт

Якщо проєкт розміщений на GitHub:

```powershell
git clone <repository-url>
cd CV_maker
```

Або можна просто завантажити папку проєкту й відкрити її у PyCharm або VS Code.

---

### Крок 2. Створити віртуальне середовище

У папці проєкту виконай:

```powershell
python -m venv .venv
```

Активуй середовище:

```powershell
.\.venv\Scripts\Activate.ps1
```

Після активації в терміналі має з'явитися приблизно таке:

```text
(.venv) PS C:\Users\YourName\...\CV_maker>
```

---

### Крок 3. Встановити Python-залежності

```powershell
pip install pdfkit
```

Також можна створити файл `requirements.txt`:

```text
pdfkit
```

І встановлювати залежності так:

```powershell
pip install -r requirements.txt
```

---

### Крок 4. Встановити wkhtmltopdf

Потрібно окремо встановити програму `wkhtmltopdf` для Windows.
https://wkhtmltopdf.org/downloads.html

Для більшості сучасних Windows-систем потрібно обрати:

```text
Windows Installer 64-bit
```

Після встановлення програма зазвичай знаходиться тут:

```text
C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe
```

---

### Крок 5. Перевірити встановлення wkhtmltopdf

У PowerShell виконай:

```powershell
where wkhtmltopdf
```

або:

```powershell
wkhtmltopdf --version
```

Очікуваний результат:

```text
C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe
```

або версія програми, наприклад:

```text
wkhtmltopdf 0.12.6
```

---

## 6. Встановлення на macOS

Встанови Python-залежності:

```bash
pip install pdfkit
```

Встанови `wkhtmltopdf` через Homebrew:

```bash
brew install wkhtmltopdf
```

Перевір встановлення:

```bash
which wkhtmltopdf
wkhtmltopdf --version
```

---

## 7. Встановлення на Linux / Ubuntu

Встанови Python-залежності:

```bash
pip install pdfkit
```

Встанови `wkhtmltopdf`:

```bash
sudo apt update
sudo apt install wkhtmltopdf
```

Перевір встановлення:

```bash
which wkhtmltopdf
wkhtmltopdf --version
```

---

## 8. Базове використання

Запусти скрипт:

```bash
python generate_cv_pdf.py
```

На Windows можна також запустити через Python із віртуального середовища:

```powershell
.\.venv\Scripts\python.exe generate_cv_pdf.py
```

Після успішного запуску в папці проєкту з'явиться PDF:

```text
CV_Viktor_Nikoriak_GeoAI.pdf
```

---

## 9. Рекомендований Python-скрипт

Створи файл:

```text
generate_cv_pdf.py
```

Приклад:

```python
from pathlib import Path
import shutil
import pdfkit


BASE_DIR = Path(__file__).resolve().parent

HTML_FILE = BASE_DIR / "cv_viktor_nikoriak_GeoAI.html"
OUTPUT_PDF = BASE_DIR / "CV_Viktor_Nikoriak_GeoAI.pdf"


def find_wkhtmltopdf() -> str:
    from_path = shutil.which("wkhtmltopdf")

    if from_path:
        return from_path

    possible_paths = [
        r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe",
        r"C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe",
    ]

    for path in possible_paths:
        if Path(path).exists():
            return path

    raise FileNotFoundError(
        "Не знайдено wkhtmltopdf. "
        "Встанови wkhtmltopdf або вручну вкажи шлях до wkhtmltopdf.exe."
    )


def main() -> None:
    wkhtmltopdf_path = find_wkhtmltopdf()

    config = pdfkit.configuration(
        wkhtmltopdf=wkhtmltopdf_path
    )

    options = {
        "encoding": "UTF-8",
        "page-size": "A4",
        "orientation": "Portrait",
        "margin-top": "15mm",
        "margin-right": "15mm",
        "margin-bottom": "15mm",
        "margin-left": "15mm",
        "enable-local-file-access": None,
        "print-media-type": None,
    }

    pdfkit.from_file(
        str(HTML_FILE),
        str(OUTPUT_PDF),
        configuration=config,
        options=options,
    )

    print(f"PDF створено: {OUTPUT_PDF}")


if __name__ == "__main__":
    main()
```

Цей варіант спочатку шукає `wkhtmltopdf` у системному PATH, а потім перевіряє типові папки встановлення на Windows.

---

## 10. Як редагувати CV

Відкрий файл:

```text
cv_viktor_nikoriak.html
```

У ньому є дві головні частини:

```html
<style>
    CSS-стилі
</style>
```

і:

```html
<body>
    Зміст CV
</body>
```

### Редагування персональної інформації

На початку HTML-файлу знайди блок:

```html
<h1>Viktor Nikoriak</h1>

<div class="contact">
Python GIS Engineer | Hydrologist | GeoAI Researcher<br>
Phone: +380 000 000 000<br>
Email: your.email@example.com<br>
</div>
```

Заміни ім'я, професійну роль, телефон, email, LinkedIn, GitHub, сайт або ORCID на власні дані.

---

### Редагування розділів

Типові розділи CV:

```html
<h2>Professional Summary</h2>
<h2>Core Competencies</h2>
<h2>Technical Skills</h2>
<h2>Selected Projects</h2>
<h2>Professional Experience</h2>
<h2>Education</h2>
<h2>Publications</h2>
<h2>Certifications and Workshops</h2>
<h2>Languages</h2>
```

Їх можна перейменовувати, видаляти або додавати нові.

Наприклад, для Python-розробника:

```html
<h2>Technical Projects</h2>
<h2>Backend Development</h2>
<h2>Open Source Contributions</h2>
```

Для науковця:

```html
<h2>Research Interests</h2>
<h2>Publications</h2>
<h2>Grants</h2>
<h2>Conference Presentations</h2>
```

Для GIS-фахівця:

```html
<h2>Geospatial Skills</h2>
<h2>Remote Sensing Projects</h2>
<h2>Hydrological Modeling</h2>
```

---

## 11. Як змінити дизайн

Дизайн контролюється CSS-кодом всередині HTML-файлу.

Приклад:

```css
body {
    font-family: Arial, Helvetica, sans-serif;
    margin: 40px;
    line-height: 1.6;
    color: #222;
}

h1 {
    color: #003366;
    margin-bottom: 5px;
}

h2 {
    color: #003366;
    margin-top: 26px;
    border-bottom: 2px solid #003366;
    padding-bottom: 4px;
    page-break-after: avoid;
}
```

### Зміна основного кольору

Знайди:

```css
color: #003366;
```

і заміни на інший колір, наприклад:

```css
color: #1f4e79;
```

або:

```css
color: #2e7d32;
```

---

### Зміна розміру шрифту

Для тексту абзаців:

```css
p {
    font-size: 15px;
}
```

Для списків:

```css
li {
    font-size: 15px;
}
```

Щоб зробити CV компактнішим:

```css
p,
li {
    font-size: 13.5px;
}
```

---

### Покращення розривів сторінок

Для PDF важливо, щоб заголовки не відривалися від тексту.

Корисні CSS-правила:

```css
h2,
h3 {
    page-break-after: avoid;
}

section {
    page-break-inside: avoid;
}

ul {
    page-break-inside: avoid;
}
```

Це допомагає уникнути ситуації, коли заголовок опиняється внизу сторінки, а текст починається вже на наступній.

---

## 12. Налаштування PDF

У Python-скрипті використовуються такі параметри:

```python
options = {
    "encoding": "UTF-8",
    "page-size": "A4",
    "orientation": "Portrait",
    "margin-top": "15mm",
    "margin-right": "15mm",
    "margin-bottom": "15mm",
    "margin-left": "15mm",
    "enable-local-file-access": None,
    "print-media-type": None,
}
```

### Основні параметри

| Параметр | Значення |
|---|---|
| `encoding` | Кодування тексту, зазвичай `UTF-8` |
| `page-size` | Розмір сторінки, наприклад `A4` або `Letter` |
| `orientation` | Орієнтація: `Portrait` або `Landscape` |
| `margin-top` | Верхнє поле сторінки |
| `margin-right` | Праве поле сторінки |
| `margin-bottom` | Нижнє поле сторінки |
| `margin-left` | Ліве поле сторінки |
| `enable-local-file-access` | Дозволяє підвантажувати локальні файли, наприклад зображення |
| `print-media-type` | Використовує CSS-стилі для друку |

Приклад із меншими полями:

```python
options = {
    "encoding": "UTF-8",
    "page-size": "A4",
    "margin-top": "10mm",
    "margin-right": "10mm",
    "margin-bottom": "10mm",
    "margin-left": "10mm",
}
```

---

## 13. Пряме використання wkhtmltopdf без Python

Можна використовувати `wkhtmltopdf` напряму з терміналу:

```bash
wkhtmltopdf cv_viktor_nikoriak_GeoAI.html CV_Viktor_Nikoriak_GeoAI.pdf
```

З параметрами:

```bash
wkhtmltopdf --page-size A4 --margin-top 15mm --margin-bottom 15mm cv_viktor_nikoriak_GeoAI.html CV_Viktor_Nikoriak_GeoAI.pdf
```

Це корисно, щоб перевірити, чи працює `wkhtmltopdf` незалежно від Python.

---

## 14. Посилання в CV

HTML-посилання записуються так:

```html
<a href="https://github.com/your-username">GitHub</a>
```

Для зовнішніх посилань використовуй повні URL:

```html
<a href="https://www.linkedin.com/in/your-profile/">LinkedIn</a>
```

Для локальних файлів краще використовувати відносні шляхи:

```html
<img src="assets/photo.jpg" alt="Profile photo">
```

Якщо використовуються локальні зображення або CSS-файли, вони мають бути в папці проєкту, а в Python-опціях має бути:

```python
"enable-local-file-access": None
```

---

## 15. Додавання фото

Створи папку `assets`:

```text
CV_maker/
│
├── assets/
│   └── profile.jpg
├── cv_viktor_nikoriak.html
├── generate_cv_pdf.py
└── README.md
```

Додай у HTML:

```html
<img src="assets/profile.jpg" alt="Profile photo" class="profile-photo">
```

Додай CSS:

```css
.profile-photo {
    width: 120px;
    border-radius: 50%;
    float: right;
    margin-left: 20px;
}
```

Важливо: у деяких країнах і сферах CV без фото є більш прийнятним форматом.

---

## 16. Створення кількох версій CV

Можна створити кілька HTML-шаблонів:

```text
cv_academic.html
cv_python_developer.html
cv_gis_engineer.html
cv_short.html
```

Потім у Python-скрипті змінити:

```python
HTML_FILE = BASE_DIR / "cv_academic.html"
OUTPUT_PDF = BASE_DIR / "CV_Academic.pdf"
```

Так можна створювати різні CV для різних задач:

- академічне CV;
- CV для Python Developer;
- CV для GIS Engineer;
- коротке CV на 1 сторінку;
- CV для грантової заявки;
- CV для LinkedIn-профілю.

---

## 17. Рекомендований робочий процес

Хороший робочий процес:

```text
1. Відредагувати HTML.
2. Відкрити HTML у браузері й перевірити вигляд.
3. Запустити generate_cv_pdf.py.
4. Відкрити згенерований PDF.
5. За потреби поправити CSS.
6. Зберегти зміни в Git.
```

Приклад Git-команд:

```bash
git add cv_viktor_nikoriak_GeoAI.html generate_cv_pdf.py README.md
git commit -m "Update CV generator"
```

Згенерований PDF можна або комітити, або не комітити — залежно від того, як часто він змінюється.

---

## 18. Типові проблеми

### `wkhtmltopdf` не розпізнається в терміналі

Перевір:

```powershell
where wkhtmltopdf
```

Якщо нічого не показує, перезапусти PowerShell, PyCharm або комп'ютер.

Також можна вручну вказати шлях у скрипті:

```python
r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
```

---

### PDF виглядає не так, як HTML у браузері

HTML у браузері й HTML у `wkhtmltopdf` можуть рендеритися трохи по-різному.

Рекомендації:

- використовуй простий CSS;
- уникай дуже нових CSS-функцій;
- не покладайся на складний JavaScript;
- перевіряй PDF після великих змін;
- краще використовувати статичний HTML і CSS.

---

### Українські символи або спеціальні символи відображаються неправильно

Переконайся, що в HTML є:

```html
<meta charset="UTF-8">
```

А в Python-опціях є:

```python
"encoding": "UTF-8"
```

---

### Зображення не відображаються

Переконайся, що в опціях є:

```python
"enable-local-file-access": None
```

Також перевір шлях до зображення.

Добре:

```html
<img src="assets/profile.jpg">
```

Гірше:

```html
<img src="C:\Users\YourName\Desktop\profile.jpg">
```

Краще тримати всі зображення всередині папки проєкту.

---

### CV занадто довге

Можна зробити текст компактнішим через CSS:

```css
body {
    margin: 25px;
    line-height: 1.4;
}

p,
li {
    font-size: 13px;
}
```

Також можна зменшити відступи між розділами:

```css
h2 {
    margin-top: 18px;
}
```

---

### Заголовки залишаються самі внизу сторінки

Додай:

```css
h2,
h3 {
    page-break-after: avoid;
}
```

Для великих блоків:

```css
section {
    page-break-inside: avoid;
}
```

---

## 19. Безпека

Використовуй цей проєкт тільки з HTML, якому довіряєш.

Не варто запускати невідомий або користувацький HTML через `wkhtmltopdf` на сервері без попередньої перевірки й очищення.

Безпечні сценарії:

- власне CV;
- власне портфоліо;
- власні шаблони звітів;
- локальні персональні документи.

Ризиковані сценарії:

- приймати HTML від невідомих користувачів;
- автоматично генерувати PDF з чужих вебсторінок на production-сервері;
- дозволяти довільний JavaScript у завантажених шаблонах.

---

## 20. Ідеї для розвитку проєкту

Можливі покращення:

- винести CSS в окремий файл;
- додати фото профілю;
- додати кілька CV-шаблонів;
- створити `requirements.txt`;
- додати вибір типу CV через аргументи командного рядка;
- додати Streamlit-інтерфейс;
- додати Django-view для генерації PDF;
- додати GitHub Actions для автоматичної генерації PDF;
- додати українську й англійську версії CV;
- винести персональні дані в JSON або YAML.

Можлива майбутня структура:

```text
CV_maker/
│
├── data/
│   └── cv_data.yaml
├── templates/
│   ├── academic.html
│   ├── developer.html
│   └── gis_engineer.html
├── assets/
│   └── profile.jpg
├── generate_cv_pdf.py
├── requirements.txt
└── README.md
```

Така структура відділяє дані, дизайн і логіку генерації.

---

## 21. Мінімальна версія для початківців

Найпростіший варіант складається лише з двох файлів:

```text
CV_maker/
│
├── cv.html
└── generate_pdf.py
```

`cv.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>My CV</title>
</head>
<body>
    <h1>Your Name</h1>
    <p>Your professional title</p>

    <h2>Experience</h2>
    <p>Your experience here.</p>
</body>
</html>
```

`generate_pdf.py`:

```python
import pdfkit

pdfkit.from_file("cv.html", "cv.pdf")
```

Запуск:

```bash
python generate_pdf.py
```

Це найменша робоча версія.

---

## 22. Головна ідея

Цей проєкт не лише про генерацію PDF.

Він показує важливий інженерний принцип:

```text
Відділяй зміст, дизайн і логіку генерації.
```

Замість того щоб ховати великий HTML-документ прямо всередині Python-коду, проєкт розділяє:

```text
HTML → зміст і дизайн
Python → автоматизація
PDF → фінальний результат
```

Так CV легше підтримувати, оновлювати, перевикористовувати й публікувати.
