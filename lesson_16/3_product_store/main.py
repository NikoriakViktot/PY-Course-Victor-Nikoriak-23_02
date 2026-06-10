class Product:
    def __init__(self, type_, name, price):
        self.type = type_
        self.name = name
        self.price = price


class ProductStore:
    def __init__(self):
        self.products = {}
        self.income = 0
        self.price_premium = 30

    def add(self, product, amount):
        if not isinstance(product, Product):
            raise ValueError("Only Product instances can be added")

        if amount <= 0:
            raise ValueError("Amount must be greater than zero")

        product_price = product.price + product.price * self.price_premium / 100

        if product.name in self.products:
            self.products[product.name]["amount"] += amount
        else:
            self.products[product.name] = {
                "product": Product(product.type, product.name, product_price),
                "amount": amount,
                "discount": 0,
            }

    def set_discount(self, identifier, percent, identifier_type="name"):
        if percent < 0 or percent > 100:
            raise ValueError("Discount percent must be from 0 to 100")

        if identifier_type not in ("name", "type"):
            raise ValueError("Identifier type must be name or type")

        found = False

        for product_data in self.products.values():
            product = product_data["product"]

            if getattr(product, identifier_type) == identifier:
                product_data["discount"] = percent
                found = True

        if not found:
            raise ValueError("Product was not found")

    def sell_product(self, product_name, amount):
        if product_name not in self.products:
            raise ValueError("Product was not found")

        if amount <= 0:
            raise ValueError("Amount must be greater than zero")

        product_data = self.products[product_name]

        if product_data["amount"] < amount:
            raise ValueError("Not enough products in the store")

        product = product_data["product"]
        discount = product_data["discount"]
        final_price = product.price - product.price * discount / 100

        product_data["amount"] -= amount
        self.income += final_price * amount

    def get_income(self):
        return self.income

    def get_all_products(self):
        return [
            {
                "type": product_data["product"].type,
                "name": product_data["product"].name,
                "price": product_data["product"].price,
                "amount": product_data["amount"],
                "discount": product_data["discount"],
            }
            for product_data in self.products.values()
        ]

    def get_product_info(self, product_name):
        if product_name not in self.products:
            raise ValueError("Product was not found")

        return product_name, self.products[product_name]["amount"]


p = Product("Sport", "Football T-Shirt", 100)
p2 = Product("Food", "Ramen", 1.5)

s = ProductStore()
s.add(p, 10)
s.add(p2, 300)
s.sell_product("Ramen", 10)

assert s.get_product_info("Ramen") == ("Ramen", 290)

print("All assertions passed")
