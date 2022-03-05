import struct

def load_file(filename):
    out = []
    seq = 0
    buffer_size = 4096
    with open(filename, 'rb') as f:
        data = f.read(buffer_size)
        while data:
            # print(len(data))
            out.append({seq:[data, False]})
            data = f.read(buffer_size)
            seq += 1
    return out


def send_datagram(sock, IP, S_PORT, D_PORT, LEN, CHECKSUM, SEQ, win, data, type):
    # packed according to the format -> '!HHhHQH'' => (network/bigEndian,un_short,un_short,short,un_short,unsigned l l)
    header = struct.pack('!HHhHQH', S_PORT, D_PORT, LEN, CHECKSUM, SEQ, win)
    if data is None:
        data = b''
    sock.sendto(header + data, (IP, D_PORT))  # Send the datagram
    print('Sending ', type, ': ', SEQ)


def resend_util(window:dict):
    ans1 = {}
    # while not window.is_empty() and window.get_index(0) is not None:
    for item in window:
        if not window[item][1]:
            ans1.update({item: window[item]})
    return ans1


def resend_append_util(window:dict, ans1:dict):
    for item in window:
        if item not in ans1 and not window[item][1]:
            ans1.update({item: window[item]})
    return ans1
