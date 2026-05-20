class EmailValid:

    def __init__(self, em):
        self.validate(em)
        self.em = em

    @staticmethod
    def validate(em):
        valid_chars = '1234567890qwertyuiopasdfghjklzxcvbnm@-_.'
        if len(em) > 64 or  (em[0] in '@-_.') or (em[len(em) - 1] in '@-_.') or ('@' not in em) or em.count('@') != 1:
            print(f'Email is Invalid!')
            return False
        i = 0
        while i < len(em):
            if em[i].lower() not in valid_chars:
                print(f'Email is Invalid!')
                return False
            elif em[i] == '@':
                if (em[i - 1] in '@-_.') or (em[i + 1] in '@-_.') or '.' not in em[i + 1: len(em) - 1]:
                    print(f'Email is Invalid!')
                    return False
            i += 1
        print(f'Email is Valid!')
        return True


e1 = EmailValid('GHJJK.KH-HGsg@gmail.com')
e2 = EmailValid('hfjhg@f.hf-')