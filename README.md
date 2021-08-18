# TP-Link WR820N Admin client
*This set of python scripts provides the ability to manage the router model of TP-Link WR820N*

***NOTE: In current version most of the features provided by the router are not implemented.***

***
## Current features: 
- User's managment;
    - Set upload speed limit;
    - Set download speed limit;
    - Set user's name;
- Receiving user data;
- Rebooting router;
- Resetting router;
- Changing password;

## Requirements 
General dependencies is presented in *requirements.txt*
```txt
certifi==2020.12.5
chardet==4.0.0
idna==2.10
requests==2.25.1
urllib3==1.26.3
```
## Example
The basic functionality is presented in *example.py*
```py
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

    # Get info about specific user
    specific_user = client.get_user_by_mac(specific_user_mac)

    # Check specific user's existence 
    if specific_user:
        # Set specific user's upload and download speedlimit to 16 KB/s
        client.change_user(specific_user, upload=16, download=16)

        # Remove speedlimit of specific user
        client.change_user(specific_user, upload=0, download=0)

    # Logout from router
    client.logout()
```
