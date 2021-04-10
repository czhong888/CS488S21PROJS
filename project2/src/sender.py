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


def rudp_send_data(ip, port, data):
    seq_num = 0
    data_len = len(data)
    # split data into datagram payload
    datagrams = []
    datagram_count = data_len // RUDP_PAYLOAD_MAX_LEN
    last_payload_len = data_len % RUDP_PAYLOAD_MAX_LEN
    if last_payload_len != 0:
        datagram_count = datagram_count + 1
    else:
        last_payload_len = RUDP_PAYLOAD_MAX_LEN
    
    print('about to send {} datagrams'.format(datagram_count), file=sys.stderr)

    for i in range(datagram_count-1):
        datagram_header = rudp_header_struct.pack(
            RUDP_TYPE_PAYLOAD, seq_num, RUDP_PAYLOAD_MAX_LEN, False)
        datagram_payload = data[(seq_num*RUDP_PAYLOAD_MAX_LEN):((seq_num+1)*RUDP_PAYLOAD_MAX_LEN)]
        datagrams.append([seq_num, datagram_header + datagram_payload, None, False])
        seq_num = seq_num + 1
    # last datagram
    datagram_header = rudp_header_struct.pack(
        RUDP_TYPE_PAYLOAD,
        seq_num,
        last_payload_len,
        True
    )
    datagram_payload = data[(datagram_count-1)*RUDP_PAYLOAD_MAX_LEN:]
    datagrams.append([seq_num, datagram_header + datagram_payload, None, False])
    
    window_begin = 0
    window_send = window_begin
    window_end = window_begin + WINDOW_SIZE
    if window_end >= datagram_count:
        window_end = datagram_count
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect((ip, port))
    while True:
        # TODO: calc condition to stop
        if window_begin >= window_end:
            break

        # send datagrams
        for i in range(window_send, window_end):
            if random.random() < rate:
                print('send datagram:', datagrams[i][0], file=sys.stderr)
                sock.send(datagrams[i][1])
            else:
                print('discard {} datagram'.format(datagrams[i][0]), file=sys.stderr)
            datagrams[i][2] = time.time()
            window_send = window_send + 1
        
        # calculate timeout
        timeout = 1.0
        now = time.time()
        for i in range(window_begin, window_send):
            t = now - datagrams[i][2]
            if t < timeout:
                timeout = t
        
        rlist, _, _ = select.select([sock], [], [], timeout)
        if sock in rlist:
            datagram = sock.recv(RUDP_DATAGRAM_MAX_LEN)
            datagram_len = len(datagram)
            if datagram_len < RUDP_HEADER_LEN:
                print('datagram too short', file=sys.stderr)
            else:
                t, sn, _, _ = rudp_header_struct.unpack(datagram[:RUDP_HEADER_LEN])
                if t != RUDP_TYPE_ACK:
                    print('ack datagram expected', file=sys.stderr)
                else:
                    print('receive ack packet for seq num:', sn, file=sys.stderr)
                    for i in range(window_begin, window_send):
                        if datagrams[i][0] == sn:
                            datagrams[i][3] = True
                            break

        # check timeout, send timeout datagrams
        update_count = 0
        now = time.time()
        last_ack = True
        for i in range(window_begin, window_send):
            if last_ack and datagrams[i][3]:
                update_count = update_count + 1
            else:
                last_ack = False
            
            if now - datagrams[i][2] > TIMEOUT:
                if random.random() < rate:
                    sock.send(datagrams[i][1])
                    print('re-send datagram:', datagrams[i][0], file=sys.stderr)
                else:
                    print('re-discard {} datagram'.format(datagrams[i][0]), file=sys.stderr)
                datagrams[i][2] = now
        
        # update window
        window_begin = window_begin + update_count
        window_end = window_end + update_count
        if window_end >= datagram_count:
            window_end = datagram_count
    
    sock.close()



def main():
    argc = len(sys.argv)
    if argc != 3:
        sys.exit(1)
    
    receiver_ip = sys.argv[1]
    try:
        receiver_port = int(sys.argv[2])
        if receiver_port < 0 or receiver_port > 65535:
            raise ValueError('bad receiver port')
    except ValueError:
        sys.exit(1)

    # data = sys.stdin.read()
    beg_time = time.time()
    data = sys.stdin.read()
    rudp_send_data(receiver_ip, receiver_port, data.encode())
    data_len = len(data)
    time_used = time.time() - beg_time
    print('Sent {} bytes in {} seconds: {} kB/s'.format(
        data_len, int(time_used), int(data_len/1024/time_used)), file=sys.stderr)



if __name__ == '__main__':
    main()
