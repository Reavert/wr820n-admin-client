import wr820n


router_url = 'http://192.168.0.1'
router_password = 'your_password'
specific_user_mac = '01-01-01-01-01-01'

if __name__ == '__main__':
    # Connecting to router
    client = wr820n.Router(router_url, router_password)

    # Receiving tuple of users
    users = client.get_users()

    # Shows list of all discovered users
    print("Users list: ")
    for user in users:
        print(user)

    # Get info about specific character
    specific_user = client.get_user_by_mac(specific_user_mac)

    # Check specific user's existence 
    if specific_user:
        # Set specific user's upload and download speedlimit to 16 KB/s
        client.change_user(specific_user, upload=16, download=16)

        # Remove speedlimit of specific user
        client.change_user(specific_user, upload=0, download=0)

    # Logout from router
    client.logout()
