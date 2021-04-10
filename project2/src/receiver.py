import sys
import time
import random
import select
import socket
import struct


rate = 0.9
TIMEOUT = 1
WINDOW_SIZE = 10
RUDP_TYPE_ACK = 1
RUDP_TYPE_PAYLOAD = 2
RUDP_DATAGRAM_MAX_LEN = 1400
# type|seq_num|payload_len|is_last_datagram
rudp_header_struct = struct.Struct('!III?')
RUDP_HEADER_LEN = rudp_header_struct.size
RUDP_PAYLOAD_MAX_LEN = RUDP_DATAGRAM_MAX_LEN - RUDP_HEADER_LEN


def rudp_receive_file(port):
    data = b''
    expect_seq_num = 0
    all_received = False
    recv_window = [None] * WINDOW_SIZE
    last_seq_num = None

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', port))
    sock.settimeout(TIMEOUT)
    while True:
        try:
            datagram_data, addr = sock.recvfrom(RUDP_DATAGRAM_MAX_LEN)
            datagram_data_len = len(datagram_data)
            if datagram_data_len < RUDP_HEADER_LEN:
                print('datagram too short, ignore', file=sys.stderr)
                continue

            t, sn, l, is_last = rudp_header_struct.unpack(datagram_data[:RUDP_HEADER_LEN])
            if t != RUDP_TYPE_PAYLOAD:
                print('payload datagram expected, ignore', file=sys.stderr)
                continue

            if sn > expect_seq_num + WINDOW_SIZE:
                print('seq_num too great, ignore', file=sys.stderr)
                continue

            print('receive {} datagram, {}, {}:'.format(sn, l, len(datagram_data[RUDP_HEADER_LEN:])), file=sys.stderr)
            if is_last:
                last_seq_num = sn

            # send ack
            ack_datagram_header = rudp_header_struct.pack(RUDP_TYPE_ACK, sn, 0, False)
            if random.random() < rate:
                print('send ack datagram', sn, file=sys.stderr)
                sock.sendto(ack_datagram_header, addr)
            else:
                print('discard ack datagram', sn, file=sys.stderr)
            if sn >= expect_seq_num:
                recv_window[sn - expect_seq_num] = datagram_data[RUDP_HEADER_LEN:]
            
            # check and update window
            count = 0
            while len(recv_window) > 0 and recv_window[0]:
                count = count + 1
                data = data + recv_window.pop(0)
            
            if count > 0:
                recv_window.extend([None] * count)
            expect_seq_num = expect_seq_num + count
            if last_seq_num and expect_seq_num >= last_seq_num:
                all_received = True
        except socket.timeout:
            if all_received:
                break
    
    return data
    


def main():
    argc = len(sys.argv)
    if argc != 2:
        sys.exit(1)

    try:
        port = int(sys.argv[1])
        if port < 1024 or port > 65535:
            raise ValueError('bad port')
    except ValueError:
        sys.exit(1)

    data = rudp_receive_file(port)
    print(data.decode(), end='')
    print('File received, exiting.', file=sys.stderr)

if __name__ == '__main__':
    main()
