import sys
import socket
import struct


# type|seqnum|length
rudp_header_struct = struct.Struct('!III')
rudp_header_size = rudp_header_struct.size

def rudp_receive_file(port, file):
    seq_num = 0
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', port))
    with open(file, 'wb') as f:
        while True:
            data, client_addr = sock.recvfrom(1500)
            data_len = len(data)
            if data_len == 0:
                break

            if data_len < rudp_header_size:
                continue

            t, data_seq_num, size = rudp_header_struct.unpack(data[:rudp_header_size])
            print(t, data_seq_num, size, data_len)
            if t != 0 or size < 0:
                print('invalid data')
                continue

            if data_seq_num != seq_num and seq_num > 0:
                # resend ack
                sock.sendto(rudp_header_struct.pack(1, seq_num-1, 0), client_addr)
                continue
            
            # print('send_ack', client_addr)
            # send ack
            sock.sendto(rudp_header_struct.pack(1, seq_num, 0), client_addr)
            # save data
            f.write(data[rudp_header_size:])
            seq_num = seq_num + 1

            if (data_len - rudp_header_size) != 1400:
                # last datagram
                break
    sock.close()



def main():
    argc = len(sys.argv)
    if argc != 3:
        sys.exit(1)

    try:
        port = int(sys.argv[1])
        if port < 1024 or port > 65535:
            raise ValueError('bad receiver port')
    except ValueError:
        sys.exit(1)


    return rudp_receive_file(port, sys.argv[2])


if __name__ == '__main__':
    main()

