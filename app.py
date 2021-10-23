import hashlib

from flask import Flask, request, jsonify, make_response
# from flask_mysqldb import MySQL
import uuid
from SqlHandler import SqlHandler as sql
app = Flask(__name__)
""" app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '1234'
app.config['MYSQL_DB'] = 'csci430'
app.config['MYSQL_HOST'] = 'localhost'
mysql = MySQL(app) """

@app.route('/register')
def register():
        # get the username and password
        username = str(request.args.get('username'))
        password = str(request.args.get('password'))
        ipaddress = request.remote_addr
        db = sql()
        # add mySQL stuff here
        """ cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM user WHERE username = %s", [username])
        rows = cur.fetchone()
        cur.close()
        if rows is not None:
                res = make_response("fail signing up")
                return res

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO user(password, username) VALUES (%s, %s)", (hashing(password), username))
        mysql.connection.commit()
        cur.close() """
        res = make_response("signup succeed")
        try:
                sessionId = request.cookies.get('cookie')
                ipaddress = request.remote_addr
                db.logout(db.getUserByCookie(sessionId, ipaddress))
        except Exception as e:
                print('user was not logged in initially')
        try:
                user = db.register(username, password, ipaddress)
                print(user)
                res.set_cookie('cookie', user.sessionID)  
        except Exception as e:
                print(e)
                res = make_response("signup failed")
        return res

@app.route('/login')
def login():
        # get the username and password
        username = str(request.args.get('username'))
        password = str(request.args.get('password'))
        ipaddress = request.remote_addr
        db = sql()
        # add mySQL stuff here
        # cur = mysql.connection.cursor()
        # cur.execute("SELECT * FROM user WHERE username = %s AND password = %s", (username, hash(password)))
        """         cur.execute("SELECT * FROM user WHERE password = %s", [hashing(password)])
        print(password,hashing(password))
        row = cur.fetchone()
        cur.close()
        print("row",row[0])
        if row is None:
                res = make_response("fail logging in")
                return res

        # serve the user a cookie
        res = make_response("logging in succeeds")
        sessionId = uuid.uuid4()

        res.set_cookie('auth_cookie', str(sessionId), max_age=60*30*6000)
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO sessions(session_id, user_id) VALUES (%s, %s)", (str(sessionId), row[0]))
        mysql.connection.commit()
        cur.close() """
        try:
                user = db.login(username, password, ipaddress)  
        except Exception as e:
                print(e)
                res = make_response("login failed")
                return res
        res = make_response("login succeed signed in as " + user.username)
        res.set_cookie('cookie', user.sessionID)
        return res

@app.route('/manage')
def manage():
        '''
        if not request.cookies.get('auth_cookie'):
                # return unauth
                pass
        else:
                # check auth
                pass
        # get the action and amount
        action = request.args.get('action')
        amount = request.args.get('amount')

        status_code = 200

        if (action == "deposit"):
                # add mySQL stuff here
                print("deposited $" + str(amount))
        elif (action == "withdraw"):
                # add mySQL stuff here
                print("withdrew $" + str(amount))
        elif (action == "balance"):
                # add mySQL stuff here
                print("balance=")
        elif (action == "close"):
                # add mySQL stuff here
                print("account closed")
        else:
                status_code = 400
        
        return jsonify({
                'Status': status_code,
                'Response': 'account action'
        })
        '''
        #need to add responses for each
        action = str(request.args.get('action'))
        cookie = str(request.cookies.get('cookie'))
        ipaddress = request.remote_addr
        db = sql()
        user = db.getUserByCookie(cookie, ipaddress)
        if user is None:
                return make_response('not logged in')
        print(user)
        if (action == 'close'):
                db.deleteUser(cookie, ipaddress)
                return make_response('user deleted')
        elif (action == 'withdraw'):
                amount = abs(float(request.args.get('amount')))
                db.getBalance(user)
                if (user.balance < amount):
                        resp = make_response('failed, insufficient balance')
                        return resp
                db.changeBalance(user, amount *-1)
        elif action == 'balance':
                db.changeBalance(user, 0)
        else:
                amount = abs(float(request.args.get('amount')))
                db.changeBalance(user, amount)
        return make_response("balance is " + str(user.balance))


@app.route('/logout')
def logout():
        # delete user cookie
        sessionId = request.cookies.get('cookie')
        ipaddress = request.remote_addr
        db = sql()
        db.logout(db.getUserByCookie(sessionId, ipaddress))
        '''
        print(request.cookies)
        print(sessionId)
        if sessionId is not None:
                cur = mysql.connection.cursor()
                cur.execute("DELETE FROM sessions WHERE session_id = %s", [str(sessionId)])
                mysql.connection.commit()
                cur.close()
        '''
        res = make_response("log out succeeds")
        return res

#context = ('cert.pem', 'key.pem')
#app.run(debug=False, ssl_context=context, host='localhost', port=80)
app.run(debug=False, host='localhost', port=80)

def hashing(password):
        return hashlib.md5(password.encode('utf-8')).hexdigest()