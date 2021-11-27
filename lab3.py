import os
import socket
import tqdm
import re
import time
import sys

SEPARATOR = "<SEPARATOR>"
BUFFER_SIZE = 1024
SOCKET_PORT = 19001
TIMEOUT = 20
OK_STATUS = 200

def inputRequestHandle(request):
    data = request.split()
    command = data[0]

    if (len(data) == 2):
        body = data[1]

    if command == "echo":
        client.send(str(request).encode('utf-8'))
        if (ackWait(command) == False):
            return
        print(client.recv(BUFFER_SIZE).decode('utf-8'))

    if command == "time":
        client.send(str(request).encode('utf-8'))
        if (ackWait(command) == False):
            return
        print(client.recv(BUFFER_SIZE).decode('utf-8'))

    if command == "download":
        client.send(str(request).encode('utf-8'))
        if (ackWait(command) == False):
            return
        downloadFile(body, request)

    if command == "exit":
        client.send(str(request).encode('utf-8'))
        if (ackWait(command) == False):
            return
        client.close()
        os._exit(1)

def ackWait(command_to_compare):
    while True:
        response = client.recv(BUFFER_SIZE).decode('utf-8').split(" ", 2)

        if not response:
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

def isServerAviable(request, command):
    global client

    client.close()

    i = TIMEOUT

    while(i > 0):
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((HOST, PORT))
            client.send(request.encode('utf-8'))
            ackWait(command)
            return True

        except socket.error as er:
            sys.stdout.write("Waiting for a server: %d seconds \r" %i)
            sys.stdout.flush()

        i -= 1
        time.sleep(1)

    sys.stdout.flush()
    print("\nServer was disconnected")
    sys.stdout.flush()
    return False


def downloadFile(file_name, request):
    size = int(client.recv(BUFFER_SIZE).decode('utf-8'))
    client.send("OK".encode('utf-8'))
    client.send(str(0).encode('utf-8'))
    data_size_recv = int(client.recv(BUFFER_SIZE).decode('utf-8'))
    client.send("OK".encode('utf-8'))
    progress = tqdm.tqdm(range(size), f"Sending {file_name}", unit="B", unit_scale=True, unit_divisor=1024)
    if (data_size_recv == 0):
        f = open(file_name, "wb")
    else:
        progress.update(len(data_size_recv))
        f = open(file_name, "rb+")

    while (data_size_recv < size):
        try:
            data = client.recv(BUFFER_SIZE)
            f.seek(data_size_recv, 0)
            f.write(data)
            data_size_recv += len(data)
            client.send(str(data_size_recv).encode('utf-8'))
            progress.update(len(data))


        except socket.error as e:
            if(isServerAviable(request, "download")):
                size = int(client.recv(BUFFER_SIZE).decode('utf-8'))
                client.send("OK".encode('utf-8'))
                client.send(str(data_size_recv).encode('utf-8'))
                data_size_recv = int(client.recv(BUFFER_SIZE).decode('utf-8'))
                client.send("OK".encode('utf-8'))
                print("\n")
            else:
                f.close()
                client.close()
                os._exit(1)

        except KeyboardInterrupt:
            print("KeyboardInterrupt was handled")
            f.close()
            client.close()
            os._exit(1)
    progress.close()

    f.close()
    print("\n" + file_name + " was downloaded")


def exit():
    pass

def checkValidRequest(request):
    command = request.split()
    if (len(command) == 0):
        return False
    else: return True



is_valid_address = False

REGULAR_IP = '^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$'
regex = re.compile(REGULAR_IP)


# while (is_valid_address == False):
#     addr = input("\nInput host addres: ")
#     if (regex.match(addr)):
#         is_valid_address = True
#         HOST = addr
#     else:
#         try:
#             HOST = socket.gethostbyname(addr)
#             is_valid_address = True
#         except socket.error:
#             print("Please, input valid address")
#             is_valid_address = False

HOST = '127.0.0.1'

print("Client start")

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, SOCKET_PORT))


while True:

    try:
        request = input()
        if (checkValidRequest(request)):
            inputRequestHandle(request)
    except KeyboardInterrupt:
        print("KeyboardInterrupt was handled")
        client.close()
        os._exit(1)
