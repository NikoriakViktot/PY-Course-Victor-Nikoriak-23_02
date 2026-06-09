# ── Базова реалізація Node — використовується у всіх задачах ─────────────────
from __future__ import annotations
from collections import deque
from typing import Optional


class Node:
    """Вузол бінарного дерева."""
    def __init__(self, value: int):
        self.value = value
        self.left:  Optional[Node] = None
        self.right: Optional[Node] = None

    def __repr__(self):
        return f"Node({self.value})"


def inorder(node, result=None):
    """In-order обхід (Лів → Корінь → Прав). Повертає список значень."""
    if result is None: result = []
    if node:
        inorder(node.left,  result)
        result.append(node.value)
        inorder(node.right, result)
    return result


def height(node) -> int:
    """Висота дерева. O(n)."""
    if node is None: return -1
    return 1 + max(height(node.left), height(node.right))


def is_valid_bst(node, min_val=float('-inf'), max_val=float('inf')) -> bool:
    """Валідація BST через передачу глобального діапазону."""
    if node is None: return True
    if not (min_val < node.value < max_val): return False
    return (is_valid_bst(node.left,  min_val, node.value) and
            is_valid_bst(node.right, node.value, max_val))


def bst_insert(node, value) -> Node:
    """Вставка значення у BST. Повертає (можливо новий) корінь."""
    if node is None: return Node(value)
    if value < node.value: node.left  = bst_insert(node.left,  value)
    elif value > node.value: node.right = bst_insert(node.right, value)
    return node


print("Базові структури завантажено ✓")


def find_lca(root: Optional[Node], node_a: Node, node_b: Node) -> Optional[Node]:
    """ Пошук Найнижчого Спільного Предка (LCA) у бінарному дереві. """
    # 1. Базовий випадок: якщо root is None → return None
    if root is None:
        return None

    # 2. Якщо root == node_a або root == node_b → return root
    if root == node_a or root == node_b:
        return root

    # 3. Рекурсивно шукаємо зліва
    left = find_lca(root.left, node_a, node_b)

    # 4. Рекурсивно шукаємо справа
    right = find_lca(root.right, node_a, node_b)

    # 5. Якщо left і right обидва не None → root є LCA → return root
    if left is not None and right is not None:
        return root

    # 6. Інакше → return left if left else right
    return left if left is not None else right


def insert_subtree(root: Optional[Node], target_value: int, subtree: Optional[Node], to_left: bool = True) -> bool:
    """
    Знаходить вузол із значенням target_value та приєднує до нього subtree.
    to_left = True  -> вставляє в ліве піддерево (node.left)
    to_left = False -> вставляє в праве піддерево (node.right)
    Повертає True, якщо вузол знайдено і вставку виконано, інакше False.
    """
    if root is None:
        return False

    # Якщо знайшли цільовий вузол — приєднуємо піддерево
    if root.value == target_value:
        if to_left:
            root.left = subtree
        else:
            root.right = subtree
        return True

    # Шукаємо далі рекурсивно в лівому або правому піддереві
    if insert_subtree(root.left, target_value, subtree, to_left):
        return True
    return insert_subtree(root.right, target_value, subtree, to_left)


def delete_subtree(root: Optional[Node], target_value: int) -> Optional[Node]:
    """
    Знаходить вузол із значенням target_value і повністю видаляє його
    разом з усім його піддеревом.
    Повертає (можливо новий) корінь дерева.
    """
    if root is None:
        return None

    # Якщо сам корінь є цільовим вузлом — видаляємо все дерево
    if root.value == target_value:
        return None

    # Перевіряємо лівого нащадка: якщо це цільовий вузол — відсікаємо його
    if root.left and root.left.value == target_value:
        root.left = None
        return root

    # Перевіряємо правого нащадка: якщо це цільовий вузол — відсікаємо його
    if root.right and root.right.value == target_value:
        root.right = None
        return root

    # Рекурсивно запускаємо видалення для піддерев
    delete_subtree(root.left, target_value)
    delete_subtree(root.right, target_value)
    return root




def run_task2_tests():
    # Будуємо дерево:
    #       4
    #      / \
    #     2   6
    #    / \ / \
    #   1  3 5  7
    r = Node(4)
    r.left = Node(2);  r.right = Node(6)
    r.left.left  = Node(1);  r.left.right  = Node(3)
    r.right.left = Node(5);  r.right.right = Node(7)

    n1 = r.left.left    # Node(1)
    n2 = r.left         # Node(2)
    n3 = r.left.right   # Node(3)
    n5 = r.right.left   # Node(5)
    n6 = r.right        # Node(6)
    n7 = r.right.right  # Node(7)

    print("=== Задача 2: Найнижчий Спільний Предок (LCA) ===")
    print()

    cases = [
        (n1, n3, n2, "LCA(1,3)=2"),
        (n1, n7, r,  "LCA(1,7)=4"),
        (n5, n7, n6, "LCA(5,7)=6"),
        (n2, n6, r,  "LCA(2,6)=4"),
        (n1, n2, n2, "LCA(1,2)=2 (один є предком іншого)"),
    ]

    for a, b, expected, desc in cases:
        result = find_lca(r, a, b)
        ok = result is expected
        print(f"  [{'✓' if ok else '✗'}] {desc}: результат={result}")


run_task2_tests()