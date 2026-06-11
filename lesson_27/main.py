from html.parser import HTMLParser


class DOMNode:
    def __init__(self, tag, parent=None):
        self.tag = tag
        self.text = ""
        self.children = []
        self.parent = parent

    def add_child(self, child):
        self.children.append(child)

    def add_text(self, text):
        text = text.strip()

        if text:
            if self.text:
                self.text += " "
            self.text += text

    def get_text(self):
        parts = []

        if self.text:
            parts.append(self.text)

        for child in self.children:
            child_text = child.get_text()
            if child_text:
                parts.append(child_text)

        return " ".join(parts)

    def find_by_tag(self, tag):
        result = []

        if self.tag == tag:
            result.append(self)

        for child in self.children:
            result.extend(child.find_by_tag(tag))

        return result

    def __str__(self):
        return f"<{self.tag}> {self.get_text()}"

    def __repr__(self):
        return f"DOMNode(tag={self.tag!r}, text={self.text!r})"


class DOMTreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__()
        self.root = DOMNode("document")
        self.current_node = self.root

    def handle_starttag(self, tag, attrs):
        new_node = DOMNode(tag, self.current_node)
        self.current_node.add_child(new_node)
        self.current_node = new_node

    def handle_endtag(self, tag):
        while self.current_node.parent is not None and self.current_node.tag != tag:
            self.current_node = self.current_node.parent

        if self.current_node.parent is not None:
            self.current_node = self.current_node.parent

    def handle_data(self, data):
        self.current_node.add_text(data)

    def get_tree(self):
        return self.root


def parse_html(html_document):
    parser = DOMTreeBuilder()
    parser.feed(html_document)
    return parser.get_tree()


def find_text_by_tag(root, tag):
    nodes = root.find_by_tag(tag)
    return [node.get_text() for node in nodes if node.get_text()]


def main():
    html_file_path = input("Enter html file path: ").strip()
    tag = input("Enter tag: ").strip().lower()

    try:
        with open(html_file_path, "r", encoding="utf-8") as file:
            html_document = file.read()
    except FileNotFoundError:
        print("HTML file was not found")
        return

    dom_tree = parse_html(html_document)
    texts = find_text_by_tag(dom_tree, tag)

    if not texts:
        print(f"No text found for tag '{tag}'")
        return

    for text in texts:
        print(text)


if __name__ == "__main__":
    main()
