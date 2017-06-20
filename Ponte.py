#!/usr/bin/python
# -*- coding: utf-8 -*-


"""


Ponte.py
Programa que provê acesso à interface serial RS-485 baseada na PRU através de um socket TCP/IP.

Autor: Eduardo Pereira Coelho


Histórico de versões:

20/06/2017 - Código reestruturado. Adicionado suporte para mais de um cliente simultaneamente.

24/05/2017 - Versão inicial.


"""

# Módulos necessários

from PRUserial485 import *
from Queue import Queue
import socket
import threading
import time
import sys

# Porta TCP para escutar conexões de clientes

SERVER_PORT = 4000

# Fila com as operações a serem realizadas 

queue = Queue()

# Função que retorna uma estampa de tempo (usada pelas mensagens de log)

def time_string():
    return(time.strftime("%d/%m/%Y, %H:%M:%S - ", time.localtime()))

# Procedimento que escuta requisições de um determinado cliente

def client_thread(client_connection, client_address):

    while (True):

        # Lê mensagem do cliente

        data = client_connection.recv(32768)

        if (data):

            # Se há uma nova mensagem, é necessário processá-la

            queue.put([client_connection, data])

        else:

            # Caso contrário, registra a desconexão do cliente

            sys.stdout.write(time_string() + "Cliente " + client_address[0] + " desconectado.\n")
            sys.stdout.flush()
            break

# Thread que processa a fila de operações a serem realizadas através da interface serial

def queue_processing_thread():

    # Inicialização da interface PRUserial485 (como mestre serial a 6 Mbps)

    PRUserial485_open(6, "M")
    PRUserial485_sync_stop()

    while (True):

        # Retira a próxima operação da fila

        item = queue.get(block = True)

        # Envia requisição do cliente através da interface serial PRUserial485, com timeout de
        # resposta de 2 s.

        PRUserial485_write(list(item[1]), 2000.0)

        # Lê a resposta da interface serial

        answer = PRUserial485_read()

        # Envia a resposta ao cliente

        item[0].sendall("".join(answer))

# Procedimento principal

if (__name__ == "__main__"):

    # Cria o socket para o servidor TCP/IP

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("", SERVER_PORT))
    server_socket.listen(5)

    # Imprime mensagem inicial

    sys.stdout.write("Ponte.py\n")
    sys.stdout.write(time_string() + "Servidor TCP/IP na porta " + str(SERVER_PORT) + " para ponte com interface serial PRUserial485 inicializado.\n")
    sys.stdout.flush()

    # Cria thread que irá processar a fila de requisições

    new_thread = threading.Thread(target = queue_processing_thread)
    new_thread.setDaemon(True)
    new_thread.start()

    while (True):

        # Espera pela conexão de um cliente

        connection, address  = server_socket.accept()

        # Imprime mensagem na tela informando uma nova conexão

        sys.stdout.write(time_string() + "Cliente " + address[0] + " conectado.\n")
        sys.stdout.flush()

        # Lança a thread que irá escutar as requisições do cliente

        new_thread = threading.Thread(target = client_thread, args = (connection, address))
        new_thread.setDaemon(True)
        new_thread.start()    
