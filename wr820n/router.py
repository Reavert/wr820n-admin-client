import urllib.parse

from .authenticator import Authenticator
from .tddp_command import TDDPCommand as TDDP
from .router_exceptions import *
from .router_user import RouterUser
import requests


class Router:
    """Class for router managment by HTTP.   
    Args:
        url (str): ip or domain name of router
        password (str): pass key to access to admin panel
        timeout (int, optional): Timeout of requests. Defaults to 3.
        """

    __cmd_prefix = 'main staMgt -add'
    __default_auth_key = 'WaQ7xbhc9TefbwK'

    def __init__(self, url: str, password: str, timeout=3):
        """Router constructor"""
        self.url = url
        self.authenticator = Authenticator(password)
        self.__salt1 = ''
        self.__salt2 = ''
        self.session_id = ''
        self.response = requests.Response()
        self.timeout = timeout

    def instruction(self, cmd: str):
        """Sends instruction to router with custom command.
        Args:
            cmd (str): custom command to send
        """
        self.__try_request(TDDP.TDDP_INSTRUCT, TDDP.SYN, cmd)

    def logout(self):
        """Sends logout command to router."""
        self.__try_request(TDDP.TDDP_LOGOUT, TDDP.SYN)

    def change_user(self, user: RouterUser, **kwargs):
        """Changes user info
        Args:
            user (RouterUser): user's info
        Keyword args:
            name (str, optional): using for changing name of user
            upload (int, optional): using for changing upload speed limit of user
            download (int, optional): using for changing download speed limit of user
        """
        new_name = kwargs.get('name', user.name)
        new_upload_limit = kwargs.get('upload', user.up_speed_limit)
        new_download_limit = kwargs.get('download', user.down_speed_limit)

        cmd = f"{Router.__cmd_prefix} mac:{user.mac} name:{new_name} upload:{new_upload_limit * 1024} download:{new_download_limit * 1024}"
        self.instruction(cmd)

    def get_user_by_mac(self, mac: str):
        """Return user's info by MAC-address
        Args:
            mac (str): mac-address of user
        Returns:
            RouterUser: user's info
        """
        total_users = self.get_users()
        for user in total_users:
            if mac == user.mac:
                return user
        return None

    def get_users(self):
        """Returns tuple of users."""
        # TODO: Replace magic number
        info = self.read([13])
        params = info.split('\r\n')[2:]
        users_info = {}
        users = []
        for p in params:
            key_id_value = p.split(' ')
            if len(key_id_value) == 3:
                key = key_id_value[0]
                user_id = int(key_id_value[1])
                value = key_id_value[2]
                if user_id not in users_info:
                    users_info[user_id] = {}
                users_info[user_id][key] = value
        for user_id in users_info:
            users.append(RouterUser(users_info[user_id]))
        return tuple(users)

    def read(self, blocks):
        """Reads router data from specific blocks
        Args:
            blocks (list): list of block's numbers
        Returns:
            dict: parameters stored in blocks
        """
        if not blocks:
            return []
        result = {}
        cmd = ''
        for n in blocks:
            cmd += str(n)
            if not n == blocks[-1]:
                cmd += '#'
        self.__try_request(TDDP.TDDP_READ, TDDP.ASYN, cmd)
        lines = self.response.text.split('\r\n')
        for line in lines:
            temp = line.split(' ')
            if len(temp) == 2:
                key = temp[0]
                value = urllib.parse.unquote(temp[1])
                result[key] = value
            elif len(temp) == 3:
                key = temp[0]
                index = int(temp[1])
                value = urllib.parse.unquote(temp[2])
                if key in result:
                    result[key] += [[index, value]]
                else:
                    result[key] = [[index, value]]
        return result

    def reboot(self):
        """Reboots router"""
        self.__try_request(TDDP.TDDP_REBOOT, TDDP.ASYN)

    def reset(self, confirm=False):
        """Resets router settings. Be careful using this function
        Args:
            confirm (bool): confirm you action by passing True
        """
        if confirm:
            self.__try_request(TDDP.TDDP_RESET, TDDP.ASYN)

    def change_password(self, new_password):
        """Changes password of router admin-user
        Args:
            new_password (str): new password of the router
        """
        auth_key = self.authenticator.auth_key
        self.authenticator = Authenticator(new_password)
        params = {'code': TDDP.TDDP_CHGPWD, 'asyn': TDDP.SYN, 'auth': auth_key}
        self.response = requests.post(
            url=self.url,
            params=params,
            data=self.authenticator.auth_key,
            headers={'Content-Type': 'text/html'},
            timeout=self.timeout)

    def auth(self):
        """Trying to send auth request to router.
        Raises:
            WrongPasswordException: can not connect to the router
        """
        try:
            self.__request(TDDP.TDDP_AUTH, TDDP.SYN)
        except UnauthorizedAccessException:
            raise WrongPasswordException('Wrong password')

    def __generate_session_id(self):
        """Generates session id via authenticator and store it in self.sesion_id
        Raises:
            IncorrectResponseFormatException: can not parse response
        """
        try:
            keys = self.__get_auth_response_keys(
                self.__parse_auth_response(self.response.text))
        except IncorrectResponseFormatException:
            raise IncorrectResponseFormatException(
                'Incorrect response format received')

        self.session_id = self.authenticator.get_session_id(
            keys[0], keys[1])

    def __parse_auth_response(self, response: str):
        """Separates response values.
        Args:
            response (str): response data, where stored auth data
        Returns:
            [type]: [description]
        """
        return response.split('\r\n')

    def __get_auth_response_keys(self, response_values):
        """Find out the auth-encrypt keys in auth response.
        Args:
            response_values (dict): dictionary of auth-response
        Raises:
            IncorrectResponseFormatException: can not get auth response keys
        Returns:
            dict: dictionary of two auth-elements (first: encrypt, second: salt)
        """
        try:
            encrypt_arg = response_values[3]
            salt_arg = response_values[4]
        except IndexError:
            raise IncorrectResponseFormatException(
                'Encrypt and salt haven\'t been received')
        return [encrypt_arg, salt_arg]

    def __try_request(self, code: int, asyn: int, payload=''):
        """Trying to send custom router request
        Args:
            code (int): custom TDDP-command code
            asyn (int): TDDP.SYN(0) or TDDP.ASYN(1)
            payload (str, optional): custom request payload. Defaults to ''.
        Raises:
            RequestException: request exception via authorization fail
        """
        try:
            self.__request(code, asyn, payload)
        except UnauthorizedAccessException:
            try:
                self.__generate_session_id()
                self.auth()
                self.__request(code, asyn, payload)
            except UnauthorizedAccessException:
                raise RequestException('Unable to auth')

    def __request(self, code: int, asyn: int, payload=''):
        """Sends custom HTTP payload to router.
        Args:
            code (int): custom TDDP-command code
            asyn (int): TDDP.SYN or TDDP.ASYN
            payload (str, optional): custom request payload. Defaults to ''.
        Raises:
            UnauthorizedAccessException: got incorrect session id
        """
        params = {'code': code, 'asyn': asyn, 'id': self.session_id}
        self.response = requests.post(
            url=self.url,
            params=params,
            data=payload,
            headers={'Content-Type': 'text/html'},
            timeout=self.timeout)

        if self.response.status_code == 401:
            raise UnauthorizedAccessException('Incorrect session id')
