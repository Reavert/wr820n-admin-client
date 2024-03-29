import urllib.parse

from .block import Block
from .authenticator import Authenticator
from .tddp_command import TDDPCommand as TDDP
from .router_exceptions import *
from .router_user import RouterUser
import requests


class Router:
    """Class for router management by HTTP.
    Args:
        url (str): ip or domain name of router
        password (str): pass key to access to admin panel
        timeout (int, optional): Timeout of requests. Defaults to 3.
        """
    # Here are the manually found state codes
    # Perhaps the names of the variables do not match the state code
    STATE_UNKNOWN = -1
    STATE_INITIALIZED = 4
    STATE_STARTUP = 5

    __cmd_prefix = 'main staMgt -add'
    __default_auth_key = 'WaQ7xbhc9TefbwK'

    def __init__(self, url: str, password: str, timeout=3):
        """Router constructor"""
        self.url = url
        self.authenticator = Authenticator(password)
        self.state = Router.STATE_UNKNOWN
        self.encrypt_arg = ''
        self.salt_arg = ''
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
        """Returns user's info by MAC-address
        Args:
            mac (str): mac-address of user
        Returns:
            RouterUser: user's info
        """
        total_users = self.get_users()
        for user in total_users:
            if mac.lower() == user.mac.lower():
                return user
        return None

    def get_user_by_name(self, name: str):
        """
        Returns user's info by MAC-address
        Args:
            name (str): name of user
        Returns:
            RouterUser: user's info
        """
        total_users = self.get_users()
        for user in total_users:
            if name == user.name:
                return user
        return None

    def get_online_users(self):
        """
        Returns online users
        Returns:
            list of RouterUser: list of online users
        """
        total_users = self.get_users()
        online_users = list()
        for user in total_users:
            if user.online:
                online_users.append(user)
        return online_users

    def get_users(self):
        """Returns tuple of users."""
        info = self.read([Block.STARTTABLE_DATA_ID])
        params = list(info.items())[1:]
        users_info = {}
        users = []
        for key, value in params:
            for user_id in value:
                param_value = value[user_id]
                if user_id not in users_info:
                    users_info[user_id] = {}
                users_info[user_id][key] = param_value
        for user_id, info in users_info.items():
            users.append(RouterUser(info))
        return tuple(users)

    def get_peer_mac(self):
        """Gets peer's mac"""
        self.__try_request(TDDP.TDDP_GETPEERMAC, TDDP.SYN)
        peer_mac = self.response.text.split('\r\n')[1]
        return peer_mac

    def write(self, block_id, **parameters):
        """
        Writes data to specific block
        Args:
            block_id (int): block id where to set parameters
            **parameters: custom values of chosen block
        """
        data = f"id {block_id}\r\n"
        for key, value in parameters.items():
            if type(value) is dict:
                for v_key, v_value in value.items():
                    data += f"{key} {v_key} {v_value}\r\n"
            else:
                data += f"{key} {value}\r\n"
        self.__try_request(TDDP.TDDP_WRITE, TDDP.ASYN, data)

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
                    result[key][index] = value
                else:
                    result[key] = {index: value}
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
        """Generates session id via authenticator and store it in self.session_id
        Raises:
            IncorrectResponseFormatException: can not parse response
        """
        self.session_id = self.authenticator.get_session_id(
            self.encrypt_arg, self.salt_arg)

    def __get_auth_info(self):
        """Parse auth-response values.
        Raises:
            IncorrectResponseFormatException: can not get auth response values
        """
        response_values = self.response.text.split('\r\n')
        try:
            self.state = int(response_values[1])
            self.login_attempts = int(response_values[2])
            self.encrypt_arg = response_values[3]
            self.salt_arg = response_values[4]
        except IndexError:
            raise IncorrectResponseFormatException()

    def update_auth_info(self):
        """Updates (sync) class instance by previous auth-response"""
        self.__get_auth_info()
        self.__generate_session_id()

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
                self.update_auth_info()
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
