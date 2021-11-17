import os
import socket
import tqdm
import regex
import random
import re
import time

SEPARATOR = "<SEPARATOR>"
BUFFER_SIZE = 1024 * 32  # 8KB
SOCKET_PORT = 50015


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

UDP_BUFFER_SIZE = 2048
TIMEOUT = 20
DOWNLOAD_PROGRESS = 0
OK_STATUS = 200
UDP_DATAGRAMS_AMOUNT = 50

datagram_count_in = 0
datagram_count_out = 0


def udp_send(data, addr, bytes_amount, datagrams_amount):
    global datagram_count_out
    datagram_count_out_old = datagram_count_out
    # repeat_flag = False
    # print('Send')
    # print('start ', datagram_count_out)
    data_part = bytes()
    data_temp = bytes(data)
    while(True):
        data = bytes(data_temp)
        for i in range(datagrams_amount):
            temp = format(datagram_count_out, '05d').encode('utf-8')
            # print('===iteration ', i)
            data_part = data[:bytes_amount]
            data_part = temp + data_part
            # repeat_flag = False
            # print(data_part)
            # print(data)
            client.sendto(data_part, addr)
            data = data[bytes_amount:]
            # datagram_count_out += 1
            if datagram_count_out == 99999:
                datagram_count_out = 0
            else:
                datagram_count_out += 1

        try:
            client.settimeout(3.0)
            seq_num = client.recvfrom(5)
            client.settimeout(None)
        except Exception:
            # print('Exc')
            # repeat_flag = True
            # i -= 1
            if datagram_count_out == 0:
                datagram_count_out = 99999
            else:
                datagram_count_out -= 1
            continue
        try:    
            seq_num_int = int(seq_num[0])
        except Exception:
            datagram_count_out = datagram_count_out_old
            continue
        # print(seq_num_int)
        # print('datagram_count_out_old ', datagram_count_out_old)
        # print('datagrams_amount ', datagrams_amount)
        # print('seq_num_int ', seq_num_int)
        # print('datagram_count_out ', datagram_count_out)
        if 99999 - datagram_count_out_old < datagrams_amount and seq_num_int >= 0 and seq_num_int < datagrams_amount - (99999 - datagram_count_out_old):
            sent_amount = 99999 - datagrams_amount + 1 + seq_num_int
        else:
            sent_amount = seq_num_int - datagram_count_out_old

        if datagram_count_out == int(seq_num[0]):
            datagram_count_out = int(seq_num[0])
            # print('finish ', datagram_count_out)
            return True, sent_amount
        else:
            # print('finish ', datagram_count_out)
            return False, sent_amount

def udp_recv1(bytes_amount, timeout, datagrams_amount):
    global datagram_count_in 
    print('Recv')
    # print('start ', datagram_count_in)
    # datagram_count_in_temp = datagram_count_in
    # error_flag = False
    exc_flag = False
    recv_flag = False
    client.settimeout(timeout)
    data = bytes()

    recv_flags = []
    # seq_nums = []
    buffer = []
    addr = '0.0.0.0'
    
    # for i in range(datagrams_amount):
    #     recv_flags.append(False)
    #     # seq_nums.append(0)
    #     buffer.append(bytes())
    print('AAAA')

    for i in range(datagrams_amount):
        print('===iteration ', i)
        try:
            data_temp, addr = client.recvfrom(bytes_amount)
            recv_flag = True
            # print(data_temp)
            seq_num_str = data_temp[:5]
            seq_num = int(seq_num_str)
            # print('seq_num', seq_num)
        except Exception:
            # print('bbbbbb')
            exc_flag = True
            break

        if seq_num == datagram_count_in:
            data += data_temp[5:]
            if datagram_count_in == 99999:
                datagram_count_in = 0
            else:
                datagram_count_in += 1
        else:
            break

        # if 99999 - datagram_count_in < datagrams_amount and seq_num >= 0 and seq_num < datagrams_amount - (99999 - datagram_count_in) - 1:
        #     seq_num_temp = 99999 + 1 + seq_num
        # else:
        #     seq_num_temp = seq_num
        # if seq_num_temp >= datagram_count_in and seq_num_temp < datagram_count_in + datagrams_amount:
        #     recv_flags[seq_num_temp - datagram_count_in] = not recv_flags[seq_num_temp - datagram_count_in]

            # buffer[seq_num_temp - datagram_count_in] = bytes(data_temp[5:])
    # if all(b==True for b in recv_flags):
    #     for i in range(datagrams_amount):
    #         data += buffer[i]
    #     if datagram_count_in + datagrams_amount > 99999:
    #         datagram_count_in = datagrams_amount - (99999 - datagram_count_in) - 1
    #     else:
    #         datagram_count_in += datagrams_amount
    # else:
    #     for i in range(datagrams_amount):
    #         if recv_flags[i] == True:
    #             data += buffer[i]
    #             if datagram_count_in == 99999:
    #                 datagram_count_in = 0
    #             else:
    #                 datagram_count_in += 1
    #         else:
    #             break
        
    # print('finish ', datagram_count_in)

    if recv_flag:
        temp = format(datagram_count_in, '05d')
        client.sendto(str.encode(temp), addr)
    else:
        addr = None
    
    return data, addr, exc_flag

def udp_recv(bytes_amount, timeout, datagrams_amount):
    global datagram_count_in
    datagram_count_in_old = datagram_count_in 
    # print('Recv')
    # print('start ', datagram_count_in)
    # datagram_count_in_temp = datagram_count_in
    # error_flag = False
    exc_flag = False
    recv_flag = False
    client.settimeout(timeout)
    data = bytes()

    i_temp = 0
    recv_flags = []
    # seq_nums = []
    buffer = []
    addr = '0.0.0.0'
    
    for i in range(datagrams_amount):
        recv_flags.append(False)
        # seq_nums.append(0)
        buffer.append(bytes())

    while 1:
        for i in range(i_temp, datagrams_amount):
            # print('===iteration ', i)
            try:
                client.settimeout(1.0)
                data_temp, addr = client.recvfrom(bytes_amount)
                client.settimeout(None)
                # print('===iteration ', i)
                recv_flag = True
                # print(data_temp)
                seq_num_str = data_temp[:5]
                seq_num = int(seq_num_str)
                # print('seq_num', seq_num)
            except Exception:
                input(f'bbbbbb{i} {seq_num}')
                exc_flag = True
                break
            # if not error_flag:
            
            # print('seq_num', seq_num)
            if 99999 - datagram_count_in < datagrams_amount and seq_num >= 0 and seq_num < datagrams_amount - (99999 - datagram_count_in) - 1:
                seq_num_temp = 99999 + 1 + seq_num
            else:
                seq_num_temp = seq_num
            # print('datagram_count_in', datagram_count_in)
            # print('datagrams_amount', datagrams_amount)

            if seq_num_temp >= datagram_count_in and seq_num_temp < datagram_count_in + datagrams_amount:
                recv_flags[seq_num_temp - datagram_count_in] = not recv_flags[seq_num_temp - datagram_count_in]

                # seq_nums[seq_num - datagram_count_in] = seq_num
                buffer[seq_num_temp - datagram_count_in] = bytes(data_temp[5:])


                # print(datagram_count_in_temp)
                # data += data_temp
            # print(recv_flags)
            # print(buffer)
        
        if all(b==True for b in recv_flags):
            # print('aaaaa2')
            for j in range(datagrams_amount):
                recv_flags[j] = False
                data += buffer[j]
            if datagram_count_in + datagrams_amount > 99999:
                # print('overflow')
                datagram_count_in = datagrams_amount - (99999 - datagram_count_in) - 1
            else:
                datagram_count_in += datagrams_amount

            # print('aaaaa1')
            temp = format(datagram_count_in, '05d')
            # print(temp)
            client.sendto(str.encode(temp), addr)
            break
        else:
            # print('aaaaa3')
            for j in range(datagrams_amount):
                if recv_flags[j] == True:
                    data += buffer[j]
                    recv_flags[j] = False
                    if datagram_count_in == 99999:
                        datagram_count_in = 0
                    else:
                        datagram_count_in += 1
                else:
                    break
            i_temp = datagram_count_in - datagram_count_in_old
            datagram_count_in_old = datagram_count_in
            # print('bbbbbb1')
            temp = format(datagram_count_in, '05d')
            # print(temp)
            client.sendto(str.encode(temp), addr)
            continue
                    
                    

        
    # print('finish ', datagram_count_in)

    # if recv_flag:
    #     print('aaaaa1')
    #     temp = format(datagram_count_in, '05d')
    #     print(temp)
    #     client.sendto(str.encode(temp), addr)
    else:
        addr = None
    
    return data, addr, exc_flag


def get_data():
    # data, address = client.recvfrom(UDP_BUFFER_SIZE)
    data, address, a = udp_recv(UDP_BUFFER_SIZE, None, 1)
    data = data.decode('utf-8')
    return [data, address]

def send_data(data):
    # client.sendto(str(data).encode('utf-8'), server_address)
    udp_send(str(data).encode('utf-8'), server_address, UDP_BUFFER_SIZE, 1)


def handle_input_request(request):
    data = request.split()
    command = data[0]

    if (len(data) == 2):
        params = data[1]

    if (command == "echo"):
        send_data(request)
        # udp_send(request, server_address, 1024, 1)
        # if (wait_for_ack(command) == False):
        #     print('bbbbbbbbbbbbbbbbbb')
        #     return
        
        echo()

    if (command == "time"):
        send_data(request)
        # if (wait_for_ack(command) == False):
        #     return
        get_time()

    if (command == "download"):
        send_data(request)
        if (wait_for_ack(command) == False):
            return
        print('ddddddddddddd')
        download(params, request)

    if (command == "upload"):
        send_data(request)
        if (wait_for_ack(command) == False):
            return
        print('ddddddddddddd')
        upload(params)

    if (command == "help"):
        print("help - to see list of commands\n\
                exit - to quit\n\
                echo - to resend message to a client\n\
                upload - to upload file on the server\n\
                download - to download file from a server\n\
                time - get server time\
                ")

    if (command == "exit"):
        # send_data(request)
        # if (wait_for_ack(command) == False):
        #     return
        client.close()
        os._exit(1)

# def wait_for_ack(command_to_compare):
#     while True:
#         response = get_data()[0].split(" ", 2)

#         if not response:
#             return False

#         sent_request = response[0]
#         status = response[1]

#         if (len(response) > 2):
#             message = response[2]
#         else: message = None

#         if (command_to_compare == sent_request and int(status) == OK_STATUS):
#             return True
#         elif (message):
#             print(message)
#             return False
#         else:
#             return False

def wait_for_ack(command_to_compare):
    while True:
    # for i in range(10):

        # response = get_data()[0].split(" ", 2)
        response, a, b = udp_recv(UDP_BUFFER_SIZE, 10.0, 1)
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

        print('44444444444444')
        print(command_to_compare)
        print(sent_request)
        print(int(status))
        print(OK_STATUS)



        if (command_to_compare == sent_request and int(status) == OK_STATUS):
            return True
        elif (message):
            print('222222222')
            print(message)
            return False
        else:
            print('33333333333')
            return False

def echo():
    print(get_data()[0])

def get_time():
    print(get_data()[0])


def upload(file_name):
    f = open(file_name, "rb+")

    size = int(os.path.getsize(file_name))
    total_size=0

    print("File size: %f" % (size))
    send_data(size)

    data_size_recv = int(get_data()[0])

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
    global WINDOW_SIZE
    global DOWNLOAD_PROGRESS # ?

    send_data(WINDOW_SIZE)
    print("WINDOW_SIZE = ")
    WINDOW_SIZE = int(get_data()[0])
    server_window = WINDOW_SIZE
    print(WINDOW_SIZE)
    size = int(get_data()[0])
    total_size = 0
    print("size = ")
    print(size)
    send_data(DOWNLOAD_PROGRESS)

    data_size_recv = int(get_data()[0])
    print("data_size_recv = ")
    print(data_size_recv)
    file_name = os.path.basename(file_name)
    if (data_size_recv == 0):
        f = open(file_name, "wb")
    else:
        f = open(file_name, "rb+")

    current_pos = data_size_recv
    print("=====================")
    i = 0

    progress = tqdm.tqdm(range(int(size)), f"Progress of {file_name}:", unit="B", unit_scale=True,
                         unit_divisor=1024)
    progress.update(total_size)
    while (1):
        try:
            # data = client.recvfrom(UDP_BUFFER_SIZE)[0]
            # print('bbbbbbbb')
            data, address, a = udp_recv(UDP_BUFFER_SIZE + 5, None, UDP_DATAGRAMS_AMOUNT)
            if data:
                if data == b'EOF':
                    break
                else:
                    i += 1
                    f.seek(current_pos, 0)
                    f.write(data)
                    current_pos += len(data)
                    server_window = server_window - len(data)
                    if (server_window == 0):
                        server_window = WINDOW_SIZE
                        # send_data(current_pos)
                total_size+=len(data)
                print('upd')
                progress.update(len(data))
                # print(total_size)
                if total_size == size:
                    break


            else:
                print("Server disconnected")
                return

        except KeyboardInterrupt:
            print("KeyboardInterrupt was handled")
            send_data("ERROR")
            f.close()
            client.close()
            progress.close()
            os._exit(1)
            # progress.close()
    progress.close()
    print("END")
    if size == total_size:
        print("\n" + file_name + " was downloaded")
    f.close()


#===================UDP END ==========================

# if __name__ == '__main__':
#     try:
#         main()
#     except Exception as e:
#         print('Server unavailable')
#         print(e)


print("1 - UDP Client\n2 - TCP Client")

# num = int(input("Введите число: "))
num = 0
while(1):
    num = input('Введите число: ')
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
        addr = input("\nInput host address: ")
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
    while True:
        request = input('<<')
        if not request:
            continue
        command, *params = request.split(' ')
        if command != 'upload' and command != 'download' and command != 'echo' and command != 'exit' and command != 'help' and command != 'time':
            print('Unknowm command. Please, try again')
            continue
        handle_input_request(request)
