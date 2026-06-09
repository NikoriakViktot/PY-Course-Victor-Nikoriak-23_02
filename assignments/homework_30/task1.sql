CREATE TABLE contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL
);
ALTER TABLE contacts RENAME TO phone_book;
ALTER TABLE phone_book ADD COLUMN phone_number TEXT;
INSERT INTO phone_book (first_name, last_name, phone_number)
VALUES ('Тарас', 'Шевченко', '+380501111111');
INSERT INTO phone_book (first_name, last_name, phone_number)
VALUES ('Леся', 'Українка', '+380672222222');
INSERT INTO phone_book (first_name, last_name, phone_number)
VALUES ('Іван', 'Франко', '+380933333333');
UPDATE phone_book
SET phone_number = '+380679999999'
WHERE id = 2;
DELETE FROM phone_book
WHERE id = 3;
