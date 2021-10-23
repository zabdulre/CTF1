class LoggedInUser:
    username = None
    balance = 0
    sessionID = None
    ipaddress = None

    def __init__(self, hashedCookieVal, username, balance, ipaddress):
        self.username = username
        self.balance = balance
        self.ipaddress = ipaddress
        self.sessionID = hashedCookieVal