class Author:
    def __init__(self, name, country, birthday):
        self.name = name
        self.country = country
        self.birthday = birthday
        self.books = []

    def __repr__(self):
        return f"Author(name='{self.name}', country='{self.country}')"

    def __str__(self):
        return f"{self.name} from {self.country}"


class Book:
    total_books = 0

    def __init__(self, name, year, author):
        if not isinstance(author, Author):
            raise ValueError("author must be an instance of Author")

        self.name = name
        self.year = year
        self.author = author

        author.books.append(self)
        Book.total_books += 1

    def __repr__(self):
        return f"Book(name='{self.name}', year={self.year}, author='{self.author.name}')"

    def __str__(self):
        return f"'{self.name}' by {self.author.name} ({self.year})"


class Library:
    def __init__(self, name):
        self.name = name
        self.books = []
        self.authors = []

    def new_book(self, name, year, author):
        book = Book(name, year, author)
        self.books.append(book)

        if author not in self.authors:
            self.authors.append(author)

        return book

    def group_by_author(self, author):
        return [book for book in self.books if book.author == author]

    def group_by_year(self, year):
        return [book for book in self.books if book.year == year]

    def __repr__(self):
        return f"Library(name='{self.name}', books={len(self.books)})"

    def __str__(self):
        return f"Library '{self.name}' with {len(self.books)} books"


# Example
author1 = Author("George Orwell", "UK", "1903-06-25")
author2 = Author("J.K. Rowling", "UK", "1965-07-31")

lib = Library("My Library")

lib.new_book("1984", 1949, author1)
lib.new_book("Animal Farm", 1945, author1)
lib.new_book("Harry Potter", 1997, author2)

print(lib.group_by_author(author1))
print(lib.group_by_year(1949))
print("Total books:", Book.total_books)