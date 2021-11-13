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

#===================UDP start=========================
WINDOW_SIZE = 4096

UDP_BUFFER_SIZE = 1024
TIMEOUT = 20
DOWNLOAD_PROGRESS = 0
OK_STATUS = 200

datagram_count_in = 0
datagram_count_out = 0


def udp_send(data, addr, bytes_amount, datagrams_amount):
    global datagram_count_out
    datagram_count_out_old = datagram_count_out
    print('Send')
    print('start ', datagram_count_out)
    data_part = str()
    for i in range(datagrams_amount):
        temp = format(datagram_count_out, '05d')
        print('===iteration ', i)
        data_part = data[:bytes_amount]
        data_part = str.encode(temp + data_part)
        print(data_part)
        print(data)
        client.sendto(data_part, addr)
        data = data[bytes_amount:]
        # datagram_count_out += 1
        if datagram_count_out == 99999:
            datagram_count_out = 0
        else:
            datagram_count_out += 1

    seq_num = client.recvfrom(bytes_amount)
    
    seq_num_int = int(seq_num[0])
    print(seq_num_int)
    print('datagram_count_out_old ', datagram_count_out_old)
    print('datagrams_amount ', datagrams_amount)
    print('seq_num_int ', seq_num_int)
    print('datagram_count_out ', datagram_count_out)
    if 99999 - datagram_count_out_old < datagrams_amount and seq_num_int >= 0 and seq_num_int < datagrams_amount - (99999 - datagram_count_out_old):
        sent_amount = 99999 - datagrams_amount + 1 + seq_num_int
    else:
        sent_amount = seq_num_int - datagram_count_out_old

    if datagram_count_out == int(seq_num[0]):
        datagram_count_out = int(seq_num[0])
        print('finish ', datagram_count_out)
        return True, sent_amount
    else:
        print('finish ', datagram_count_out)
        return False, sent_amount


def udp_recv(bytes_amount, timeout, datagrams_amount):
    global datagram_count_in 
    print('Recv')
    print('start ', datagram_count_in)
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
    
    for i in range(datagrams_amount):
        recv_flags.append(False)
        # seq_nums.append(0)
        buffer.append(bytes())

    for i in range(datagrams_amount):
        print('===iteration ', i)
        try:
            data_temp, addr = client.recvfrom(bytes_amount)
            recv_flag = True
            print(data_temp)
            seq_num_str = data_temp[:5]
            seq_num = int(seq_num_str)
            print('seq_num', seq_num)
        except Exception:
            print('bbbbbb')
            exc_flag = True
            break
        # if not error_flag:
        
        print('seq_num', seq_num)
        if 99999 - datagram_count_in < datagrams_amount and seq_num >= 0 and seq_num < datagrams_amount - (99999 - datagram_count_in) - 1:
            seq_num_temp = 99999 + 1 + seq_num
        else:
            seq_num_temp = seq_num
        print('datagram_count_in', datagram_count_in)
        print('datagrams_amount', datagrams_amount)

        if seq_num_temp >= datagram_count_in and seq_num_temp < datagram_count_in + datagrams_amount:
            recv_flags[seq_num_temp - datagram_count_in] = not recv_flags[seq_num_temp - datagram_count_in]

            # seq_nums[seq_num - datagram_count_in] = seq_num
            buffer[seq_num_temp - datagram_count_in] = bytes(data_temp[5:])


            # print(datagram_count_in_temp)
            # data += data_temp
        print(recv_flags)
        print(buffer)
    
    if all(b==True for b in recv_flags):
        for i in range(datagrams_amount):
            data += buffer[i]
        if datagram_count_in + datagrams_amount >= 99999:
            datagram_count_in = datagrams_amount - (99999 - datagram_count_in) - 1
        else:
            datagram_count_in += datagrams_amount
    else:
        for i in range(datagrams_amount):
            if recv_flags[i] == True:
                data += buffer[i]
                if datagram_count_in == 99999:
                    datagram_count_in = 0
                else:
                    datagram_count_in += 1
            else:
                break
        
    print('finish ', datagram_count_in)

    if recv_flag:
        temp = format(datagram_count_in, '05d')
        client.sendto(str.encode(temp), addr)
    else:
        addr = None
    
    return data, addr, exc_flag


def get_data():
    # data, address = client.recvfrom(UDP_BUFFER_SIZE)
    data, address, a = udp_recv(1024, None, 1)
    data = data.decode('utf-8')
    return [data, address]

def send_data(data):
    client.sendto(str(data).encode('utf-8'), server_address)


def handle_input_request(request):
    data = request.split()
    command = data[0]

    if (len(data) == 2):
        params = data[1]

    if (command == "echo"):
        # send_data(request)
        udp_send(request, server_address, 1024, 1)
        if (wait_for_ack(command) == False):
            print('bbbbbbbbbbbbbbbbbb')
            return
        
        echo()

    if (command == "time"):
        send_data(request)
        if (wait_for_ack(command) == False):
            return
        get_time()

    if (command == "download"):
        send_data(request)
        if (wait_for_ack(command) == False):
            return
        download(params, request)


    if (command == "exit"):
        send_data(request)
        if (wait_for_ack(command) == False):
            return
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
        response, a, b = udp_recv(1024, 10.0, 1)
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


def download(file_name, request):
    global WINDOW_SIZE

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
            data = client.recvfrom(UDP_BUFFER_SIZE)[0]
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
                        send_data(current_pos)
                total_size+=len(data)
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
            os._exit(1)
            progress.close()
    print("END")
    progress.close()
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
num = int(input("Введите число: "))
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
        addr = input("\nInput host addres: ")
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
        handle_input_request(request)
