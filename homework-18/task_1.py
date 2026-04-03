class Email:
    def __init__(self, email):
        self.validate = email

    @property
    def validate(self):
        return self._validate

    @validate.setter
    def validate(self, value):
        if self._is_valid_email(value):
            self._validate = value

        else:
            raise ValueError(f'Невірний формат email: {value}')

    @staticmethod
    def _is_valid_email(email):
        if '@' not in email:
            return False

        local, domain = email.split('@',1)
        if not local or not domain:
            return False

        if '.' not in domain:
            return False

        if email.startswith('.') or email.endswith('.'):
            return False

        return True