class Library:
    def __init__(self, name):
        self.name = name
        self.books = []
        self.authors = []

    def new_book(self, name, year, author):
        if author not in self.authors:
            self.authors.append(author)
        book = Book(name, year, author)
        self.books.append(book)
        return book

    def group_by_author(self, author):
        return [book for book in self.books if book.author == author]

    def group_by_year(self, year):
        return [book for book in self.books if book.year == year]

    def __repr__(self):
        return f'Library({self.name})'

    def __str__(self):
        return f'Library {self.name} with {len(self.books)} books'


class Book:
    total_books = 0
    def __init__(self, name, year, author):
        self.name = name
        self.year = year
        self.author = author
        Book.total_books += 1
        author.books.append(self)

    def __repr__(self):
        return f'Book({self.name})'

    def __str__(self):
        return f'{self.name}, ({self.year}, by {self.author.name})'


class Author:
    def __init__(self, name, country, birthday):
        self.name = name
        self.country = country
        self.birthday = birthday
        self.books = []

    def __repr__(self):
        return f'Author({self.name})'

    def __str__(self):
        return f'{self.name}, ({self.country}, born {self.birthday})'