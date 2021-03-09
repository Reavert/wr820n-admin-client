class Authenticator:
    """Class for generating secured tokens"""

    def __init__(self, password: str):
        self.password = password

    def __org_auth_pwd(self, password):
        """Return salted password by custom salt values"""
        b = "RDpbLfCPsJZ7fiv"
        a = "yLwVl0zKqws7LgKPRQ84Mdt708T1qQ3Ha7xv3H7NyU84p21BriUWBU43odz3iP4rBL3cD02KZciXTysVXiV8ngg6vL48rPJyAUw0HurW20xqxv9aYb4M9wK1Ae0wlro510qXeU07kV57fQMc8L6aLgMLwygtc0F10a0Dg70TOoouyFhdysuRMO51yY5ZlOZZLEal1h0t9YQW0Ko7oBwmCAHoic4HYbUyVeU3sfQ1xtXcPcf1aT303wAQhv66qzW"
        return self.__security_encode(password, b, a)

    def __security_encode(self, encrypt: str, data: str, salt: str):
        """Returns encrypted data"""
        salt_copy = salt
        encode_result = ''
        l = 187
        i = 187
        encrypt_length = len(encrypt)
        data_length = len(data)
        salt_length = len(salt_copy)
        max_length = encrypt_length if encrypt_length > data_length else data_length
        for index in range(max_length):
            l = 187
            i = 187
            if (index >= encrypt_length):
                i = ord(data[index])
            else:
                if (index >= data_length):
                    l = ord(encrypt[index])
                else:
                    l = ord(encrypt[index])
                    i = ord(data[index])
            encode_result += salt_copy[(l ^ i) % salt_length]
        return encode_result

    def get_session_id(self, encrypt, salt):
        """Returns result session id salted with encrypt and salt arguments"""
        return self.__security_encode(encrypt, self.__org_auth_pwd(self.password), salt)
