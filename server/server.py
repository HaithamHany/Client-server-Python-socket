import socket
import random
import string
import time
from threading import Thread
import os
from pathlib import Path

root = os.getcwd()
def get_working_directory_info(working_directory):
    """
    Creates a string representation of a working directory and its contents.
    :param working_directory: path to the directory
    :return: string of the directory and its contents.
    """
    dirs = '\n-- ' + '\n-- '.join([i.name for i in Path(working_directory).iterdir() if i.is_dir()])
    files = '\n-- ' + '\n-- '.join([i.name for i in Path(working_directory).iterdir() if i.is_file()])
    dir_info = f'Current Directory: {working_directory}:\n|{dirs}{files}'
    return dir_info


def generate_random_eof_token():
    """Helper method to generates a random token that starts with '<' and ends with '>'.
     The total length of the token (including '<' and '>') should be 10.
     Examples: '<1f56xc5d>', '<KfOVnVMV>'
     return: the generated token.
     """
    return ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(8))


def receive_message_ending_with_token(active_socket, buffer_size, eof_token):
    """
    Same implementation as in receive_message_ending_with_token() in client.py
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


def handle_cd(current_working_directory, new_working_directory):
    """
    Handles the client cd commands. Reads the client command and changes the current_working_directory variable 
    accordingly. Returns the absolute path of the new current working directory.
    :param current_working_directory: string of current working directory
    :param new_working_directory: name of the sub directory or '..' for parent
    :return: absolute path of new current working directory
    """
    path = os.path.join(current_working_directory, new_working_directory)

    if os.path.exists(path):
        os.chdir(new_working_directory)
    else:
        print(f"{new_working_directory} directory doesn't exist")


def handle_mkdir(current_working_directory, directory_name):
    """
    Handles the client mkdir commands. Creates a new sub directory with the given name in the current working directory.
    :param current_working_directory: string of current working directory
    :param directory_name: name of new sub directory
    """
    path = os.path.join(current_working_directory, directory_name)
    os.mkdir(path)
    print(f"{directory_name} directory has been created")

def handle_rm(current_working_directory, object_name):
    """
    Handles the client rm commands. Removes the given file or sub directory. Uses the appropriate removal method
    based on the object type (directory/file).
    :param current_working_directory: string of current working directory
    :param object_name: name of sub directory or file to remove
    """

    path = current_working_directory +'\\'+ object_name;

    if os.path.isdir(path):
        os.rmdir(object_name)
    elif os.path.isfile(path):
        os.remove(object_name)
        print(f"{object_name} has been removed")
    else:
        print(f"file {object_name} has been attempted to be removed but file doesn't exist")


def handle_ul(current_working_directory, file_name, service_socket, eof_token):
    """
    Handles the client ul commands. First, it reads the payload, i.e. file content from the client, then creates the
    file in the current working directory.
    Use the helper method: receive_message_ending_with_token() to receive the message from the client.
    :param current_working_directory: string of current working directory
    :param file_name: name of the file to be created.
    :param service_socket: active socket with the client to read the payload/contents from.
    :param eof_token: a token to indicate the end of the message.
    """
    file_content = receive_message_ending_with_token(service_socket, 1024, eof_token)
    path = current_working_directory +'\\'+ file_name

    if os.path.exists(current_working_directory):
        with open(path, 'wb+') as f:
            f.write(file_content)
            f.close()

        print(f"content of {file_name} has been uploaded")


def handle_dl(current_working_directory, file_name, service_socket, eof_token):
    """
    Handles the client dl commands. First, it loads the given file as binary, then sends it to the client via the
    given socket.
    :param current_working_directory: string of current working directory
    :param file_name: name of the file to be sent to client
    :param service_socket: active service socket with the client
    :param eof_token: a token to indicate the end of the message.
    """
    path = current_working_directory + '\\' + file_name

    if os.path.isfile(file_name):
        with open(path, 'rb') as f:
            file_content = f.read()

        file_content_with_token = file_content + eof_token.encode()
        service_socket.sendall(file_content_with_token)
        print(f"content of {file_name} is being downloaded")
        return

    service_socket.sendall('invalid'.encode() + eof_token.encode())


class ClientThread(Thread):
    def __init__(self, service_socket: socket.socket, address: str):
        Thread.__init__(self)
        self.service_socket = service_socket
        self.address = address

    def run(self):
        # initialize the connection
        print("Connection from : ", self.address)

        random_eof_token = '<' + generate_random_eof_token() + '>'

        # establish working directory,'
        current_working_directory = get_working_directory_info(os.path.abspath(root))
        current_directory_with_token = current_working_directory.encode() + random_eof_token.encode()

        # send random eof token
        self.service_socket.sendall(random_eof_token.encode())
        print(f'Sent EOF token  "{random_eof_token.encode()}" to: {self.address}')

        # send the current dir info
        time.sleep(0.5)
        self.service_socket.sendall(current_directory_with_token)
        print(f'Sent CWD to: {self.address}')

        # get the command and arguments and call the corresponding method
        while True:
            command = receive_message_ending_with_token(self.service_socket, 1024, random_eof_token)
            split = command.decode().split(' ')
            command = split[0]

            if len(split) > 1:
                argument = split[1]

            print(f'Received {command} {argument} from:', self.address)
            if command == 'exit':
                print('Exiting the application.')
                self.service_socket.close()
                print('Connection closed from:', self.address)
                break
            elif command == 'cd':
                handle_cd(os.getcwd(), argument)
            elif command == 'mkdir':
                handle_mkdir(os.getcwd(), argument)
            elif command == 'rm':
                handle_rm(os.getcwd(), argument)
            elif command == 'ul':
                handle_ul(os.getcwd(), argument, self.service_socket, random_eof_token)
            elif command == 'dl':
                handle_dl(os.getcwd(), argument, self.service_socket, random_eof_token)

            # send current dir info
            updated_directory = get_working_directory_info(os.path.abspath(os.getcwd())).encode() + random_eof_token.encode()
            self.service_socket.sendall(updated_directory)


def main():
    HOST = "127.0.0.1"
    PORT = 65432

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        while True:
            conn, addr = s.accept()
            client_thread = ClientThread(conn, addr)
            client_thread.start()


if __name__ == '__main__':
    main()
