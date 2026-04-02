class Product:
    def __init__(self, type, name, price):
        self.type = type
        self.name = name
        self.price = price


class ProductStore:
    def __init__(self):
        self.products = {}
        self.income = 0

    def add(self, product, amount):
        if amount <= 0:
            raise ValueError("Amount must be positive")

        product.price *= 1.3  # +30%

        if product.name in self.products:
            self.products[product.name]["amount"] += amount
        else:
            self.products[product.name] = {
                "product": product,
                "amount": amount
            }

    def set_discount(self, identifier, percent, identifier_type='name'):
        for item in self.products.values():
            product = item["product"]

            if (identifier_type == 'name' and product.name == identifier) or \
               (identifier_type == 'type' and product.type == identifier):
                product.price *= (1 - percent / 100)

    def sell_product(self, product_name, amount):
        if product_name not in self.products:
            raise ValueError("Product not found")

        item = self.products[product_name]

        if item["amount"] < amount:
            raise ValueError("Not enough product in stock")

        item["amount"] -= amount
        self.income += item["product"].price * amount

    def get_income(self):
        return self.income

    def get_all_products(self):
        return [(p["product"].name, p["amount"]) for p in self.products.values()]

    def get_product_info(self, product_name):
        if product_name not in self.products:
            raise ValueError("Product not found")

        item = self.products[product_name]
        return (item["product"].name, item["amount"])


# Test
p = Product('Sport', 'Football T-Shirt', 100)
p2 = Product('Food', 'Ramen', 1.5)

s = ProductStore()

s.add(p, 10)
s.add(p2, 300)
s.sell_product('Ramen', 10)

print(s.get_product_info('Ramen'))
print("Income:", s.get_income())

assert s.get_product_info('Ramen') == ('Ramen', 290)