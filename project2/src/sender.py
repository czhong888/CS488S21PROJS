import sys
import time
import socket
import struct

# type|seqnum|length
rudp_header_struct = struct.Struct('!III')
rudp_header_size = rudp_header_struct.size

def rudp_send_file(receiver_ip, receiver_port, file):
    seq_num = 0
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0.5)
    with open(file, 'rb') as f:
        while True:
            chunk = f.read(1400)
            chunk_len = len(chunk)
            if chunk_len == 0:
                break
            header = rudp_header_struct.pack(0, seq_num, chunk_len)
            while True:
                sock.sendto(header+chunk, (receiver_ip, receiver_port))
                # print('send data, len:', len(header+chunk))
                try:
                    ack_data, _ = sock.recvfrom(1500)
                    ack_data_size = len(ack_data)
                    if ack_data_size < rudp_header_size:
                        # send again
                        continue

                    t, ack_seq_num, size = rudp_header_struct.unpack(ack_data[0:rudp_header_size])
                    # print('receive ack', ack_data_size, t, ack_seq_num, size)
                    if t != 1 or ack_seq_num != seq_num or size != 0:
                        # send again
                        continue

                    seq_num  = seq_num + 1
                    break
                except socket.timeout:
                    # send again
                    print('timeout, resend data')
                    continue
    sock.close()


def main():
    argc = len(sys.argv)
    if argc != 4:
        sys.exit(1)

    receiver_ip = sys.argv[1]
    try:
        receiver_port = int(sys.argv[2])
        if receiver_port < 0 or receiver_port > 65535:
            raise ValueError('bad receiver port')
    except ValueError:
        sys.exit(1)
    
    # print(type(data_to_send), len(data_to_send))
    return rudp_send_file(receiver_ip, receiver_port, sys.argv[3])



if __name__ == '__main__':
    main()
