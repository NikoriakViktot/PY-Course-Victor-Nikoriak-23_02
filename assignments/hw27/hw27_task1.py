from html.parser import HTMLParser


# -------------------------------
# ВУЗОЛ ДЕРЕВА
# -------------------------------
class Node:
    def __init__(self, tag, text=""):
        self.tag = tag
        self.text = text.strip()
        self.children = []
        self.parent = None

    def add_child(self, node):
        node.parent = self
        self.children.append(node)

    def remove(self):
        if self.parent:
            self.parent.children.remove(self)
            self.parent = None

    def __repr__(self):
        return f"<{self.tag}>: {self.text}"


# -------------------------------
# ДЕРЕВО
# -------------------------------
class Tree:
    def __init__(self, root=None):
        self.root = root

    def insert_subtree(self, parent_node, subtree):
        """Вставка піддерева"""
        if subtree.root:
            parent_node.add_child(subtree.root)

    def delete_subtree(self, node):
        """Видалення піддерева"""
        node.remove()

    def find_by_tag(self, tag):
        """Пошук всіх вузлів за тегом"""
        result = []

        def dfs(node):
            if node.tag == tag:
                result.append(node)
            for child in node.children:
                dfs(child)

        if self.root:
            dfs(self.root)

        return result

    def print_tree(self, node=None, level=0):
        if node is None:
            node = self.root

        print("  " * level + f"{node.tag}: {node.text}")

        for child in node.children:
            self.print_tree(child, level + 1)


# -------------------------------
# HTML → DOM ПАРСЕР
# -------------------------------
class DOMParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.tree = Tree()

    def handle_starttag(self, tag, attrs):
        node = Node(tag)

        if not self.stack:
            self.tree.root = node
        else:
            self.stack[-1].add_child(node)

        self.stack.append(node)

    def handle_endtag(self, tag):
        if self.stack:
            self.stack.pop()

    def handle_data(self, data):
        if self.stack:
            self.stack[-1].text += data.strip() + " "


# -------------------------------
# ПРИКЛАД ВИКОРИСТАННЯ
# -------------------------------
if __name__ == "__main__":
    html_doc = """
    <html>
        <body>
            <h1>Заголовок</h1>
            <p>Це параграф</p>
            <div>
                <p>Ще один текст</p>
            </div>
        </body>
    </html>
    """

    # Парсимо HTML
    parser = DOMParser()
    parser.feed(html_doc)

    tree = parser.tree

    print("=== ДЕРЕВО ===")
    tree.print_tree()

    # Пошук за тегом
    tag_to_find = "p"
    print(f"\n=== ПОШУК ТЕГА '{tag_to_find}' ===")
    nodes = tree.find_by_tag(tag_to_find)

    for n in nodes:
        print(n.text)

    # Вставка піддерева
    print("\n=== ВСТАВКА ПІДДЕРЕВА ===")
    new_subtree = Tree(Node("div", "Новий блок"))

    body = tree.find_by_tag("body")[0]
    tree.insert_subtree(body, new_subtree)

    tree.print_tree()

    # Видалення піддерева
    print("\n=== ВИДАЛЕННЯ ПІДДЕРЕВА ===")
    to_delete = tree.find_by_tag("h1")[0]
    tree.delete_subtree(to_delete)

    tree.print_tree()