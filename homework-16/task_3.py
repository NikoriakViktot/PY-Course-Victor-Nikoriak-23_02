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
        price_with_markup = product.price * 1.3

        if product.name in self.products:
            self.products[product.name]['amount'] += amount

        else:
            self.products[product.name] = {
                'product': product,
                'amount': amount,
                'price': price_with_markup
            }

    def set_discount(self, identifier, percent, identifier_type='name'):
        found = False

        for product_dict in self.products.values():
            product = product_dict['product']

            if (identifier_type == 'name') and (product.name == identifier) or \
                (identifier_type == 'type') and (product.type == identifier):
                product_dict['price'] *= (1 - percent / 100)
                found = True

        if not found:
            raise ValueError("No product found")

    def sell_product(self, product_name, amount):
        if product_name not in self.products:
            raise ValueError(f"{product_name} not found in store")

        product_dict = self.products[product_name]

        if product_dict['amount'] < amount:
            raise ValueError(f"Not enough {product_name} in store")

        product_dict['amount'] -= amount
        self.income += product_dict['price'] * amount

    def get_income(self):
        return self.income

    def get_all_products(self):
        return self.products.values()

    def get_product_info(self, product_name):
        if product_name not in self.products:
            raise ValueError(f"{product_name} not found in store")

        else:
            product_info = self.products[product_name]
            amount = product_info['amount']
            return (product_name, amount)


p = Product('Sport', 'Football T-Shirt', 100)
p2 = Product('Food', 'Ramen', 1.5)

s = ProductStore()
s.add(p, 10)
s.add(p2, 300)

s.sell_product('Ramen', 10)
assert s.get_product_info('Ramen') == ('Ramen', 290)