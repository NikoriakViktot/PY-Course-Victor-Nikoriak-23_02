class Product:
    def __init__(self, product_type, name, price):
        self.product_type = product_type
        self.name = name
        self.price = price

class ProductStore:
    def __init__(self):
        self.products = {}
        self.income = 0
    def add(self, product, amount):
        store_price = product.price * 1.3
        if product.name in self.products:
            self.products[product.name]['amount'] += amount
        else:
            self.products[product.name] = {'product': product, 'amount': amount, 'price': store_price}
    def set_discount(self, identifier, percent, identifier_type="name"):
        for item in self.products.values():
            if identifier_type == 'name':
                check_value = item['product'].name
            else:
                check_value = item['product'].product_type
            if check_value == identifier:
                item['price'] -= item['price'] * (percent / 100)
    def sell_product(self, product_name, amount):
        if product_name not in self.products:
            raise ValueError("Товару з такою назвою не існує")
        if self.products[product_name]['amount'] < amount:
            raise ValueError("Недостатньо товару на складі")
        else:
            self.products[product_name]['amount'] -= amount
            self.income += (self.products[product_name]['price'] * amount)
    def get_income(self):
        return self.income
    def get_all_products(self):
        return self.products

    def get_product_info(self, product_name):
        amount = self.products[product_name]['amount']
        return (product_name, amount)

p = Product('Sport', 'Football T-Shirt', 100)
p2 = Product('Food', 'Ramen', 1.5)
s = ProductStore()

s.add(p, 10)
s.add(p2, 300)
s.sell_product('Ramen', 10)

assert s.get_product_info('Ramen') == ('Ramen', 290)