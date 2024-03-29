import os
import socket
import tqdm
import regex
import random
import re

SOCKET_PORT = 0

#===================UDP start=========================
UDP_BUFFER_SIZE = 1024
TIMEOUT = 20
STATUS_OK = 'OK'
STATUS_NO_FILE = 'NO FILE'
UDP_DATAGRAMS_AMOUNT = 5

DOWNLOAD_SERVICE_PORT = 50001
UPLOAD_SERVICE_PORT = 50002
ECHO_SERVICE_PORT = 50003
TIME_SERVICE_PORT = 50004

server_address = ('127.0.0.1', 0)
dunamic_sock_num = 0

server_download_addr = ('127.0.0.1', DOWNLOAD_SERVICE_PORT)
server_upload_addr = ('127.0.0.1', UPLOAD_SERVICE_PORT)
server_echo_addr = ('127.0.0.1', ECHO_SERVICE_PORT)
server_time_addr = ('127.0.0.1', TIME_SERVICE_PORT)

client_download_sock = None
client_upload_sock = None
client_echo_sock = None
client_time_sock = None

client_id_str = 0

disconnected_flag = False

datagram_count_in = 0
datagram_count_out = 0


def udp_send(data, addr, bytes_amount, datagrams_amount, greeting_flag = False):
    global server_address
    addr = server_address
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


def udp_recv(server_addr, bytes_amount, timeout, datagrams_amount):
    global server_address
    global dunamic_sock_num
    # print('recv')
    global datagram_count_in
    # datagram_count_in_old = datagram_count_in 
    datagram_count_in_begin = datagram_count_in 

    exc_flag = False
    aaa = False
    data = bytes()
    counter = 0
    attempts_counter = 0

    # timeout /= 10

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
                # print('Recv: ', data_temp)

               
                client.settimeout(None)
                
                # print('===iteration ', i)
                seq_num = int(data_temp[:5])
                # print('c', data_temp[:5])
                
                data_temp = data_temp[5:]
                # print('Recv: ', data_temp)
                # print('b', data_temp[:5])
                dunamic_sock_num = int(data_temp[:5])
                # print('dddd', dunamic_sock_num)
                # print('d')
                # print('data', data_temp)
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
                # if aaa and attempts_counter == 10:
                    raise Exception
                # elif aaa:
                    # print('v')
                    # temp = format(datagram_count_in, '05d')
                    # client.sendto(str.encode(temp), server_address)
                    # attempts_counter += 1
                break
            # print('i_temp', i_temp)
            # print(datagram_count_in - datagram_count_in_begin)
            # if datagram_count_in - datagram_count_in_begin > 4:
            #     input('datagram_count_in - datagram_count_in_begin!!!')
            # print('datagram_count_in', datagram_count_in)
            # print('seq_num', seq_num)
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
            # print('aaaaaaa', server_address)
            server_address = list(server_address)
            server_address[1] = dunamic_sock_num
            server_address = tuple(server_address)
            # print(server_address)
            client.sendto(temp.encode('utf-8'), server_address)
            

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
            # print('aaaaa2', server_address)
            server_address = list(server_address)
            # print('aaaaa4', server_address)
            server_address[1] = dunamic_sock_num
            # print('aaaaa5', server_address)
            server_address = tuple(server_address)
            print('aaaaa3', server_address)
            client.sendto(str.encode(temp), server_address)
            continue
         
    return data, addr, exc_flag


def get_data(addr, ll):
    print('>Receiving information')
    data, address, a = udp_recv(addr, ll + 10, 10, 1)
    print('>Information received ', data)
    data = data.decode('utf-8')
    return [data, address]


def send_data(addr, data):
    # global server_address
    print('>Sending information')
    udp_send(str(data).encode('utf-8'), addr, UDP_BUFFER_SIZE, 1)
    print('>Information sent')


def handle_input_request(request):
    global datagram_count_out
    global datagram_count_in
    global server_download_addr
    global server_upload_addr
    global server_echo_addr
    global server_time_addr
    global server_address

    data = request.split()
    command = data[0]

    if len(data) == 2:
        params = data[1]

    try:
        if command == "echo":
            datagram_count_in = 0
            datagram_count_out = 0
            server_address = server_echo_addr
            send_data(server_echo_addr, request)
            print(get_data(server_echo_addr, len(params) + 5)[0])
            # echo(server_echo_addr, len(params) + 5)

        elif command == "time":
            datagram_count_in = 0
            datagram_count_out = 0
            server_address = server_time_addr
            send_data(server_time_addr, request)
            print('Time:', get_data(addr, 26)[0])
            # get_time(server_time_addr)

        elif command == "download":
            datagram_count_in = 0
            datagram_count_out = 0
            server_address = server_download_addr
            send_data(server_download_addr, request)
            download(params, request)

        elif command == "upload":
            datagram_count_in = 0
            datagram_count_out = 0
            server_address = server_upload_addr
            send_data(server_upload_addr, request)
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
            exit(0)
    except Exception as e:
        print('Cannot process the command. Please, try again')
        print(e)


def echo(addr, l):
    print(get_data(addr, l)[0])


def get_time(addr):
    print('Time:', get_data(addr, 26)[0])


def upload(file_name):
    global server_upload_addr
    global disconnected_flag
    global server_upload_addr

    print('=upload=')

    f = open(file_name, "rb+")

    get_data(server_upload_addr, UDP_BUFFER_SIZE)[0]

    size = int(os.path.getsize(file_name))
    total_size=0

    print("File size: ", size)
    send_data(server_upload_addr ,size)

    data_size_recv = int(get_data(server_upload_addr, UDP_BUFFER_SIZE)[0])

    f.seek(data_size_recv, 0)

    progress = tqdm.tqdm(range(int(size)), f"Progress of {file_name}:", unit="B", unit_scale=True,
                        unit_divisor=1024)

    progress.update(total_size)
    while (1):
        try:
            data_file = f.read(UDP_BUFFER_SIZE * UDP_DATAGRAMS_AMOUNT)
            udp_send(data_file, server_upload_addr, UDP_BUFFER_SIZE, UDP_DATAGRAMS_AMOUNT)
            
            total_size+=len(data_file)
            progress.update(len(data_file))
            if total_size == size:
                break
        except Exception:
            disconnected_flag = True
            print('Disconnected from server!')
            break

    progress.close()
    print("End of upload")
    if(total_size == size):
        print(f'File [{file_name}] was sent completely')
    f.close()


def download(file_name, request):
    global disconnected_flag
    global client_id_str
    global server_download_addr

    if get_data(server_download_addr, UDP_BUFFER_SIZE)[0] != STATUS_OK:
        return

    print('=download=')

    try:
        size = int(get_data(server_download_addr, UDP_BUFFER_SIZE)[0])
        total_size = 0
        print("size = ", size)
        # print(size)
        send_data(server_download_addr, 0)
    except Exception as e:
        print('Cannot get information about the file. Please, try again')
        print(e)
        return

    file_name = os.path.basename(file_name)

    f = open(file_name, "wb")

    print("=====================")

    progress = tqdm.tqdm(range(int(size)), f"Progress of {file_name}:", unit="B", unit_scale=True,
                         unit_divisor=1024)
    progress.update(total_size)
    while (1):
        try:
            data, address, a = udp_recv(server_download_addr, UDP_BUFFER_SIZE + 10, 10.0, UDP_DATAGRAMS_AMOUNT)
            if data:                
                f.write(data)

                total_size+=len(data)
                progress.update(len(data))
                if total_size == size:
                    break
            else:
                print("Server disconnected")
                return
        except Exception as e:        
            disconnected_flag = True
            print('Disconnected from server!')
            print(e)
            # exit(0)
            break

    progress.close()
    print("End of upload")
    if size == total_size:
        print(f'File [{file_name}] was received completely')
    f.close()


def send_greeting(client_id):
    global server_address
    udp_send(('connect ' + str(client_id)).encode('utf-8'), server_address, UDP_BUFFER_SIZE, 1, True)


########################################### MAIN ###########################################
is_valid_address = False
# default_addr = '192.168.1.2'
default_addr = '127.0.0.1'

REGULAR_IP = '^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$'
regex = re.compile(REGULAR_IP)

while is_valid_address == False:
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

server_download_addr = (addr, DOWNLOAD_SERVICE_PORT)
server_upload_addr = (addr, UPLOAD_SERVICE_PORT)
server_echo_addr = (addr, ECHO_SERVICE_PORT)
server_time_addr = (addr, TIME_SERVICE_PORT)

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


client_id = random.randint(0, 65535)
print('ID:', client_id)
# client_id_str = bytes(client_id)
client_id_str = client_id

# try:
#     send_greeting(client_id_str)
# except Exception:
#     print('Cannot connect to server!')
#     exit(0)
while True:
    if disconnected_flag:
        try:
            print('Reconnecting to server...')
            # send_greeting(client_id_str)
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
