# pylint: disable=invalid-name
"""
TextAnalysis - анализатор темы текстов.
Использование:
    Аргумент -h             Отобразить это сообщение
    Аргумент -i <файл>      Обработать текст из файла
    add <тема>              Добавить темы
    remove <тема>           Удалить тему
    list                    Отобразить сохраненные темы
    text <text>             Обработать введенный текст
    Аргумент -t <файл>      Использовать свой словарь тем

Полное использование:
Usage:
    TextAnalysis (-h|--help|--version)
    TextAnalysis [-i=<path>]    [-t=<path>]
    TextAnalysis add <theme>    [-t=<path>]
    TextAnalysis remove <theme> [-t=<path>]
    TextAnalysis list           [-t=<path>]
    TextAnalysis text [-t=<path>] <text>

Options:
    <theme>                   Название темы
    <text>                    Обычный текст
    -i --input_file=<path>    Путь файла с текстом
    -t --themes_file=<path>   Путь файла с темами

"""
import socket
import threading

from docopt import docopt

from __init__ import __version__
from main import main
# Модуль socketserver для сетевого программирования
from socketserver import *

# данные сервера
host = 'pythonapp'
port = 777
addr = (host, port)

DEFAULT_ARG = {
    '--themes_file': './demo_data/themes.json',
    '--input_file': './demo_data/input.txt',
}


class ClientThread(threading.Thread):

    def __init__(self, clientAddress, clientsocket):
        threading.Thread.__init__(self)
        self.csocket = clientsocket
        print("New connection added: ", clientAddress)

    def run(self):
        print("Connection from : ", clientAddress)
        # self.csocket.send(bytes("Hi, This is from Server..",'utf-8'))
        msg = ''
        while True:
            data = ""
            args = docopt(__doc__, version=__version__)
            args['use_local_files'] = 0  # Флаг использования файлов по умолчанию
            if not args['--themes_file']:
                args['--themes_file'] = DEFAULT_ARG['--themes_file']
                args['use_local_files'] += 1
            if not args['--input_file']:
                args['--input_file'] = DEFAULT_ARG['--input_file']
                args['use_local_files'] += 2

            data = self.csocket.recv(32000)
            if len(data) == 0:
                print("")
                return
            if data == b'CheckHealth':
                self.csocket.send(bytes("{Ready}", 'utf-8'))
                continue
            elif data[:3] == b'Add':
                args['add'] = 1
                args['<theme>'] = data[3:].decode()
            elif data[:6] == b'Remove':
                args['remove'] = 1
                args['<theme>'] = data[6:].decode()
            elif data[:4] == b'List':
                args['list'] = 1
            elif data[:4] == b'Text':
                args['text'] = 1
                args['<text>'] = data[4:].decode()

            # Запуск
            answer = '{' + main(args) + '}'
            self.csocket.send(bytes(answer, 'utf-8'))


if __name__ == '__main__':
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(addr)
    print("Server started")
    print("Waiting for client request..")
    while True:
        server.listen(1)
        clientsock, clientAddress = server.accept()
        newthread = ClientThread(clientAddress, clientsock)
        newthread.start()
