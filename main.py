# from _typeshed import Self
import os
import socket
import time
import argparse
import tqdm

SEPARATOR = "<SEPARATOR>"
BUFFER_SIZE = 1024 * 32 #8KB
IP_ADDRESS = '127.0.0.1'
SOCKET_PORT = 50015

def speed(buf, t0, t1):
    return round(len(buf) / (t1 - t0) / 1024 ** 2, 2)


def upload_file(connection, file_name):
    print('Upload to server')
    filesize = os.path.getsize(file_name)
    print('Size: ', filesize)
    connection.send(f"{file_name}{SEPARATOR}{filesize}".encode())
    connection.recv(10)
    progress = tqdm.tqdm(range(filesize), f"Sending {file_name}", unit="B", unit_scale=True, unit_divisor=1024)

    f = open(file_name, "rb")
    bytes_read = f.read()
    # print(bytes_read)
    while len(bytes_read) >= BUFFER_SIZE:
        part = bytes_read[:BUFFER_SIZE]
        # print(len(part))
        bytes_read = bytes_read[BUFFER_SIZE:]
        connection.send(part)
            # update the progress bar
        progress.update(len(part))
    # progress.close()


    if (len(bytes_read)) > 0:
        connection.send(bytes_read)
            # update the progress bar
        progress.update(len(bytes_read))
    progress.close()

    print('All')
    f.close()

def recvall(sock, amount_to_read):
    n = 0
    data = bytearray()
    while n < amount_to_read:
        b = sock.recv(amount_to_read)
        if not b:
            return None
        n += len(b)
        data.extend(b)

    return data



def download_file(sock, file_name):
    # receive the file infos
    # receive using client socket, not server socket
    received = sock.recv(BUFFER_SIZE).decode()
    file, filesize = received.split(SEPARATOR)
    if filesize == '-':
        print('File does not exist')
        return
    # remove absolute path if there is
    file = os.path.basename(file)
    print(file)
    # convert to integer
    filesize = int(filesize)
    # start receiving the file from the socket
    # and writing to the file stream
    progress = tqdm.tqdm(range(filesize), f"Receiving {file}", unit="B", unit_scale=True, unit_divisor=1024)
    total_read = 0
    if filesize >= BUFFER_SIZE:
        amount_to_read = BUFFER_SIZE
    else:
        amount_to_read = filesize
    with open(file, "wb") as f:
        while True:

            # read 1024 bytes from the socket (receive)

            while 1:
                cont = 'y'
                # bytes_read = sock.recv(amount_to_read, socket.MSG_WAITALL)
                bytes_read = recvall(sock, amount_to_read)
                print(amount_to_read)
                print(len(bytes_read))
                if len(bytes_read) < amount_to_read:
                    amount_to_read -= len(bytes_read)
                    print('Connection lost')
                    while 1:
                        try:
                            sock.settimeout(30)
                            sock.connect((IP_ADDRESS if IP_ADDRESS else '127.0.0.1', SOCKET_PORT))
                            sock.settimeout(None)
                            break
                        except Exception as e:
                            print('Cannot connect to server.')
                            while 1:
                                cont = input('Try again (y/n)?')
                                sock.settimeout(None)
                                if cont == 'y' or cont == 'n':
                                    break
                                print('Check your input')
                            if cont == 'n':
                                break

                if cont == 'n':
                    break
                else:
                    break

            print('Good!')


            # if not bytes_read:
            #     # nothing is received
            #     # file transmitting is done
            #     break


            # write to the file the bytes we just received
            f.write(bytes_read)
            # update the progress bar
            progress.update(len(bytes_read))
            total_read += len(bytes_read)
            if filesize - total_read >= BUFFER_SIZE:
                amount_to_read = BUFFER_SIZE
            else:
                amount_to_read = filesize - total_read
            if total_read == filesize:
                progress.close()
                print('All')
                break
    f.close()



def main():

    print('TCP Client!')
    print('-' * 64)

    ip_address = input(f'enter the server ip address: ')
    IP_ADDRESS = ip_address if ip_address else '127.0.0.1'

    sock = socket.socket()
    sock.connect((ip_address if ip_address else '127.0.0.1', SOCKET_PORT))

    while True:
        message = input('<< ')

        if not message:
            continue

        command, *params = message.split(' ')

        if message == 'q':
            sock.close()
            break
        if command == 'upload':
            file_name = params[0]

            if not os.path.isfile(file_name):
                print('File does not exist')
            else:
                message = f'{command} {params[0].split(os.path.sep)[-1]}'
                sock.send(bytes(message, encoding='utf-8'))

                upload_file(sock, file_name)
            # sock.close()
        elif command == 'download':
            file = params[0]

            if len(params) > 1:
                file_name = params[1]
            else:
                file_name = file

            message = f'{command} {file}'
            sock.send(bytes(message, encoding='utf-8'))
            sock.settimeout(10)
            download_file(sock, file_name)
            # sock.close()
        elif command == 'kill':
            sock.close()
            return
        else:
            sock.send(message.encode(encoding='utf-8'))
            try:
                data = sock.recv(1024)
            except ConnectionAbortedError as e:
                print(f'connection with server lost: {e}')
                return
            finally:
                print(f'>> {data.decode(encoding="utf-8")}')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(e)
