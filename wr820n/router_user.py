from .router_exceptions import BadUserData


class RouterUser:
    """Class stored information about router user"""

    def __init__(self, info: dict):
        """Router user constructor
        Args:
            info (dict): dictionary of user info
        """
        try:
            self.ip = info.get('ip')
            self.mac = info.get('mac')
            self.bind_entry = int(info.get('bindEntry'))
            self.sta_mgt_entry = int(info.get('staMgtEntry'))
            self.type = int(info.get('type'))
            self.online = bool(int(info.get('online')))
            self.blocked = bool(int(info.get('blocked')))
            self.up_speed = int(info.get('up'))
            self.down_speed = int(info.get('down'))
            self.up_speed_limit = int(info.get('upLimit'))
            self.down_speed_limit = int(info.get('downLimit'))
            self.name = info.get('name')
        except:
            raise BadUserData("Can not create RouterUser")

    def __str__(self):
        return f"{'on-line' if self.online else 'off-line'} {self.name} ({self.mac})"
