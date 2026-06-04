# Написати алгоритм, що буде парсити html документ та зберігати його Document Object
# Model (DOM) у дереві. Дерево повинно зберігати тег та текст, обрамлений цим тегом
# (якщо є такий). Додати можливість пошуку тексту за тегом.
# Вхідні дані: html документ та тег
# Вихідні дані: текст, якщо є.
from html.parser import HTMLParser
# --- Клас Вузла Дерева (DOM Node) ---
class DOMNode:
    def __init__(self, tag, text=""):
        self.tag = tag  # Назва тегу (наприклад, 'h1', 'p', 'div')
        self.text = text  # Текст всередині тегу (якщо є)
        self.children = []  # Список дочірніх вузлів дерева
    def add_child(self, child_node):
        """Додає дочірній елемент до поточного вузла"""
        self.children.append(child_node)
# --- Клас Парсера HTML ---
class DOMParser(HTMLParser):
    def __init__(self):
        super().__init__()
        # Створюємо кореневий віртуальний вузол для всього документа
        self.root = DOMNode("root")
        # Стек допомагає нам відстежувати рівні вкладеності тегів (DOM дерево)
        self.stack = [self.root]
    def handle_starttag(self, tag, attrs):
        """Викликається, коли парсер зустрічає відкриваючий тег: <p>, <div>"""
        # Ті теги, які не мають закриваючих пар (самозакривні), можна ігнорувати або додавати окремо
        if tag in ('meta', 'link', 'br', 'img', 'hr'):
            new_node = DOMNode(tag)
            self.stack[-1].add_child(new_node)
            return
        new_node = DOMNode(tag)
        # Додаємо новий вузол як дитину до поточного активного вузла (верхнього у стеку)
        self.stack[-1].add_child(new_node)
        # Кладемо новий вузол у стек — тепер він поточний контекст розбору
        self.stack.append(new_node)
    def handle_data(self, data):
        """Викликається, коли парсер знаходить текст між тегами"""
        cleaned_data = data.strip()
        if cleaned_data and len(self.stack) > 1:
            # Додаємо текст до поточного активного тегу на вершині стеку
            # Якщо текст розбитий на кілька рядків, об'єднуємо його
            if self.stack[-1].text:
                self.stack[-1].text += " " + cleaned_data
            else:
                self.stack[-1].text = cleaned_data
    def handle_endtag(self, tag):
        """Викликається, коли парсер зустрічає закриваючий тег: </p>, </div>"""
        if tag in ('meta', 'link', 'br', 'img', 'hr'):
            return
        # Якщо закриваючий тег збігається з поточним у стеку, забираємо його зі стеку
        if len(self.stack) > 1 and self.stack[-1].tag == tag:
            self.stack.pop()
# --- Функція Пошуку тексту за Тегом (Обхід дерева вглиб - DFS) ---
def find_text_by_tag(node, target_tag, results=None):    """
    Рекурсивно шукає всі тексти для заданого тегу в дереві.
    Повертає список знайдених текстових блоків.
    """
    if results is None:
        results = []
    # Якщо тег збігається і містить текст, додаємо до результатів
    if node.tag == target_tag and node.text:
        results.append(node.text)
    # Рекурсивно перевіряємо всіх дітей цього вузла
    for child in node.children:
        find_text_by_tag(child, target_tag, results)
    return results
if __name__ == "__main__":
    # Вхідні дані: HTML документ
    html_document = """
    <html>
        <head>
            <title>Мій блог</title>
        </head>
        <body>
            <div class="content">
                <h1>Ласкаво просимо до Python!</h1>
                <p>Зв'язані списки та дерева — це базові структури.</p>
                <p>Дерево DOM дозволяє парсити HTML документи.</p>
            </div>
            <footer>
                <p>Контакти: info@example.com</p>
            </footer>
        </body>
    </html> 
    """

# 1. Ініціалізуємо парсер та передаємо йому документ
    parser = DOMParser()
    parser.feed(html_document)
# Отримуємо корінь нашого згенерованого DOM-дерева
    dom_tree_root = parser.root
# 2. Вхідні дані: Тег для пошуку
    search_tag = "p"
# 3. Виконуємо пошук по створеному дереву
    found_texts = find_text_by_tag(dom_tree_root, search_tag)
    # Вихідні дані: Текст, якщо є
    print(f"--- Результати пошуку тексту для тегу <{search_tag}> ---")
    if found_texts:
        for idx, text in enumerate(found_texts, 1):
            print(f"{idx}. {text}")
    else:
        print(f"Тексту для тегу <{search_tag}> не знайдено.")
    print("\n" + "-" * 40 + "\n")
# Спробуємо знайти інший тег
    search_tag_h1 = "h1"
    found_h1 = find_text_by_tag(dom_tree_root, search_tag_h1)
    print(f"--- Результати пошуку тексту для тегу <{search_tag_h1}> ---")
    print(found_h1[0] if found_h1 else "Не знайдено")
