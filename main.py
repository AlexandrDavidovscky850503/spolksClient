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

#===================UDP start=========================
UDP_BUFFER_SIZE = 32768
TIMEOUT = 20
DOWNLOAD_PROGRESS = 0
OK_STATUS = 200
UDP_DATAGRAMS_AMOUNT = 15
server_address = ('127.0.0.1', SOCKET_PORT)
client_id_str = 0

disconnected_flag = False

datagram_count_in = 0
datagram_count_out = 0


def udp_send(data, addr, bytes_amount, datagrams_amount, greeting_flag = False):
    global datagram_count_out
    fl = False
    datagram_count_out_begin = int(datagram_count_out)
    data_temp = bytes(data)
    i_temp = 0
    seq_num = (-1, '127.0.0.1')
    loop_counter = 0
    while(True):
        loop_counter += 1
        if loop_counter == 3276800:
            raise Exception
        for i in range(i_temp, datagrams_amount):
            loop_counter = 0
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
            if i < datagrams_amount - 1:
                try:
                    fl = False
                    client.settimeout(0)
                    seq_num = client.recvfrom(5)
                    client.settimeout(None)
                    fl = True
                    break

                except Exception:
                    # if exc_counter == 75:
                    #      raise Exception
                    # exc_counter += 1
                    client.settimeout(None)
                    pass
        # print('aaaaaaa')

        if not fl:
            # print('A0A0', datagram_count_out)
            client.settimeout(10)
            seq_num = client.recvfrom(5)

            # print('A1A1', seq_num)
        fl = False
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
                    # print('a')
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
    print('>Receiving information')
    data, address, a = udp_recv(ll + 5, 10, 1)
    print('>Information received ', data)
    data = data.decode('utf-8')
    return [data, address]

def send_data(data):
    global server_address
    print('>Sending information')
    udp_send(str(data).encode('utf-8'), server_address, UDP_BUFFER_SIZE, 1)
    print('>Information sent')


def handle_input_request(request):
    data = request.split()
    command = data[0]

    if len(data) == 2:
        params = data[1]

    try:
        if command == "echo":
            send_data(request)
            echo(len(params))

        elif command == "time":
            send_data(request)
            get_time()

        elif command == "download":
            send_data(request)
            download(params, request)

        elif command == "upload":
            send_data(request)
            upload(params)

        elif command == "help":
            print("help - to see list of commands\n\
                    exit - to quit\n\
                    echo - to resend message to a client\n\
                    upload - to upload file on the server\n\
                    download - to download file from a server\n\
                    time - get server time\
                    ")

        elif command == "exit":
            client.close()
            os._exit(1)
    except Exception:
        print('Cannot process the command. Please, try again')

def echo(l):
    print(get_data(l)[0])

def get_time():
    print(get_data(21)[0])


def upload(file_name):
    global server_address
    global disconnected_flag
    f = open(file_name, "rb+")

    size = int(os.path.getsize(file_name))
    total_size=0

    print("File size: %f" % (size))
    send_data(size)

    data_size_recv = int(get_data(UDP_BUFFER_SIZE)[0])

    f.seek(data_size_recv, 0)
    current_pos = data_size_recv

    progress = tqdm.tqdm(range(int(size)), f"Progress of {file_name}:", unit="B", unit_scale=True,
                        unit_divisor=1024)

    progress.update(total_size)
    while (1):
        try:
            if 1:
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
        except Exception:
            disconnected_flag = True
            print('Disconnected from server!')
            break

    progress.close()
    print("END")
    if(total_size == size):
        print("All")
    f.close()


def download(file_name, request):
    if int(get_data(UDP_BUFFER_SIZE)[0]) != OK_STATUS:
        return
    global disconnected_flag
    global client_id_str
    global DOWNLOAD_PROGRESS # ?
    print('=download=')

    try:
        size = int(get_data(UDP_BUFFER_SIZE)[0])
        total_size = 0
        print("size = ", size)
        # print(size)
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
            if data:
                if 1:
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
        except Exception:        
            disconnected_flag = True
            print('Disconnected from server!')
            # exit(0)
            break
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
    # default_addr = '192.168.1.2'
    default_addr = '127.0.0.1'

    REGULAR_IP = '^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$'
    regex = re.compile(REGULAR_IP)

    while (is_valid_address == False):
        addr = input(f"\nInput host address [{default_addr} is default]: ")
        if not addr:
            addr = default_addr
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
        if disconnected_flag:
            try:
                print('Reconnecting to server...')
                send_greeting(client_id_str)
                disconnected_flag = False
            except Exception:
                print('Cannot connect to server!')
                exit(0)
        request = input('<< ')
        if not request:
            continue
        command, *params = request.split(' ')
        if command != 'upload' and command != 'download' and command != 'echo' and command != 'exit' and command != 'help' and command != 'time':
            print('Unknowm command. Please, try again')
            continue
        handle_input_request(request)
