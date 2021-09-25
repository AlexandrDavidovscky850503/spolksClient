import os
import socket
import time
import argparse
import tqdm

SEPARATOR = "<SEPARATOR>"
BUFFER_SIZE = 1024 * 8 #8KB

def speed(buf, t0, t1):
    return round(len(buf) / (t1 - t0) / 1024 ** 2, 2)


def upload_file(connection, file_name):
    print('Upload to server')
    filesize = os.path.getsize(file_name)
    connection.send(f"{file_name}{SEPARATOR}{filesize}".encode())
    progress = tqdm.tqdm(range(filesize), f"Sending {file_name}", unit="B", unit_scale=True, unit_divisor=1024)
    with open(file_name, "rb") as f:
        while True:
            # read the bytes from the file
            bytes_read = f.read(BUFFER_SIZE)
            if not bytes_read:
                # file transmitting is done
                break
            # we use sendall to assure transimission in
            # busy networks
            connection.sendall(bytes_read)
            # update the progress bar
            progress.update(len(bytes_read))
    f.close()

def download_file(sock, file_name):
    # receive the file infos
    # receive using client socket, not server socket
    received = sock.recv(BUFFER_SIZE).decode()
    file, filesize = received.split(SEPARATOR)
    # remove absolute path if there is
    file = os.path.basename(file)
    # convert to integer
    filesize = int(filesize)
    # start receiving the file from the socket
    # and writing to the file stream
    progress = tqdm.tqdm(range(filesize), f"Receiving {file}", unit="B", unit_scale=True, unit_divisor=1024)
    with open(file, "wb") as f:
        while True:
            # read 1024 bytes from the socket (receive)
            bytes_read = sock.recv(BUFFER_SIZE)
            if not bytes_read:
                # nothing is received
                # file transmitting is done
                break
            # write to the file the bytes we just received
            f.write(bytes_read)
            # update the progress bar
            progress.update(len(bytes_read))
    f.close()



def main():

    print('TCP Client!')
    print('-' * 64)

    ip_address = input(f'enter the server ip address: ')

    while True:
        sock = socket.socket()
        sock.connect((ip_address if ip_address else '127.0.0.1', 50001))

        message = input('<< ')

        if not message:
            continue

        command, *params = message.split(' ')

        if message == 'q':
            sock.close()
            break
        if command == 'upload':
            file_name = params[0]

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
            sock.close()
        else:
            sock.send(bytes(message, encoding='utf-8'))
            try:
                data = sock.recv(1024)
            except ConnectionAbortedError as e:
                print(f'connection with server lost: {e}')
                return
            finally:
                print(f'>> {data.decode(encoding="utf-8")}')

        if command == 'kill':
            sock.close()
            return


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(e)