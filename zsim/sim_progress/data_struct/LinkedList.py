from typing import Generic, TypeVar

T = TypeVar("T")


class Node(Generic[T]):
    def __init__(self, data: T | None = None):
        self.data: T | None = data
        self.next: "Node[T] | None" = None


class NodeIterator(Generic[T]):
    def __init__(self, head: Node[T] | None):
        self.current: Node[T] | None = head

    def __next__(self) -> T:
        if self.current is None:
            raise StopIteration
        data = self.current.data
        self.current = self.current.next
        if data is None:
            raise StopIteration
        return data

    def __iter__(self):
        return self


class LinkedList(Generic[T]):
    def __init__(self):
        self.head: Node[T] | None = None

    def add(self, data: T) -> None:
        """在链表尾部添加"""
        new_node = Node(data)
        if self.head is None:
            self.head = new_node
        else:
            current = self.head
            while current.next:
                current = current.next
            current.next = new_node

    def insert(self, data: T) -> None:
        """在链表头部插入"""
        new_node = Node(data)
        new_node.next = self.head
        self.head = new_node

    def __iter__(self):
        return NodeIterator(self.head)

    def __str__(self) -> str:
        elements = []
        current = self.head
        while current:
            elements.append(current.data)
            current = current.next
        return str(elements)

    def __len__(self) -> int:
        count = 0
        current = self.head
        while current:
            count += 1
            current = current.next
        return count

    def __getitem__(self, index: int) -> Node[T]:
        current = self.head
        if current is None:
            raise IndexError("Index out of range")
        for _ in range(index):
            current = current.next
            if current is None:
                raise IndexError("Index out of range")
        return current

    def print_list(self) -> None:
        current = self.head
        while current:
            print(f"{current.data} -> ", end="")
            current = current.next
        print("None")

    def pop_head(self) -> Node[T] | None:
        if self.head is not None:
            removed_node = self.head
            self.head = self.head.next
            return removed_node
        else:
            return None

    def remove(self, data: T) -> bool:
        current = self.head
        previous = None
        while current:
            if current.data == data:
                if previous:
                    previous.next = current.next
                else:
                    self.head = current.next
                return True
            previous = current
            current = current.next
        return False
