import datetime
import socket
import struct
import threading
import sqlite3
import time
from db_util import *
# from werkzeug.security import check_password_hash, generate_password_hash
from window import Window
from util import *
import os
import copy

"""
basic messaging server for cmd, without any fancy protocols
"""

ENCODING = 'utf-8'
HOST = '127.0.0.1'
PORT = 50004
SENDER_PORT = 50001
RECEIVE_PORT = 50002
# initialize database if not exist
create_db()

# here you can add all the available files to the database
submit_file_to_db('lama.png')
submit_file_to_db('hello.txt')
submit_file_to_db('mov.mp4')

hello_file = load_file('hello.txt')
lama_file = load_file('lama.png')
mov_file = load_file('mov.mp4')
file_dict = {'lama.png': lama_file,'hello.txt': hello_file,'mov.mp4': mov_file}
# printsockett(len(mov_file))


# creating the TCP socket and binding it.
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try:
    server.bind((HOST, PORT))
except:
    print("Error binding the socket!")
server.listen(15)

clientsList = []
nicknames = []  # nickname to display - not used for now
usernames = []


# broadcasting incoming messaging to all clients
def broadcast(client, username, message):
    senderID = get_client_id(username)
    disassemble = message.decode(ENCODING).split(' ')
    if disassemble[1] == '/to':
        receiver = disassemble[2]
        receiverID = get_client_id(receiver)
        if receiver in usernames:
            reconstruct = f'{disassemble[0]} ' + ' '.join(disassemble[3:])
            index = usernames.index(receiver)
            try:
                clientsList[index].send(reconstruct.encode(ENCODING))
                try:
                    s = ' '.join(map(str, disassemble[3:]))
                    log_message(senderID, receiverID, s, datetime.datetime.now())
                except:
                    print('logging message unsuccessful (1)')
            except:
                print(f'Unable to send to {receiver}')
        else:
            try:
                client.send("he's not here".encode(ENCODING))
            except:
                print('Unable to send')
    else:
        for client in clientsList:
            try:
                client.send(message)
            except:
                continue

        ''' log messages in the database, if the message is to everyone the receiver is 0'''
        try:
            if len(disassemble) > 2:
                if disassemble[2] == 'joined' or disassemble[2] == 'left':
                    s = ' '.join(map(str, disassemble))
                    log_message(senderID, 0, s, datetime.datetime.now())
                else:
                    s = ' '.join(map(str, disassemble[1:]))
                    log_message(senderID, 0, s, datetime.datetime.now())
            else:
                s = ' '.join(map(str, disassemble[1:]))
                log_message(senderID, 0, s, datetime.datetime.now())
        except:
            print('logging message unsuccessful (2)')


def logout(client):
    index = clientsList.index(client)
    clientsList.remove(client)
    # nickname = nicknames[index]
    username = usernames[index]
    usernames.remove(username)
    try:
        client.send("DISCONNECTED".encode(ENCODING))  # sending to the client
        client.close()
        broadcast(client, username, f"{username} has left the chat!\n".encode(ENCODING))
    except:
        client.close()
        update_status_db(username, 0)

    # update the database that this client in now offline
    update_status_db(username, 0)


def send_file(client, file_name, c_addr, start_packt, username):
    # print(client.getpeername())
    try:
        file_size = os.path.getsize(file_name)
    except:
        print("file doesn't exsit." )
        return
    file_list_cpy = copy.deepcopy(file_dict[file_name])
    num_of_pckts = len(file_list_cpy)
    stop_on = int(num_of_pckts/2)
    LEN = 0  # Length of datagram, initialize it to 0
    CHECKSUM = 0  # Not used, 0 is a dummy value
    header_length = 18
    data_length = 1024  # Length of payload in bytes
    window_size = 3  # Size of the window
    timeout_flag = False
    last_max_win = 3
    timeout = 3  # Time out in seconds

    head_SEQ = start_packt  # Head sequence number of queue
    SEQ = 0
    last_SEQ = -1  # SEQ of last datagram, stays at -1 until iteration is known
    fseq = 0
    num_timeouts = 0  # Number of timeouts
    timeout_SEQ = []  # SEQs that have timed-out (time-outed?)

    while True:

        try:

            file_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Create socket
            data = f'syn {num_of_pckts}'.encode(ENCODING)
            send_datagram(file_sock, c_addr[0], SENDER_PORT, c_addr[1], LEN, CHECKSUM, SEQ, window_size, data, 'syn')
            file_sock.settimeout(3)
            # print(c_addr)
            Ack, addr = file_sock.recvfrom(1024)
            check = Ack[header_length:]
            # print(check)
            # print(addr)
            # print(c_addr)
            if check == b'syn-ack' and addr == c_addr:
                data = b'ack'
                send_datagram(file_sock, c_addr[0], SENDER_PORT, c_addr[1], LEN, CHECKSUM, SEQ, window_size, data, 'ack')
                break
        except socket.timeout:
            print('Timedout!!!, handshake unsuccessful.')
            continue
        except:
            print('something went wrong.')
            logging.debug("An exception was thrown!", exc_info=True)
            logging.info("An exception was thrown!", exc_info=True)
            logging.warning("An exception was thrown!", exc_info=True)
            continue


    window = {}  # Initialize the queue

    resend_window = []  # Initialize the queue
    ACKed_list = []  # for DUP ACKs
    timeout_check = []
    dup_list = []

    s = start_packt
    # start to send
    print('start sending...')
    # as long as there is more to read from the file
    while True:
        i = 0
        # filling the sending window
        while len(window) < window_size:
            if len(resend_window) > 0:
                keys_list = list(resend_window.keys())
                window.update({keys_list[0]:resend_window.pop(keys_list[0])})

                SEQ = keys_list[0]
            else:
                window.update(file_list_cpy[s])
                SEQ = s
                if s < len(file_list_cpy) - 1:
                    s += 1

            # if the file is done
            if s == len(file_list_cpy) - 1:
                last_SEQ = s
                print(f'final seq: {last_SEQ}')
                break
            print(f'buffered seq: {SEQ}')

        # actually send stuff
        # loops on the datagrams that in the window
        for key in window:
            # if we didn't recieved an ACk for i yet, do:
            if not window[key][1]:
                SEQ = key  # current seq
                data = window[key][0]  # current data
                LEN = len(data) + header_length

                if SEQ == last_SEQ:
                    LEN = -1
                send_datagram(file_sock, c_addr[0], SENDER_PORT, c_addr[1], LEN, CHECKSUM, SEQ, window_size, data, 'SEQ')
                timeout_check.append(SEQ)
                # if reached end of file
                if SEQ == last_SEQ:
                    # file.close()
                    break

        # start excepting ACKs
        print('waiting for ACKs...')

        file_sock.setblocking(0)

        # setting up a timer for ACK timeout
        when_to_timeout = datetime.timedelta(0, timeout)  # the delta between now and the timeout we set
        start_time = datetime.datetime.now()  # Start the timer

        # while the window is not empty
        count = 0
        while len(window) > 0:
            if datetime.datetime.now() > start_time + when_to_timeout and len(timeout_check) > 0:
                num_timeouts += 1
                timeout_SEQ.append(timeout_check[0])
                # print(f'timeout seq: {timeout_check[0]}')
                timeout_flag = True
                if len(resend_window) == 0:
                    resend_window = resend_util(window)
                else:
                    resend_window = resend_append_util(window, resend_window)
                window_size = 1
                window = {}
                timeout_check.clear()
                break  # need to break in order to start sending again, in other word, timeout = catastrophe
            # if not timeout, try to receive ACK
            else:
                try:
                    response, add = file_sock.recvfrom(64)
                    if response == -1:
                        continue
                except:
                    time.sleep(1)

            # taking the ACK header apart
            try:
                pop_header = response[:header_length]  # Isolate header (16)
            except:
                continue
            # pack format -> '!HHhHQH'' => (network/bigEndian,un_short,un_short,short,un_short,unsigned l l)
            try:
                header = struct.unpack('!HHhHQH', pop_header)  # Unpack header
            except:
                continue
            ACK = header[4]  # Get the SEQ from the header
            win = header[5]

            isDup = response[header_length:]
            # print(isDup)
            if isDup == b'FIN':
                data = f'User {username} downloaded 100% out of file. last byte is: {file_size}'.encode(ENCODING)
                send_datagram(file_sock, c_addr[0], SENDER_PORT, c_addr[1], LEN, CHECKSUM, SEQ, window_size, data, 'FIN')
                file_sock.close()
                dup_list.clear()
                ACKed_list.clear()
                timeout_check.clear()
                s = 0
                return
            if isDup == b'Stop':
                # data = f'Stop, User {username} downloaded 50% out of file. last byte is: {stop_on*data_length}\nsend con to continue.'.encode(ENCODING)
                # send_datagram(file_sock, c_addr[0], SENDER_PORT, c_addr[1], LEN, CHECKSUM, SEQ, window_size, data, 'Stop')
                # isDup = b''
                dup_list.clear()
                ACKed_list.clear()
                timeout_check.clear()
                file_sock.close()
                return
            if ACK in dup_list:
                break

            if ACK not in ACKed_list and isDup != b'DUP':
                ACKed_list.append(ACK)
                timeout_check.remove(ACK)
                print('Received ACK: ', ACK)
                window[ACK][1] = True  # Mark SEQ as ACKed
                count += 1
                if not timeout_flag and count >= window_size:
                    window_size += 1
                    window[ACK][1] = True
                    if last_max_win < window_size:
                        last_max_win = window_size
                elif timeout_flag and count >= window_size:
                    if window_size*2 <= int(last_max_win/2):
                        window_size *= 2
                        window[ACK][1] = True
                    else:
                        timeout_flag = False

            elif isDup == b'DUP' and ACK in window:
                response = b''
                print(f'DUP ACK: {ACK}')
                dup_list.append(ACK)
                window[ACK][1] = True
                if window_size > 1:
                    if len(resend_window) == 0:
                        resend_window = resend_util(window)
                    else:
                        resend_window = resend_append_util(window, resend_window)
                    window_size = int(window_size / 2)
                    window = {}
                    break

            # While not empty and head has been ACKed
            while len(window) > 0 and ACK in window:
                if window[ACK][1]:
                    window.pop(ACK)  # Dequeue the data
                    print('Popping SEQ: ', ACK)
                    
                    if (head_SEQ == last_SEQ):  # If last datagram
                        print('--------------------- FILE SENT ---------------------')
                        print('Number of timeouts: ', num_timeouts)
                        data = f'User {username} downloaded 100% out of file. last byte is: {file_size}'.encode(ENCODING)
                        send_datagram(file_sock, c_addr[0], SENDER_PORT, c_addr[1], LEN, CHECKSUM, SEQ, window_size, data, 'FIN')

                        file_sock.close()
                        dup_list.clear()
                        ACKed_list.clear()
                        timeout_check.clear()
                        s = 0
                        return
                    else:
                        head_SEQ += 1  # Move SEQ head to next number


# handle client messaging
def handle(client, addr, username):
    while True:
        # getting a message from the client and broadcasting it to all clients
        try:
            try:
                message = client.recv(1024)
            except ConnectionResetError:
                # print('hello')
                # client.send("DISCONNECTED".encode(ENCODING))  # sending to the client
                client.close()
                update_status_db(username, 0)
                usernames.remove(username)
                break

            # checking for commands
            if message.decode(ENCODING) == '/exit':
                logout(client)
                break
            disassemble = message.decode(ENCODING).split(' ')
            if disassemble[0] == '/file':
                print(disassemble)
                file_name = disassemble[1]
                port = int(disassemble[2])
                start_packt = int(disassemble[3])
                c_addr = (addr[0], port)
                thread = threading.Thread(target=send_file, args=(client, file_name, c_addr, start_packt, username))
                thread.start()
            elif disassemble[0] == '/fileslist':
                file_list = get_file_list()
                list_str = file_list_str(file_list)
                client.send(list_str.encode(ENCODING))
            elif disassemble[0] == '/clientslist':
                clients_list = get_clients_list()
                list_str = file_list_str(clients_list)
                client.send(list_str.encode(ENCODING))
            elif disassemble[0] == '/online':
                clients_list = get_online_clients()
                list_str = file_list_str(clients_list)
                client.send(list_str.encode(ENCODING))
            else:
                try:
                    if client in clientsList:
                        broadcast(client, username,
                                  f"{usernames[clientsList.index(client)]}: {message.decode(ENCODING)}".encode(
                                      ENCODING))
                except KeyboardInterrupt:
                    client.close()
                    update_status_db(username, 0)
                    usernames.remove(username)
                    break
                except ConnectionResetError:
                    client.close()
                    update_status_db(username, 0)
                    usernames.remove(username)
                    break
                except:

                    client.send("DISCONNECTED".encode(ENCODING))  # sending to the client
                    client.close()
                    update_status_db(username, 0)
                    continue
        # if the client not in the list/disconnected/crushed/etc..
        except KeyboardInterrupt:
            client.close()
            update_status_db(username, 0)
            usernames.remove(username)
            break
        except ConnectionResetError:
            # client.send("DISCONNECTED".encode(ENCODING))  # sending to the client
            client.close()
            update_status_db(username, 0)
            usernames.remove(username)
            break
        except:
            logging.debug("An exception was thrown!", exc_info=True)
            logging.info("An exception was thrown!", exc_info=True)
            logging.warning("An exception was thrown!", exc_info=True)
            client.send("DISCONNECTED".encode(ENCODING))  # sending to the client
            client.close()
            update_status_db(username, 0)
            break


def validate(client, username):
    conn = sqlite3.connect('chatApp.db')
    cur = conn.cursor()
    cur.execute("""SELECT username FROM clients""")
    names = cur.fetchall()
    flag = False
    for name in names:
        if name[0] == username:
            try:
                client.send("this username is taken, please enter a new one: ".encode(ENCODING))
                username = client.recv(1024).decode(ENCODING)
            except KeyboardInterrupt:
                client.close()
                update_status_db(username, 0)
                usernames.remove(username)
                break
            except ConnectionResetError:
                client.close()
                update_status_db(username, 0)
                usernames.remove(username)
                break
            except:
                client.send("DISCONNECTED".encode(ENCODING))  # sending to the client
                client.close()
                update_status_db(username, 0)
                break
            flag = True
            break
    if flag:
        validate(client, username)
    else:
        conn.close()
        return username


def register(client, address):
    try:
        client.send("USERNAME".encode(ENCODING))
        username = client.recv(1024).decode(ENCODING)
        username = validate(client, username)  # check if the name is taken

        client.send("PASSWD".encode(ENCODING))
        password = client.recv(1024).decode(ENCODING)

        # client.send("NICK".encode(ENCODING))
        # nickname = client.recv(1024).decode(ENCODING)
    except KeyboardInterrupt:
        client.close()
        return
    except ConnectionResetError:
        client.close()
        return
    except:
        client.send("DISCONNECTED".encode(ENCODING))  # sending to the client
        client.close()
        update_status_db(username, 0)
        return

    # hash the password
    # hashed = generate_password_hash(password)

    usernames.append(username)
    clientsList.append(client)

    print(f"{username} connected to the server")
    try:
        client.send("\nConnected to the server".encode(ENCODING))  # sending to the client
        broadcast(client, username,
                  f"{username} has joined the chat!".encode(ENCODING))  # sending to all of the clients
    except KeyboardInterrupt:
        client.close()
        update_status_db(username, 0)
        usernames.remove(username)
        return
    except ConnectionResetError:
        client.close()
        update_status_db(username, 0)
        usernames.remove(username)
        return
    except:
        client.send("DISCONNECTED".encode(ENCODING))  # sending to the client
        client.close()
        update_status_db(username, 0)
        return

    # submit to db
    submit_to_db(username, password, username)

    # each client gets it's own thread, the coma in the args is to make it a tuple
    thread = threading.Thread(target=handle, args=(client, address, username))
    # thread.daemon = True
    thread.start()


def login(client, address):
    try:
        try_count = 1
        client.send("USERNAME".encode(ENCODING))
        username = client.recv(1024).decode(ENCODING)
        client.send("PASSWD".encode(ENCODING))
        password = client.recv(1024).decode(ENCODING)
    except KeyboardInterrupt:
        client.close()
        return
    except ConnectionResetError:
        print('con error')
        client.close()
        return
    try:
        conn = sqlite3.connect('chatApp.db')
        cur = conn.cursor()
        cur.execute("""SELECT hashed_passwd, isConnected FROM clients WHERE username = :username""",
                    {"username": username})
        output = [item for item in cur.fetchall()]
        names = [item[0] for item in output]
        isCon = [item[1] for item in output]
        conn.close()
        if len(names) < 1:
            client.send(f"invalid username".encode(ENCODING))
            client.send("DISCONNECTED".encode(ENCODING))  # sending to the client
            client.close()
            update_status_db(username, 0)
            return
        elif isCon[0] == 1:
            client.send(f"user already connected from somewhere else".encode(ENCODING))
            client.send("DISCONNECTED".encode(ENCODING))  # sending to the client
            # update_status_db(username, 0)
            client.close()
            return

        while names[0] != password:
            if try_count < 3:
                client.send(
                    f"invalid password, please try again ({3 - try_count} trials left)".encode(ENCODING))
                try_count += 1
                password = client.recv(1024).decode(ENCODING)
            else:
                client.send("DISCONNECTED".encode(ENCODING))  # sending to the client
                client.close()
                update_status_db(username, 0)
                return

        # client.send("NICK".encode(ENCODING))
        # username = client.recv(1024).decode(ENCODING)
    except KeyboardInterrupt:
        client.close()
        update_status_db(username, 0)
        usernames.remove(username)
        return
    except ConnectionResetError:
        client.close()
        update_status_db(username, 0)
        usernames.remove(username)
        return
    # except:
    #     client.send("DISCONNECTED".encode(ENCODING))  # sending to the client
    #     client.close()
    #     update_status_db(username, 0)
    #     return

    usernames.append(username)
    clientsList.append(client)

    print(f"{username} connected to the server")
    try:
        client.send("\nConnected to the server".encode(ENCODING))  # sending to the client
        broadcast(client, username,
                  f"{username} has joined the chat!\n".encode(ENCODING))  # sending to all of the clients
    except KeyboardInterrupt:
        client.close()
        update_status_db(username, 0)
        usernames.remove(username)
        return
    except ConnectionResetError:
        client.close()
        update_status_db(username, 0)
        usernames.remove(username)
        return
    except Exception:
        print(Exception)
        client.send("DISCONNECTED".encode(ENCODING))  # sending to the client
        client.close()
        update_status_db(username, 0)
        return

    # update status in db
    update_status_db(username, 1)

    # each client gets it's own thread, the coma in the args is to make it a tuple
    thread = threading.Thread(target=handle, args=(client, address, username))
    # thread.daemon = True
    thread.start()


# receiving messages - run on the main thread
def receive():
    while True:
        try:
            try:
                client, address = server.accept()
            except:
                # clientsList.clear()
                # usernames.clear()
                disconnect_all()
                # print(usernames)
                break
            print(f"Got a connection from: {str(address)}")
            try:
                client.send("REG/LOG".encode(ENCODING))
                reg_or_log = client.recv(1024).decode(ENCODING)
            except:
                continue

            count = 0
            while True:
                if reg_or_log == 'login':
                    break
                if reg_or_log == 'register':
                    break
                count += 1
                if count >= 3:
                    break

                try:
                    client.send("REG/LOG".encode(ENCODING))
                    reg_or_log = client.recv(1024).decode(ENCODING)
                except:
                    continue

            if count == 3:
                try:
                    client.send("Unfortunately, you are a piece of shit, bye".encode(ENCODING))
                    client.send("DISCONNECTED".encode(ENCODING))  # sending to the client
                    client.close()
                except:
                    continue
            if reg_or_log == 'login':
                login(client, address)
            elif reg_or_log == 'register':
                register(client, address)
        except ConnectionError:
            print('hey')
            client.send("DISCONNECTED".encode(ENCODING))  # sending to the client
            client.close()
            clientsList.clear()
            usernames.clear()
            disconnect_all()
            server.close()
            break
    exit(0)


print("Server running...")
receive()
