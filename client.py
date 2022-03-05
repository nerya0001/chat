import os
import socket
import struct
import threading
import time
import logging
from util import *
from window import Window

"""
basic messaging client for cmd, without any fancy protocols
"""

ENCODING = 'utf-8'
HOST = '127.0.0.1'  # here we need to put the server IP
II = '0.0.0.0'
PORT = 50004
# ports for files
SENDER_PORT = 50001
RECEIVE_PORT = 50002



# client object
class Client:
    def __init__(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        self.recv_file = []
        self.next_packt = 0
        self.stop_receive = False
        self.file_resume_name = ''
        # self.nickname = input('\nPlease enter a nickname: ')

        self.running = True  # will be set to false when we want to stop everything

        # the client has two threads, one for listening and the other for sending
        self.receive_thread = threading.Thread(target=self.receive)
        self.write_thread = threading.Thread(target=self.write)

        # we want this thread to also close when the client receives 'DISCONNECTED'
        self.write_thread.daemon = True

        self.receive_thread.start()
        self.write_thread.start()

    def stop(self):
        self.running = False
        self.sock.close()
        exit(0)


    def receive_file(self, filename):
        LEN = 18  # Length of the header
        CHECKSUM = 0  # Checksum, dummy value
        head_SEQ = 0  # Expected SEQ number

        recv_timeout = 60  # Timeout on receiver side
        last_SEQ = -1  # SEQ of last datagram
        header_length = 18


        window_size = 3  # Size of the window
        # window = Window(window_size, 0, 0, 0)  # Initialize the data buffer
        # is_ACKed = Window(window_size, 0, 0, 0)  # Initialize the ACK queue
        ACKed_list = []  # a list to check for duplicate ACKs
        dup_list = []  # a list to check for duplicate ACKs
        next_seq = 0
        build_file_name = filename.split('.')
        outputfile = build_file_name[0] + '_out' + '.' + build_file_name[1]
        try:
            file = open(outputfile, 'wb')  # Open the file in binary mode
        except FileNotFoundError:
            print("can't open file")
        re_file_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Create socket
        re_file_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        re_file_sock.bind((HOST, RECEIVE_PORT))  # Bind IP address and port number

        print('Waiting for the server to connect...')
        print('1')
        # this message send file request over TCP
        # try:
        #
        #     self.sock.send(message.encode(ENCODING))
        # except:
        #     print('oops')


        # handshake
        while True:

            try:
                Ack, addr = re_file_sock.recvfrom(1024)

                check = Ack[header_length:].decode(ENCODING).split(' ')
                # print(check)
                # print(addr)
                if check[0] == 'syn':
                    num_of_pckts = int(check[1])
                    data = b'syn-ack'
                    send_datagram(re_file_sock, HOST, RECEIVE_PORT, addr[1], LEN, CHECKSUM, 0, window_size, data, 'syn-ack')
                    re_file_sock.settimeout(3)
                    Ack, addr = re_file_sock.recvfrom(1024)
                    check = Ack[header_length:]
                    if check == b'ack':
                        break
                    else:
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

        print('Waiting for file...')
        while True:  # Main file receiving loop
            # Fill buffers with default values
            re_file_sock.settimeout(recv_timeout)  # Set timeout
            try:
                datagram, addr = re_file_sock.recvfrom(8192)  # Receive the datagram
            except ConnectionResetError:
                print(ConnectionResetError)
            except socket.timeout:
                # print('Receiver timed out. File transfer being aborted.')
                # print('Receiver timed out. sending last ACK.')
                # s = rewin.keys()
                # i = 0
                # while i in s:
                #     i += 1

                # payload = b''  # Dummy payload for ACK
                # TODO - to not foget the 0 case!!!!!! - ????
                # send_datagram(re_file_sock, HOST, RECEIVE_PORT, SENDER_PORT, LEN, CHECKSUM, i - 1, window_size, payload,'ACK')
                # RECEIVER SHOULD BE NOTIFIED
                re_file_sock.close()
                return
            finally:
                re_file_sock.settimeout(None)  # Stop the timeout

            bin_header = datagram[:header_length]  # Get 16 bits for the header
            header = struct.unpack('!HHhHQH', bin_header)  # Unpack header
            SEQ = header[4]  # Get sequence number
            window_size = header[5]
            # check = datagram[header_length:].decode(ENCODING).split(' ')
            # print(check[0])
            # if check[0] == 'Stop,':
            #     print('hey what?!')
            #     # a = input('type CON to continue:')
            #     data = f'CON'.encode(ENCODING)
            #     send_datagram(re_file_sock, HOST, RECEIVE_PORT, addr[1], LEN, CHECKSUM, SEQ, window_size, data, 'CON')
            #     break
            print('Received SEQ: ', SEQ)
            if SEQ == self.next_packt:
                self.next_packt += 1
            # Send ACK
            if SEQ in dup_list:
                payload = b'DUP'  # Dummy payload for ACK
                send_datagram(re_file_sock, HOST, RECEIVE_PORT, addr[1], LEN, CHECKSUM, SEQ, window_size, payload,'DUP-ACK')
                continue
            else:
                payload = b''  # Dummy payload for ACK
                send_datagram(re_file_sock, HOST, RECEIVE_PORT, addr[1], LEN, CHECKSUM, SEQ, window_size, payload,'ACK')

            if SEQ not in dup_list:
                dup_list.append(SEQ)

                payload = datagram[header_length:]  # Get payload
                self.recv_file.append([SEQ, payload])
                LEN = header[2]  # Get length
                if LEN == -1:  # If last datagram
                    last_SEQ = SEQ
                    print(f'last_SEQ: {last_SEQ}')
            if self.stop_receive:
                self.stop_receive = False
                payload = b'Stop'  # Dummy payload for ACK
                send_datagram(re_file_sock, HOST, RECEIVE_PORT, addr[1], LEN, CHECKSUM, SEQ, window_size, payload,'Stop')
                re_file_sock.close()
                return
            # Write to file
            if len(self.recv_file) == num_of_pckts:
                try:
                    self.recv_file.sort(key=lambda x:x[0])
                except:
                    logging.debug("An exception was thrown!", exc_info=True)
                    logging.info("An exception was thrown!", exc_info=True)
                    logging.warning("An exception was thrown!", exc_info=True)
                print('write to file...')
                for i in range(len(self.recv_file)):
                    # print('Writing SEQ: ', i)
                    payload = self.recv_file[i][1]  # Get the data from the buffer
                    # print(len(payload))
                    file.write(payload)  # Write the data to the file
                    # next_seq = head_SEQ + 1
                    ACKed_list.append(next_seq)
                file.close()
                print('Done.')
                print('Final SEQ: ', SEQ)
                print('--------------------- FILE RECEIVED ---------------------')

                # close connection
                data = f'FIN'.encode(ENCODING)
                send_datagram(re_file_sock, HOST, SENDER_PORT, RECEIVE_PORT, LEN, CHECKSUM, SEQ, window_size, data, 'FIN')

                f, add = re_file_sock.recvfrom(1048)

                print(f[header_length:].decode(ENCODING))
                re_file_sock.close()
                self.next_packt = 0
                self.recv_file.clear()
                self.stop_receive = False
                self.file_resume_name = ''
                return
                # else:
                #     next_seq += 1

    # handle sending a message
    def write(self):
        # a while true loop only in terminal mode if i'm not mistaken
        while True:
            try:
                message = f'{input("")}'
                try:
                    disassemble = message.split(' ')
                    if disassemble[0] == '/file':
                        messagemod = message + ' ' + str(RECEIVE_PORT) + ' ' + '0'
                        self.file_resume_name = disassemble[1]
                        if len(self.recv_file) > 0:
                            self.recv_file.clear()
                            self.next_packt = 0
                            self.stop_receive = False
                        self.sock.send(messagemod.encode(ENCODING))
                        self.file_thread = threading.Thread(target=self.receive_file, args=(self.file_resume_name,))
                        self.file_thread.start()
                    elif disassemble[0] == '/con':
                        messagemod = '/file' + ' ' + self.file_resume_name + ' ' + str(RECEIVE_PORT) + ' ' + str(self.next_packt)
                        self.sock.send(messagemod.encode(ENCODING))
                        self.file_thread = threading.Thread(target=self.receive_file, args=(self.file_resume_name,))
                        self.file_thread.start()
                    elif disassemble[0] == '/stop':
                        self.stop_receive = True
                    else:
                        self.sock.send(message.encode(ENCODING))
                except:
                    self.stop()
            except EOFError:

                self.stop()
                break
            except KeyboardInterrupt:
                self.running = False
                self.stop()
                break
            except ConnectionResetError:

                self.running = False
                self.stop()
                break
            except:
                print('something wrong')

    def receive(self):
        while self.running:
            try:
                message = self.sock.recv(1024).decode(ENCODING)
                if message == 'NICK':
                    self.sock.send(self.nickname.encode(ENCODING))
                elif message == 'DISCONNECTED':
                    print("Disconnected from the server")
                    self.running = False
                    self.stop()
                    break
                elif message == 'REG/LOG':
                    print("\ntype login or register: ")
                elif message == 'USERNAME':
                    print('enter a username: ')
                elif message == 'PASSWD':
                    print('enter a password: ')
                else:
                    print(message)

            except KeyboardInterrupt:
                self.running = False
                self.stop()
                break
            except ConnectionAbortedError:
                print('this is where 1')
                self.running = False
                self.stop()
                break
            except ConnectionResetError:
                print('this is where 2')
                self.running = False
                self.stop()
                break
            except:
                # logging.debug("An exception was thrown!", exc_info=True)
                # logging.info("An exception was thrown!", exc_info=True)
                # logging.warning("An exception was thrown!", exc_info=True)
                print('this is where 3')
                self.running = False
                self.stop()
                break


client = Client(HOST, PORT)
