import sqlite3


def create_db():
    # create a database for the app
    conn = sqlite3.connect('chatApp.db')
    cur = conn.cursor()
    # table that will hold information on all of the client
    cur.execute("""CREATE TABLE if not exists clients(
        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        username text NOT NULL, 
        hashed_passwd text NOT NULL,
        nickname text NOT NULL, 
        isConnected integer NOT NULL
        );
    """)

    # create the messages table
    cur.execute("""CREATE TABLE if not exists messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        sent_from INTEGER NOT NULL, 
        sent_to INTEGER NOT NULL,
        message text NOT NULL,
        sent_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # create the files table
    cur.execute("""CREATE TABLE if not exists files(
        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        filename text NOT NULL
        );
    """)

    conn.commit()
    conn.close()


def update_status_db(username: str, status: int):
    conn = sqlite3.connect('chatApp.db')
    cur = conn.cursor()
    # update the status in the db
    if status == 0:
        cur.execute("""UPDATE clients SET isConnected = 0 WHERE username= :username""", {"username": username})
    elif status == 1:
        cur.execute("""UPDATE clients SET isConnected = 1 WHERE username= :username""", {"username": username})
    conn.commit()
    conn.close()


def submit_to_db(username, hashed, nickname):
    conn = sqlite3.connect('chatApp.db')
    cur = conn.cursor()
    # table that will hold information on all of the client
    cur.execute(
        """INSERT OR IGNORE INTO clients (username, hashed_passwd, nickname, isConnected) VALUES (:username, 
        :hashed_passwd, :nickname, :isConnected)""",
        {'username': username,
         'hashed_passwd': hashed,
         'nickname': nickname,
         'isConnected': 1})
    conn.commit()
    conn.close()


# to table that will hold all the available files
def submit_file_to_db(filename):
    conn = sqlite3.connect('chatApp.db')
    cur = conn.cursor()
    file_list = get_file_list()
    if filename not in file_list:
        cur.execute(
            """INSERT OR IGNORE INTO files (filename) VALUES (:filename)""",
            {'filename': filename})
    conn.commit()
    conn.close()


def get_client_id(username):
    conn = sqlite3.connect('chatApp.db')
    cur = conn.cursor()
    cur.execute("""SELECT id FROM clients WHERE username= :username""", {'username': username})
    client_id = cur.fetchall()[0][0]
    return client_id


def get_clients_list():
    conn = sqlite3.connect('chatApp.db')
    cur = conn.cursor()
    cur.execute("""SELECT username FROM clients""")
    clients = [item[0] for item in cur.fetchall()]
    return clients


def get_online_clients():
    conn = sqlite3.connect('chatApp.db')
    cur = conn.cursor()
    cur.execute("""SELECT username FROM clients WHERE isConnected=1""")
    clients = [item[0] for item in cur.fetchall()]
    return clients


def log_message(sender, receiver, message, time):
    conn = sqlite3.connect('chatApp.db')
    cur = conn.cursor()
    cur.execute(
        """INSERT OR IGNORE INTO messages (sent_from, sent_to, message, sent_at) VALUES (:sent_from, :sent_to, 
        :message, :sent_at)""",
        {'sent_from': sender,
         'sent_to': receiver,
         'message': message,
         'sent_at': time})
    conn.commit()
    conn.close()


def disconnect_all():
    conn = sqlite3.connect('chatApp.db')
    cur = conn.cursor()
    # update the status in the db
    cur.execute("""UPDATE clients SET isConnected = 0""")
    conn.commit()
    conn.close()


def remove_file(filename):
    conn = sqlite3.connect('chatApp.db')
    cur = conn.cursor()
    file_list = get_file_list()
    if filename in file_list:
        cur.execute(
            """DELETE FROM files WHERE filename= :filename""",
            {'filename': filename})
    conn.commit()
    conn.close()


def get_file_list():
    conn = sqlite3.connect('chatApp.db')
    cur = conn.cursor()
    cur.execute("""SELECT filename FROM files""")
    filenames = [item[0] for item in cur.fetchall()]
    return filenames


def file_list_str(file_list):
    s = '\n'
    for file in file_list:
        s += file + '\n'
    return s

