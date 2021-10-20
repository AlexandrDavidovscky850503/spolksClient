import os
import socket
import tqdm
import regex
import random

SEPARATOR = "<SEPARATOR>"
BUFFER_SIZE = 1024 * 32 #8KB
SOCKET_PORT = 50015

def speed(buf, t0, t1):
    return round(len(buf) / (t1 - t0) / 1024 ** 2, 2)


def upload_file(connection, file_name, ip, message, p, c_id):
    print('Upload to server')
    filesize = os.path.getsize(file_name)
    print('Size: ', filesize)
    connection.settimeout(10.0)
    try:
        connection.send(bytes(message, encoding='utf-8'))
        connection.recv(10)
        connection.send(f"{file_name}{SEPARATOR}{filesize}".encode())
    except Exception:
        print('Cannot get file information')
        connection.close()
        while 1:
            try:
                print('Retrying to connect to', ip)                        
                connection = socket.socket()
                connection.settimeout(30.0)
                connection.connect((ip if ip else '127.0.0.1', SOCKET_PORT))
                print('connected')
                connection.settimeout(10.0)
                # connection.send(c_id)
                iii = f'{str(c_id)}' 
                connection.send(bytes(iii, encoding='utf-8'))
                connection.recv(10)
                break
            except Exception:
                print('Cannot connect to server.')
                while 1:
                    cont = input('Try again (y/n)?')
                    if cont == 'y' or cont == 'n':
                        break
                    print('Check your input')
                if cont == 'n':
                    exit(0)
        return connection
    progress = tqdm.tqdm(range(filesize), f"Sending {file_name}", unit="B", unit_scale=True, unit_divisor=1024)
    f = open(file_name, "rb")
    # print(str(f.read(5)))
    # bytes_read = f.read()
    # bytes_read_all = bytes(bytes_read)
    
    amount_to_read = BUFFER_SIZE
    total_send = 0
    while total_send < filesize:
        if filesize - total_send >= BUFFER_SIZE:
            amount_to_read = BUFFER_SIZE
        else:
            amount_to_read = filesize - total_send
            print(amount_to_read)
        part = f.read(amount_to_read)
        # part = bytes_read[:amount_to_read]
        # bytes_read = bytes_read[amount_to_read:]
        while 1:
            try:
                connection.send(part)
                connection.recv(10)
                progress.update(len(part))
                total_send += len(part)
                break
            except Exception:
                print('Connection lost')
                connection.close()
                # connection = socket.socket()
                while 1:
                    try:
                        print('Retrying to connect...')
                        print(ip)                           
                        # connection.settimeout(30.0)

                        for i in range(30):
                            connection = socket.socket()
                            # connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            # connection.getsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                            # connection.bind('192.168.1.1', p)
                            connection.settimeout(1.0)
                            try:
                                connection.connect((ip if ip else '127.0.0.1', SOCKET_PORT))
                                break
                            except:
                                # print('a')
                                if i == 29:
                                    raise Exception

                        # connection.connect((ip if ip else '127.0.0.1', SOCKET_PORT))
                        # connection.settimeout(None)
                        print('connected')                        
                        comm = 'cont'
                        total_r = '0'
                        msg = f'{comm} {total_r}'
                        connection.settimeout(10.0)
                        # connection.send(c_id)
                        iii = f'{str(c_id)}' 
                        connection.send(bytes(iii, encoding='utf-8'))
                        connection.recv(10)
                        connection.send(bytes(msg, encoding='utf-8'))
                        
                        pos = int(connection.recv(10))
                        f.seek(pos)
                        part = f.read(amount_to_read)
                        # bytes_read = bytes(bytes_read_all[pos:])
                        # part = bytes_read[:amount_to_read]
                        # bytes_read = bytes_read[amount_to_read:]
                        break
                    except Exception as e:
                        print('Cannot connect to server.')
                        while 1:
                            cont = input('Try again (y/n)?')
                            if cont == 'y' or cont == 'n':
                                break
                            print('Check your input')
                        if cont == 'n':
                            # return connection
                            exit(0)    
    progress.close()
    print(total_send)
    print('All')
    f.close()
    return connection


def recvall(sock, amount_to_read):
    n = 0
    data = bytearray()
    while n < amount_to_read:
        b = sock.recv(amount_to_read - n)
        if not b:
            print('error')
            return None
        n += len(b)
        data.extend(b)

    return data


def download_file(sock, file_name, ip, message, c_id):
    sock.settimeout(10.0)
    try:
        sock.send(bytes(message, encoding='utf-8'))
        received = sock.recv(BUFFER_SIZE).decode()
    except Exception:
        print('Cannot get file information')
        sock.close()
        while 1:
            try:
                print('Retrying to connect to', ip)                        
                sock = socket.socket()
                sock.settimeout(30.0)
                sock.connect((ip if ip else '127.0.0.1', SOCKET_PORT))
                print('connected')
                sock.settimeout(10.0)
                # sock.send(c_id)
                iii = f'{str(c_id)}' 
                sock.send(bytes(iii, encoding='utf-8'))
                sock.recv(10)
                break
            except Exception:
                print('Cannot connect to server.')
                while 1:
                    cont = input('Try again (y/n)?')
                    if cont == 'y' or cont == 'n':
                        break
                    print('Check your input')
                if cont == 'n':
                    exit(0)
        return sock
    file, filesize = received.split(SEPARATOR)
    if filesize == '-':
        print('File does not exist')
        return sock
    file = os.path.basename(file)
    print(file)
    filesize = int(filesize)
    progress = tqdm.tqdm(range(filesize), f"Receiving {file}", unit="B", unit_scale=True, unit_divisor=1024)
    total_read = 0
    if filesize >= BUFFER_SIZE:
        amount_to_read = BUFFER_SIZE
    else:
        amount_to_read = filesize
    with open(file, "wb") as f:
        while True:
            while 1:
                cont = 'y'
                try:
                    bytes_read = recvall(sock, amount_to_read)
                except Exception:
                    amount_to_read -= len(bytes_read)
                    print('Connection lost')
                    sock.close()
                    while 1:
                        try:
                            print('Retrying to connect to', ip)
                            # print(ip)                           
                            
                            for i in range(30):
                                sock = socket.socket()
                                sock.settimeout(1.0)
                                try:
                                    sock.connect((ip if ip else '127.0.0.1', SOCKET_PORT))
                                    break
                                except:
                                    # print('a')
                                    if i == 29:
                                        raise Exception                                
                            print('connected')
                            sock.settimeout(10.0)
                            # sock.send(c_id)
                            iii = f'{str(c_id)}' 
                            sock.send(bytes(iii, encoding='utf-8'))
                            sock.recv(10)
                            comm = 'cont'
                            total_r = str(total_read + len(bytes_read))
                            msg = f'{comm} {total_r}'
                            sock.send(bytes(msg, encoding='utf-8'))
                            sock.settimeout(10.0)
                            break
                        except Exception as e:
                            print('Cannot connect to server.')
                            while 1:
                                cont = input('Try again (y/n)?')
                                if cont == 'y' or cont == 'n':
                                    break
                                print('Check your input')
                            if cont == 'n':
                                # return sock
                                exit(0)
                if cont == 'n':
                    break
                else:
                    break
            f.write(bytes_read)
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
    return sock


def main():
    print('TCP Client!')
    while 1:
        ip_address = input(f'enter the server ip address: ')
        res = regex.match("^([\d]|[1-9][\d]|1[\d][\d]|2[0-4][\d]|25[0-5])\.([\d]|[1-9][\d]|1[\d][\d]|2[0-4][\d]|25[0-5])\.([\d]|[1-9][\d]|1[\d][\d]|2[0-4][\d]|25[0-5])\.([\d]|[1-9][\d]|1[\d][\d]|2[0-4][\d]|25[0-5])$", ip_address)
        if res != None:
            break
        print('Check your input')

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.getsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.connect((ip_address if ip_address else '127.0.0.1', SOCKET_PORT))
    sock.settimeout(10.0)

    client_id = random.randint(0, 65535)
    print('ID:', client_id)
    iii = f'{str(client_id)}'   
    sock.send(bytes(iii, encoding='utf-8'))
    sock.recv(10)

    # print(sock.getsockname()[1])
    port = sock.getsockname()[1]
    # print(ip_address)
    while True:
        message = input('<< ')
        if not message:
            continue
        command, *params = message.split(' ')
        if command != 'upload' and command != 'download' and  command != 'echo' and command != 'ping' and  command != 'pong' and command != 'kill' and command != 'help' and command != 'time':
            print('Unknowm command. Please, try again')
            continue
        # if message == 'q':
        #     sock.close()
        #     break
        if command == 'upload':
            file_name = params[0]
            if not os.path.isfile(file_name):
                print('File does not exist')
            else:
                message = f'{command} {params[0].split(os.path.sep)[-1]}'
                
                sock = upload_file(sock, file_name, ip_address, message, port, client_id)
            # sock.close()
        elif command == 'download':
            file = params[0]
            if len(params) > 1:
                file_name = params[1]
            else:
                file_name = file
            message = f'{command} {file}'
            sock = download_file(sock, file_name, ip_address, message, client_id)
            # sock.close()
        elif command == 'kill':
            sock.close()
            return
        elif command == 'echo':
            if (not params):
                print('Invalid arguments. Please try again')
                continue
            if (len(params[0]) == 0):
                print('Invalid arguments. Please try again')
                continue
            sock.send(message.encode(encoding='utf-8'))
            try:
                data = sock.recv(1024)
            except ConnectionAbortedError as e:
                print(f'connection with server lost: {e}')
                return
            finally:
                print(f'>> {data.decode(encoding="utf-8")}')
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
        print('Server unavailable')
        print(e)
