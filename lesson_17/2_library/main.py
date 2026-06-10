class Library:
    def __init__(self, name):
        self.name = name
        self.books = []
        self.authors = []

    def new_book(self, name: str, year: int, author):
        if not isinstance(author, Author):
            raise ValueError("Author must be an instance of Author class")

        book = Book(name, year, author)
        self.books.append(book)

        if author not in self.authors:
            self.authors.append(author)

        return book

    def group_by_author(self, author):
        if not isinstance(author, Author):
            raise ValueError("Author must be an instance of Author class")

        return [book for book in self.books if book.author == author]

    def group_by_year(self, year: int):
        return [book for book in self.books if book.year == year]

    def __str__(self):
        return f"Library: {self.name}"

    def __repr__(self):
        return f"Library(name={self.name!r}, books={len(self.books)}, authors={len(self.authors)})"


class Book:
    book_amount = 0

    def __init__(self, name: str, year: int, author):
        if not isinstance(author, Author):
            raise ValueError("Author must be an instance of Author class")

        self.name = name
        self.year = year
        self.author = author
        Book.book_amount += 1
        author.books.append(self)

    def __str__(self):
        return f"{self.name} by {self.author.name}"

    def __repr__(self):
        return f"Book(name={self.name!r}, year={self.year!r}, author={self.author.name!r})"


class Author:
    def __init__(self, name: str, country: str, birthday: str):
        self.name = name
        self.country = country
        self.birthday = birthday
        self.books = []

    def __str__(self):
        return f"Author: {self.name}"

    def __repr__(self):
        return f"Author(name={self.name!r}, country={self.country!r}, birthday={self.birthday!r})"


library = Library("City Library")
author = Author("George Orwell", "United Kingdom", "25 June 1903")

book_1 = library.new_book("Animal Farm", 1945, author)
book_2 = library.new_book("Nineteen Eighty-Four", 1949, author)

assert book_1 in library.books
assert book_2 in library.group_by_author(author)
assert library.group_by_year(1945) == [book_1]
assert Book.book_amount == 2

print(library)
print(author)
print(book_1)
print("All assertions passed")
