import mysql
from mysql import connector
import json
import bcrypt
from random import randint
from time import sleep
import LoggedInUser
import secrets

# Make a json file named sqlconfig.txt, it will have these values
#  
# user = username, database = insert database name here
# sslkey = key file name here
# sslca = sslcafile
# ssl_verify_identity = True, 
# port = portnumber here, password = passw here 
# ssl_verify_cert = True
indices = {"salt":3, "userid":0, "balance":1, "password":2, "username":4, "ipaddress":8, "sessionID":7}
globalSalt = bytes("$2b$12$k/eapMysPreNEADLRybj3O", 'utf-8')
class SqlHandler:
    conn = None 
    config = None
    def __init__(self, file = 'sqlconfig.txt'): 
        self.__setConfigData__(open(file))
        self.conn = mysql.connector.connect(**self.config)
        self.conn.autocommit = True

    def __setConfigData__(self, f):
        self.config = json.load(f)

    def register(self, username, password, ipaddress):
        ''' 
            1) check if username already exists, if it does throw exception
            2) if not, generate salt
            3) add salt to password
            4) hash password
            5) add username, hashed password, non-hashed ip to database
            6) create session for this user, return user object by using getUserByCookie
        '''
        ######## Bullet point 1 #########
        rows = self.__getUsername__(username)
        if rows is not None:
            raise Exception('Username already exists')
        
        ######## Bullet point 2 #########
        salt = str(bcrypt.gensalt(), "utf-8")
        ######## Bullet point 3 and 4 #########
        print(password)
        print(type(password))
        print(salt)
        print(type(salt))
        hashedpw = bcrypt.hashpw(bytes(password, 'utf-8'), bytes(salt, 'utf-8'))
        print('password hashed')
        ######## Bullet point 5 #########
        try:
            self.__addUser__(username, hashedpw, salt, ipaddress)
        except Exception as identifier:
            print('Could not add user due to a sql issue')
            print(identifier)
            raise Exception('Sql error, please check the connection')
        
        ######## Bullet point 6 #########
        hashedCookieID = self.__createSession__(username, ipaddress)
        print('session created')
        return self.getUserByCookie(hashedCookieID, ipaddress)

        

    
    def login(self, username, password, ipaddress):
        ''' 
            0) delay a small, random amount of time
            1) check if username already exists, if not, throw exception
            2) if it does, get the user's salt
                hashed_password = rows[0] 
            3) add salt to password
            4) hash password
            5) check that the two hashes match, if not, throw exception
               check_match = bcrypt.checkpw(password, hashed_password)
            6) create session for this user, return user object by using getUserByCookie
        '''
        ######## Bullet point 0 and 1 #########
        sleep(0.001 * randint(10,100))
        rows = self.__getUsername__(username)
        if rows is None:
            raise Exception('Invalid Login')
        print(rows)
        ######## Bullet point 2 #########
        salt = rows[indices['salt']]

        ######## Bullet point 3, 4, and 5 #########
        hashedattempt = str(bcrypt.hashpw(password.encode('utf-8'), salt.encode('utf-8')))[2:-1]
        hashedpw = rows[indices['password']]
        print(hashedpw)
        print(hashedattempt)
        print(bcrypt.checkpw(hashedpw.encode('utf-8'), hashedattempt.encode('utf-8')))
        if hashedpw != hashedattempt:
            raise Exception('Invalid Login')
        
        ######## Bullet point 6 #########
        self.conn.cursor().execute("UPDATE user SET sessionID = NULL WHERE ipaddress = %s", [ipaddress])
        self.conn.cursor().execute("UPDATE user SET ipaddress = NULL WHERE ipaddress = %s", [ipaddress])
        hashedCookieID = self.__createSession__(username, ipaddress)
        return self.getUserByCookie(hashedCookieID, ipaddress)


    
    def changeBalance(self, user, amountToChangeBy):
        '''
            1) Authenticate by User, if the user is not logged in, an exception will be thrown
            2) Change the balance
            3) Get new balance and set the user object's balance to the new balance
        '''
        self.authenticateByUserObject(user)
        curr = self.conn.cursor()
        curr.execute("UPDATE user SET balance = (balance + %s) WHERE username = %s", (amountToChangeBy, user.username))
        curr.execute("SELECT balance FROM user WHERE username = %s", [user.username])
        rows = curr.fetchone()
        user.balance = float(rows[0])
        return
    
    def getBalance(self, user):
        '''
            Sets the new balance of the user in the user object
        '''
        self.changeBalance(user, 0)
        return

    def logout(self, user):
        '''
            1) Authenticate by User, if the user is not logged in, an exception will be thrown
            2) Delete the session id and ip address from the database
        '''
        self.authenticateByUserObject(user)
        self.conn.cursor().execute("UPDATE user SET sessionID = NULL WHERE username = %s", [user.username])
        return
    
    def authenticateByUserObject(self, user):
        '''
            1) Get the user object's hashed cookie value and ip address
            2) Compare this value to the hashed session id and ip address in the database for this username
            3) if they are equal, the user is logged in, otherwise throw an exception
        '''
        print('authenticating now')
        sid = user.sessionID
        ipaddr = user.ipaddress
        # hashedsid = bcrypt.hashpw(str(sid).encode('utf-8'), globalSalt)

        rows = self.__getUsername__(user.username)
        #checksid = bcrypt.hashpw(str(rows[indices['sessionID']]).encode('utf-8'), globalSalt)
        checksid = str(rows[indices['sessionID']])
        checkip = str(rows[indices['ipaddress']])

        print (checksid)
        print(checkip)
        print(sid)
        print(ipaddr)
        if checksid is None:
            raise Exception('Not logged in')
        if checkip is None: 
            raise Exception('Not logged in')

        if checksid != sid:
            raise Exception('Not logged in')
        if checkip != ipaddr: 
            raise Exception('Not logged in')

    def deleteUser(self, cookie, ipaddress):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM user WHERE ipaddress = %s", [ipaddress])
        rows = cur.fetchall()
        for row in rows:
            if row[indices['sessionID']] == cookie:
                cur.execute("DELETE FROM user WHERE ipaddress = %s AND sessionID = %s", (ipaddress, row[indices['sessionID']])) 
        
    
    def getUserByCookie(self, stringInsideCookie, ipaddress):
        '''
            1) Get rows by non-hashed ip address
            2) See if any of these rows have the hashed session id
            3) If there is no such row, throw an exception
            4) Return a user object with all the info
        '''
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM user WHERE ipaddress = %s", [ipaddress])
        rows = cur.fetchall()
        print('we are here now')
        for row in rows:
            #if bcrypt.hashpw(str(row[7])[2:-1].encode('utf-8'), globalSalt) == str(stringInsideCookie)[2:-1]:
            if row[7] is None:
                continue
            elif row[7] == 'NULL':
                continue
            elif str(stringInsideCookie) == row[7]:
                return self.parse(self.__getUserID__(row[4]))

        
    def __createSession__(self, username, ipaddress):
        '''
            This function is not to be called directly ever
            1) Generate some random session id
            2) Store the non-hashed id along with the ip address in the database by username
            3) Return the hashed session id, this will be our cookie
        '''
        salt = bcrypt.gensalt(10)
        curr = self.conn.cursor()
        curr.execute("UPDATE user SET sessionID = %s WHERE username = %s", (str(salt).encode('utf-8'), username))
        curr.execute("UPDATE user SET ipaddress = %s WHERE username = %s", (ipaddress, username))
        return salt


    def __getUsername__(self, username):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM user WHERE username = %s", [username])
        rows = cur.fetchone()
        cur.close()
        return rows
    
    def __getUserID__(self, username):
        print('get user id')
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM user WHERE username = %s", [username])
        rows = cur.fetchone()
        cur.close()
        return rows
    
    def __generateSalt__(self):
        saltRounds = 12
        return bcrypt.gensalt(saltRounds)

    def __addUser__(self, username, hashedpw, salt, ipaddress):
        self.conn.cursor().execute("INSERT INTO user(username, password, ipaddress, salt, balance) VALUES (%s,%s,%s,%s, 0)", (username, hashedpw, ipaddress, salt))
    
    def parse(self, row):
        print('in parse rn')
        user = LoggedInUser.LoggedInUser(row[indices['sessionID']], row[indices['username']], row[indices['balance']], row[indices['ipaddress']])
        return user
