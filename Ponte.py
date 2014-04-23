#!/usr/bin/python
# -*- coding: utf-8 -*-

"""


Ponte.py
Programa que provê acesso à interface serial RS-485 baseada na PRU através de um socket TCP/IP.

Autor: Eduardo Pereira Coelho


Histórico de versões:

24/05/2017 - Versão inicial.


"""

# Módulos necessários

from PRUserial485 import *
import socket
import time
import sys

# Porta TCP para escutar conexões de clientes

SERVER_PORT = 4000

# Função que retorna uma estampa de tempo (usada pelas mensagens de log)

def time_string():
    return(time.strftime("%d/%m/%Y, %H:%M:%S - ", time.localtime()))

# Inicialização da interface PRUserial485 (como mestre serial a 6 Mbps)

PRUserial485_open(6, "M")
PRUserial485_sync_stop()

# Cria o socket para o servidor TCP/IP

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(("", SERVER_PORT))
server_socket.listen(1)

# Imprime mensagem inicial

sys.stdout.write("Ponte.py\n")
sys.stdout.write(time_string() + "Servidor TCP/IP na porta " + str(SERVER_PORT) + " para ponte com interface serial PRUserial485 inicializado.\n")
sys.stdout.flush()

while (True):

    # Espera pela conexão de um cliente

    sys.stdout.write(time_string() + "Esperando por uma conexão.\n")
    sys.stdout.flush()

    connection, client_info = server_socket.accept()

    # Imprime uma mensagem na tela informando uma nova conexão

    sys.stdout.write(time_string() + "Cliente " + client_info[0] + " conectado.\n")
    sys.stdout.flush()

    while (True):

        # Lê mensagem do cliente

        data = connection.recv(8192)

        # Se há uma nova mensagem, é necessário processá-la

        if (data):

            # Envia requisição do cliente através da interface serial PRUserial485, com timeout de
            # resposta de 1 s.

            PRUserial485_write(list(data), 1000.0)

            # Lê a resposta da interface serial

            answer = PRUserial485_read()

            # Envia a resposta ao cliente

            connection.sendall("".join(answer))

        else:

            # Registra a desconexão do cliente

            sys.stdout.write(time_string() + "Cliente " + client_info[0] + " desconectado.\n")
            sys.stdout.flush()
            break
