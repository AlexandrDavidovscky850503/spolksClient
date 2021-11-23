import builtins
from ctypes import sizeof
import os
import socket
import tqdm
import regex
import random
import re
import time

SEPARATOR = "<SEPARATOR>"
BUFFER_SIZE = 1024 * 32  # 8KB
SOCKET_PORT = 50018


def upload_reconnect(connection, ip, port, c_id, f_l, a_to_read):
    while 1:
        try:
            print('Retrying to connect to', ip)
            for i in range(30):
                connection = socket.socket()
                connection.settimeout(1.0)
                try:
                    connection.connect((ip if ip else '127.0.0.1', port))
                    break
                except:
                    if i == 29:
                        raise Exception

            print('connected')
            comm = 'cont'
            total_r = '0'
            msg = f'{comm} {total_r}'
            connection.settimeout(10.0)
            iii = f'{str(c_id)}'
            connection.send(bytes(iii, encoding='utf-8'))
            connection.recv(10)
            connection.send(bytes(msg, encoding='utf-8'))

            pos = int(connection.recv(10))
            f_l.seek(pos)
            part = f_l.read(a_to_read)
            break
        except Exception as e:
            print('Cannot connect to client.')
            while 1:
                cont = input('Try again (y/n)?')
                if cont == 'y' or cont == 'n':
                    break
                print('Check your input')
            if cont == 'n':
                exit(0)

    return connection, part


def download_reconnect(sock, ip, port, c_id, t_read, l_bytes_read):
    while 1:
        try:
            print('Retrying to connect to', ip)
            for i in range(30):
                sock = socket.socket()
                sock.settimeout(1.0)
                try:
                    sock.connect((ip if ip else '127.0.0.1', port))
                    break
                except:
                    if i == 29:
                        raise Exception
            print('connected')
            sock.settimeout(10.0)
            iii = f'{str(c_id)}'
            sock.send(bytes(iii, encoding='utf-8'))
            sock.recv(10)
            comm = 'cont'
            total_r = str(t_read + l_bytes_read)
            msg = f'{comm} {total_r}'
            sock.send(bytes(msg, encoding='utf-8'))
            sock.settimeout(10.0)
            break
        except Exception as e:
            print('Cannot connect to client.')
            while 1:
                cont = input('Try again (y/n)?')
                if cont == 'y' or cont == 'n':
                    break
                print('Check your input')
            if cont == 'n':
                exit(0)

    return sock


def reconnect(sock, ip, port, c_id):
    while 1:
        try:
            print('Retrying to connect to', ip)
            for i in range(30):
                sock = socket.socket()
                sock.settimeout(1.0)
                try:
                    sock.connect((ip if ip else '127.0.0.1', port))
                    break
                except:
                    if i == 29:
                        raise Exception
            print('connected')
            sock.settimeout(10.0)
            iii = f'{str(c_id)}'
            sock.send(bytes(iii, encoding='utf-8'))
            sock.recv(10)
            break
        except Exception:
            print('Cannot connect to client.')
            while 1:
                cont = input('Try again (y/n)?')
                if cont == 'y' or cont == 'n':
                    break
                print('Check your input')
            if cont == 'n':
                exit(0)

    return sock


def upload_file(connection, file_name, ip, message, c_id):
    print('Upload to client')
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
        connection = reconnect(connection, ip, SOCKET_PORT, c_id)
        return connection
    progress = tqdm.tqdm(range(filesize), f"Sending {file_name}", unit="B", unit_scale=True, unit_divisor=1024)
    f = open(file_name, "rb")
    amount_to_read = BUFFER_SIZE
    total_send = 0
    while total_send < filesize:
        if filesize - total_send >= BUFFER_SIZE:
            amount_to_read = BUFFER_SIZE
        else:
            amount_to_read = filesize - total_send
            print(amount_to_read)
        part = f.read(amount_to_read)
        while 1:
            try:

                connection.send(part)
                total_send += len(part)
                connection.recv(10)
                progress.update(len(part))
                # total_send += len(part)
                # print(total_send)
                break
            except Exception:
                print('Connection lost')
                connection.close()
                connection, part = upload_reconnect(connection, ip, SOCKET_PORT, c_id, f, amount_to_read)

    progress.close()
    # print('Total sent:', total_send)
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
        sock = reconnect(sock, ip, SOCKET_PORT, c_id)
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
                    # sock = download_reconnect(sock, ip, SOCKET_PORT, c_id, total_read, len(bytes_read))
                    while 1:
                        try:
                            print('Retrying to connect to', ip)
                            for i in range(30):
                                sock = socket.socket()
                                sock.settimeout(1.0)
                                try:
                                    sock.connect((ip if ip else '127.0.0.1', SOCKET_PORT))
                                    break
                                except:
                                    if i == 29:
                                        raise Exception
                            print('connected')
                            sock.settimeout(10.0)
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
                            print('Cannot connect to client.')
                            while 1:
                                cont = input('Try again (y/n)?')
                                if cont == 'y' or cont == 'n':
                                    break
                                print('Check your input')
                            if cont == 'n':
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
        ip_address = input(f'enter the client ip address: ')
        res = regex.match(
            "^([\d]|[1-9][\d]|1[\d][\d]|2[0-4][\d]|25[0-5])\.([\d]|[1-9][\d]|1[\d][\d]|2[0-4][\d]|25[0-5])\.([\d]|[1-9][\d]|1[\d][\d]|2[0-4][\d]|25[0-5])\.([\d]|[1-9][\d]|1[\d][\d]|2[0-4][\d]|25[0-5])$",
            ip_address)
        if res != None:
            break
        print('Check your input')
    client_id = random.randint(0, 65535)
    print('ID:', client_id)
    iii = f'{str(client_id)}'
    sock = socket.socket()
    # sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10.0)
    try:
        sock.connect((ip_address if ip_address else '127.0.0.1', SOCKET_PORT))
        sock.send(bytes(iii, encoding='utf-8'))
        sock.recv(10)
    except Exception:
        sock.close()
        sock = reconnect(sock, ip_address, SOCKET_PORT, client_id)
    while True:
        message = input('<< ')
        if not message:
            continue
        command, *params = message.split(' ')
        if command != 'upload' and command != 'download' and command != 'echo' and command != 'ping' and command != 'pong' and command != 'kill' and command != 'help' and command != 'time':
            print('Unknowm command. Please, try again')
            continue
        if command == 'upload':
            file_name = params[0]
            if not os.path.isfile(file_name):
                print('File does not exist')
            else:
                message = f'{command} {params[0].split(os.path.sep)[-1]}'
                sock = upload_file(sock, file_name, ip_address, message, client_id)
        elif command == 'download':
            file = params[0]
            if len(params) > 1:
                file_name = params[1]
            else:
                file_name = file
            message = f'{command} {file}'
            sock = download_file(sock, file_name, ip_address, message, client_id)
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
            try:
                sock.send(message.encode(encoding='utf-8'))
                data = sock.recv(1024)
                print(f'>> {data.decode(encoding="utf-8")}')
            except Exception:
                sock.close()
                sock = reconnect(sock, ip_address, SOCKET_PORT, client_id)
        else:
            try:
                sock.send(message.encode(encoding='utf-8'))
                data = sock.recv(1024)
                print(f'>> {data.decode(encoding="utf-8")}')
            except Exception:
                sock.close()
                sock = reconnect(sock, ip_address, SOCKET_PORT, client_id)


#===================UDP start=========================
WINDOW_SIZE = 4096

UDP_BUFFER_SIZE = 32768
TIMEOUT = 20
DOWNLOAD_PROGRESS = 0
OK_STATUS = 200
UDP_DATAGRAMS_AMOUNT = 15
server_address = ('127.0.0.1', SOCKET_PORT)
client_id_str = 0

datagram_count_in = 0
datagram_count_out = 0


def udp_send(data, addr, bytes_amount, datagrams_amount, greeting_flag = False):
    global datagram_count_out
    fl = False
    datagram_count_out_begin = int(datagram_count_out)
    data_temp = bytes(data)
    i_temp = 0
    seq_num = 0
    while(True):
        for i in range(i_temp, datagrams_amount):
            temp = format(datagram_count_out, '05d').encode('utf-8')
            # print('===iteration ', i)
            data_part = data[:bytes_amount]
            if greeting_flag:
                data_part = str('g').encode('utf-8') + temp + data_part
            else:
                data_part = temp + data_part
            # if not data_part:
            #     print('Bla')

            client.sendto(data_part, addr)
            # print(datagram_count_out)
            data = data[bytes_amount:]
            # datagram_count_out += 1
            if datagram_count_out == 99999:
                datagram_count_out = 0
            else:
                datagram_count_out += 1
            try:
                fl = False
                client.settimeout(0)
                seq_num = client.recvfrom(5)
                client.settimeout(None)
                fl = True
                break

            except Exception:

                client.settimeout(None)
                pass
        # print('aaaaaaa')

        if not fl:
            # print('A0A0', datagram_count_out)
            client.settimeout(15)
            seq_num = client.recvfrom(5)

            # print('A1A1', seq_num)
        client.settimeout(None)

        if datagram_count_out_begin + datagrams_amount > 99999:
            dd = datagram_count_out_begin + datagrams_amount - 100000
        else:
            dd = datagram_count_out_begin + datagrams_amount

        if datagram_count_out == int(seq_num[0]) and datagram_count_out == dd:
            # print('BBBB')
            # datagram_count_out = int(seq_num[0])
            # print('finish ', datagram_count_out)
            return True
        else:
            datagram_count_out = int(seq_num[0])
            # datagrams_amount = datagram_count_out - datagram_count_out_old
            if int(seq_num[0]) - datagram_count_out_begin < 0:
                i_temp = 100000 + int(seq_num[0]) - datagram_count_out_begin
            else:
                i_temp = int(seq_num[0]) - datagram_count_out_begin
            datagram_count_out_old = int(seq_num[0])
            data = bytes(data_temp[(datagram_count_out - datagram_count_out_begin) * bytes_amount:])

            # print('finish ', datagram_count_out)
            # return False, sent_amount
            continue


def udp_recv(bytes_amount, timeout, datagrams_amount):
    global server_address
    # print('recv')
    global datagram_count_in
    # datagram_count_in_old = datagram_count_in 
    datagram_count_in_begin = datagram_count_in 

    exc_flag = False
    aaa = False
    # tim1 = timeout if timeout == None else 1
    # tim2 = timeout if timeout == None else 1
    data = bytes()
    counter = 0
    req = 0

    i_temp = 0
    addr = ('127.0.0.1', SOCKET_PORT)


    while 1:
        i = i_temp
        while i < datagrams_amount:
            try:
                if aaa:
                    client.settimeout(timeout)
                else:
                    client.settimeout(0.1)
                # print(i)
                data_temp, bbb = client.recvfrom(bytes_amount)
                # if len(data_temp) < bytes_amount:
                #     print(len(data_temp))
                #     input('a')
                #     raise Exception
               
                client.settimeout(None)
                
                # print('===iteration ', i)
                seq_num = int(data_temp[:5])
                # print('seq_num', seq_num)
                # print('datagram_count_in', datagram_count_in)
                # print('counter', counter)
                if aaa and seq_num == req:
                    # print('B')
                    aaa = False
            except Exception:
                # print(f'bbbbbb', i)
                i += 1
                exc_flag = True
                # continue
                if aaa:
                    raise Exception
                break
            # print('i_temp', i_temp)
            # print(datagram_count_in - datagram_count_in_begin)
            # if datagram_count_in - datagram_count_in_begin > 4:
            #     input('datagram_count_in - datagram_count_in_begin!!!')
            if datagram_count_in == seq_num  :
                counter += 1
                data += bytes(data_temp[5:])
                if datagram_count_in == 99999:
                    datagram_count_in = 0
                else:
                    datagram_count_in += 1
            else:
                break
            i += 1

        if counter == datagrams_amount:
            # print('aaaaa1')
            temp = format(datagram_count_in, '05d')
            # client.settimeout(None)
            client.sendto(str.encode(temp), server_address)
            break
        else:
            # print('aaaaa3', datagram_count_in)
            aaa = True
            
            if datagram_count_in - datagram_count_in_begin < 0:
                i_temp = 100000 + datagram_count_in - datagram_count_in_begin
            else:
                i_temp = datagram_count_in - datagram_count_in_begin

            # datagram_count_in_old = datagram_count_in

            req = datagram_count_in
            temp = format(datagram_count_in, '05d')
            # client.settimeout(None)
            client.sendto(str.encode(temp), server_address)
            continue
         
    return data, addr, exc_flag






def get_data(ll):
    # data, address = client.recvfrom(UDP_BUFFER_SIZE)
    # recv_flags = []
    # buffer = []
    # for i in range(1):
    #     recv_flags.append(False)
    #     # seq_nums.append(0)
    #     buffer.append(bytes())
    data, address, a = udp_recv(ll + 5, 10, 1)
    # data, address, a = udp_recv(UDP_BUFFER_SIZE, None, 1, recv_flags, buffer)
    # print('AAAAA', data)
    data = data.decode('utf-8')
    return [data, address]

def send_data(data):
    global server_address
    print('send_data')
    # client.sendto(str(data).encode('utf-8'), server_address)
    udp_send(str(data).encode('utf-8'), server_address, UDP_BUFFER_SIZE, 1)
    print('send_data_end')


def handle_input_request(request):
    data = request.split()
    command = data[0]

    if (len(data) == 2):
        params = data[1]

    try:
        if (command == "echo"):
            send_data(request)
            echo(len(params))

        elif (command == "time"):
            send_data(request)
            get_time()

        elif (command == "download"):
            send_data(request)
            if (wait_for_ack(command, 12) == False):
                return
            print('ddddddddddddd')
            download(params, request)

        elif (command == "upload"):
            send_data(request)
            if (wait_for_ack(command, 12) == False):
                return
            print('ddddddddddddd')
            upload(params)

        elif (command == "help"):
            print("help - to see list of commands\n\
                    exit - to quit\n\
                    echo - to resend message to a client\n\
                    upload - to upload file on the server\n\
                    download - to download file from a server\n\
                    time - get server time\
                    ")

        elif (command == "exit"):
            client.close()
            os._exit(1)
    except Exception:
        print('Cannot process the command. Please, try again')

def wait_for_ack(command_to_compare, ll):
    print('wait_for_ack')
    while True:
    # for i in range(10):
        # recv_flags = []
        # buffer = []
        # for i in range(1):
        #     recv_flags.append(False)
        #     # seq_nums.append(0)
        #     buffer.append(bytes())
        # response = get_data()[0].split(" ", 2)
        response, a, b = udp_recv(ll + 5, 10.0, 1)
        # response, a, b = udp_recv(UDP_BUFFER_SIZE, 10.0, 1, recv_flags, buffer)
        print(response)
        response = str(response.decode('utf-8')).split(" ", 2)

        if not response:
            print('11111111111')
            return False

        sent_request = response[0]
        status = response[1]

        if (len(response) > 2):
            message = response[2]
        else: message = None

        if (command_to_compare == sent_request and int(status) == OK_STATUS):
            return True
        elif (message):
            print(message)
            return False
        else:
            return False

def echo(l):
    print(get_data(l)[0])

def get_time():
    print(get_data(21)[0])


def upload(file_name):
    global server_address
    f = open(file_name, "rb+")

    size = int(os.path.getsize(file_name))
    total_size=0

    print("File size: %f" % (size))
    send_data(size)

    data_size_recv = int(get_data(UDP_BUFFER_SIZE)[0])

    send_data(data_size_recv)

    f.seek(data_size_recv, 0)
    current_pos = data_size_recv

    print("current_pos = ")
    print(current_pos)

    progress = tqdm.tqdm(range(int(size)), f"Progress of {file_name}:", unit="B", unit_scale=True,
                        unit_divisor=1024)

    progress.update(total_size)
    while (1):
        try:
            if (current_pos >= size):
                # server.sendto(b"EOF", addr)
                udp_send("EOF", server_address, UDP_BUFFER_SIZE, UDP_DATAGRAMS_AMOUNT)
                break
            else:
                data_file = f.read(UDP_BUFFER_SIZE * UDP_DATAGRAMS_AMOUNT)
                # server.sendto(data_file, addr)
                udp_send(data_file, server_address, UDP_BUFFER_SIZE, UDP_DATAGRAMS_AMOUNT)
                
                current_pos = current_pos + UDP_BUFFER_SIZE * UDP_DATAGRAMS_AMOUNT
                f.seek(current_pos)
                total_size+=len(data_file)
                progress.update(len(data_file))
                # print(total_size)
                if total_size == size:
                    break
        except KeyboardInterrupt:
            f.close()
            client.close()
            progress.close()
            os._exit(1)

    progress.close()
    print("END")
    if(total_size == size):
        print("All")
    f.close()


def download(file_name, request):
    global client_id_str
    global WINDOW_SIZE
    global DOWNLOAD_PROGRESS # ?
    print('download')

    try:
        size = int(get_data(UDP_BUFFER_SIZE)[0])
        total_size = 0
        print("size = ")
        print(size)
        send_data(DOWNLOAD_PROGRESS)
    except Exception:
        print('Cannot get information about the file. Please, try again')
        return

    file_name = os.path.basename(file_name)
    if (DOWNLOAD_PROGRESS == 0):
        f = open(file_name, "wb")
    else:
        f = open(file_name, "rb+")

    current_pos = DOWNLOAD_PROGRESS
    print("=====================")

    progress = tqdm.tqdm(range(int(size)), f"Progress of {file_name}:", unit="B", unit_scale=True,
                         unit_divisor=1024)
    progress.update(total_size)
    i = 0
    while (1):
        try:
            data, address, a = udp_recv(UDP_BUFFER_SIZE + 5, 10.0, UDP_DATAGRAMS_AMOUNT)
            # data, address, a = udp_recv(UDP_BUFFER_SIZE + 5, 10.0, UDP_DATAGRAMS_AMOUNT, recv_flags=recv_flags, buffer=buffer)
            if data:
                if data == b'EOF':
                    break
                else:
                    i += 1
                    f.seek(current_pos, 0)
                    f.write(data)
                    # print(len(data))
                    current_pos += len(data)
                total_size+=len(data)
                # print('upd')
                progress.update(len(data))
                # print(total_size)
                if total_size == size:
                    break
            else:
                print("Server disconnected")
                return
            i += 1
            # if i % 40:
            #     time.sleep(0.01)
        except Exception:
            # print("KeyboardInterrupt was handled")
            # send_data("ERROR")
            print('Disconnected from server!')
            
            # try:
            #     for i in range(3):
            #         print('Retrying to connect...')
            #         send_greeting(client_id_str)
            # except Exception:
            #     print('Unable to connect to server.')
            f.close()
            client.close()
            progress.close()
            os._exit(1)
            # break
            # f.close()
            # client.close()
            # progress.close()
            # os._exit(1)
            # progress.close()
    progress.close()
    print("END")
    if size == total_size:
        print("\n" + file_name + " was downloaded")
    f.close()


def send_greeting(client_id):
    global server_address
    # print(client_id)
    # print(str(client_id))
    udp_send(('connect ' + str(client_id)).encode('utf-8'), server_address, UDP_BUFFER_SIZE, 1, True)


#===================UDP END ==========================


print("1 - UDP Client\n2 - TCP Client")

# num = int(input("Введите число: "))
num = 0
while(1):
    num = input('Enter the number: ')
    try:
        num = int(num)
        if num == 1 or num == 2:
            break
    except ValueError:
        pass
    print('Check your input!')   


if num == 2:
    try:
        main()
    except Exception as e:
        print('Server unavailable')
        print(e)
elif num == 1:

    is_valid_address = False

    REGULAR_IP = '^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$'
    regex = re.compile(REGULAR_IP)

    while (is_valid_address == False):
        addr = input("\nInput host address [127.0.0.1 is default]: ")
        if not addr:
            addr = '127.0.0.1'
            # addr = '192.168.1.2'
        if (regex.match(addr)):
            is_valid_address = True
            HOST = addr
        else:
            try:
                HOST = socket.gethostbyname(addr)
                is_valid_address = True
            except socket.error:
                print("Please, input valid address")
                is_valid_address = False

    server_address = (addr, SOCKET_PORT)
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # client.connect(server_address)
    # print("Connected")

    client_id = random.randint(0, 65535)
    print('ID:', client_id)
    # client_id_str = bytes(client_id)
    client_id_str = client_id

    try:
        send_greeting(client_id_str)
    except Exception:
        print('Cannot connect to server!')
        exit(0)
    while True:
        request = input('<< ')
        if not request:
            continue
        command, *params = request.split(' ')
        if command != 'upload' and command != 'download' and command != 'echo' and command != 'exit' and command != 'help' and command != 'time':
            print('Unknowm command. Please, try again')
            continue
        handle_input_request(request)
