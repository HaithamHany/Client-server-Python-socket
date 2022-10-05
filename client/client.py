import os
import socket

eof_token = None

def receive_message_ending_with_token(active_socket, buffer_size, eof_token):
    """
    Same implementation as in receive_message_ending_with_token() in server.py
    A helper method to receives a bytearray message of arbitrary size sent on the socket.
    This method returns the message WITHOUT the eof_token at the end of the last packet.
    :param active_socket: a socket object that is connected to the server
    :param buffer_size: the buffer size of each recv() call
    :param eof_token: a token that denotes the end of the message.
    :return: a bytearray message with the eof_token stripped from the end.
    """
    message_content = bytearray()
    while True:
        packet = active_socket.recv(buffer_size)
        if packet[-10:] == eof_token.encode():
            message_content += packet[:-10]
            break
        message_content += packet

    return message_content




def initialize(host, port):
    """
    1) Creates a socket object and connects to the server.
    2) receives the random token (10 bytes) used to indicate end of messages.
    3) Displays the current working directory returned from the server (output of get_working_directory_info() at the server).
    Use the helper method: receive_message_ending_with_token() to receive the message from the server.
    :param host: the ip address of the server
    :param port: the port number of the server
    :return: the created socket object
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    print('Connected to server at IP:', host, 'and Port:', port)

    while True:
        packet = s.recv(1024)
        if packet is not None:
            global eof_token
            eof_token = packet.decode()
            break
    print('Handshake Done. EOF is:', eof_token)

    current_working_directory = receive_message_ending_with_token(s, 1024, eof_token)

    print(current_working_directory.decode())

    return s


def issue_cd(command_and_arg, client_socket, eof_token):
    """
    Sends the full cd command entered by the user to the server. The server changes its cwd accordingly and sends back
    the new cwd info.
    Use the helper method: receive_message_ending_with_token() to receive the message from the server.
    :param command_and_arg: full command (with argument) provided by the user.
    :param client_socket: the active client socket object.
    :param eof_token: a token to indicate the end of the message.
    """
    command_with_token = command_and_arg.encode() + eof_token.encode()
    client_socket.sendall(command_with_token)
    split = command_and_arg.split(' ')
    dir_name = split[1]
    print(f'Current working directory has been changed to "{dir_name}"')

    cwd = receive_message_ending_with_token(client_socket, 1024, eof_token)
    print(cwd.decode())

def issue_mkdir(command_and_arg, client_socket, eof_token):
    """
    Sends the full mkdir command entered by the user to the server. The server creates the sub directory and sends back
    the new cwd info.
    Use the helper method: receive_message_ending_with_token() to receive the message from the server.
    :param command_and_arg: full command (with argument) provided by the user.
    :param client_socket: the active client socket object.
    :param eof_token: a token to indicate the end of the message.
    """
    command_with_token = command_and_arg.encode() + eof_token.encode()
    client_socket.sendall(command_with_token)
    split = command_and_arg.split(' ')
    dir_name = split[1]
    print(f'Directory "{dir_name}" has been created')

    cwd = receive_message_ending_with_token(client_socket, 1024, eof_token)
    print(cwd.decode())

def issue_rm(command_and_arg, client_socket, eof_token):
    """
    Sends the full rm command entered by the user to the server. The server removes the file or directory and sends back
    the new cwd info.
    Use the helper method: receive_message_ending_with_token() to receive the message from the server.
    :param command_and_arg: full command (with argument) provided by the user.
    :param client_socket: the active client socket object.
    :param eof_token: a token to indicate the end of the message.
    """
    command_with_token = command_and_arg.encode() + eof_token.encode()
    client_socket.sendall(command_with_token)
    split = command_and_arg.split(' ')
    filename_argument = split[1]
    print(f'Removed "{filename_argument}" from server')

    cwd = receive_message_ending_with_token(client_socket, 1024, eof_token)
    print(cwd.decode())


def issue_ul(command_and_arg, client_socket, eof_token):
    """
    Sends the full ul command entered by the user to the server. Then, it reads the file to be uploaded as binary
    and sends it to the server. The server creates the file on its end and sends back the new cwd info.
    Use the helper method: receive_message_ending_with_token() to receive the message from the server.
    :param command_and_arg: full command (with argument) provided by the user.
    :param client_socket: the active client socket object.
    :param eof_token: a token to indicate the end of the message.
    """
    #Sending the full ul command

    command_with_token = command_and_arg.encode() + eof_token.encode()
    client_socket.sendall(command_with_token)
    split = command_and_arg.split(' ')
    filename_argument = split[1]

    print(f'Sent {command_and_arg} Command  to server')

    # Read file to be uploaded

    path = os.path.join(os.getcwd(), filename_argument)
    if os.path.exists(path):
        with open(filename_argument, 'rb') as f:
            file_content = f.read()

        # Send the read file to the server
        file_content_with_token = file_content + eof_token.encode()
        client_socket.sendall(file_content_with_token)
        print(f'Sent the contents of "{filename_argument}" to server')
        # Receiving the current working directory using the helper method
        cwd = receive_message_ending_with_token(client_socket, 1024, eof_token)
        print(cwd.decode())
    else:
        print(f'{filename_argument} doesnt exist')

def issue_dl(command_and_arg, client_socket, eof_token):
    """
    Sends the full dl command entered by the user to the server. Then, it receives the content of the file via the
    socket and re-creates the file in the local directory of the client. Finally, it receives the latest cwd info from
    the server.
    Use the helper method: receive_message_ending_with_token() to receive the message from the server.
    :param command_and_arg: full command (with argument) provided by the user.
    :param client_socket: the active client socket object.
    :param eof_token: a token to indicate the end of the message.
    :return:
    """
    command_with_token = command_and_arg.encode() + eof_token.encode()
    client_socket.sendall(command_with_token)

    split = command_and_arg.split(' ')
    filename_argument = split[1]
    file_content = receive_message_ending_with_token(client_socket, 1024, eof_token)

    path = os.getcwd() + '\\' + filename_argument

    with open(path, 'wb') as f:
        f.write(file_content)
        f.close()

    cwd = receive_message_ending_with_token(client_socket, 1024, eof_token)
    print(cwd.decode())


def main():
    HOST = "127.0.0.1"  # The server's hostname or IP address
    PORT = 65432  # The port used by the server

    # initialize
    client_socket = initialize(HOST, PORT)

    while True:
        # get user input
        command_with_args = input('Enter command : ')
        split = command_with_args.split(' ')
        command = split[0]

        # call the corresponding command function or exit
        if command == 'exit':
            print('Exiting the application.')
            break
        elif command == 'cd':
            issue_cd(command_with_args, client_socket , eof_token)
        elif command == 'mkdir':
            issue_mkdir(command_with_args, client_socket , eof_token)
        elif command == 'rm':
            issue_rm(command_with_args, client_socket , eof_token)
        elif command == 'ul':
            issue_ul(command_with_args, client_socket , eof_token)
        elif command == 'dl':
            issue_dl(command_with_args, client_socket, eof_token)


if __name__ == '__main__':
    main()