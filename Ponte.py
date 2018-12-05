#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Ponte.py
Programa que provê acesso à interface serial RS-485 baseada na PRU através de um socket TCP/IP.

Autores : Eduardo Pereira Coelho / Patricia Nallin

Histórico de versões:
05/12/2018 - Execução em paralelo com IOC das fontes do Sirius (sirius-ioc-as-ps.py). Permissao para acesso a porta serial por PVs.
31/10/2018 - Suporte para python3 (python-sirius)
20/06/2017 - Código reestruturado. Adicionado suporte para mais de um cliente simultaneamente.
24/05/2017 - Versão inicial.
"""

# Módulos necessários

from PRUserial485 import *
from siriuspy.search import PSSearch
from epics import caget
import socket
import threading
import time
import sys
import subprocess

PYTHON_VERSION = sys.version_info.major

if PYTHON_VERSION == 2:
    from Queue import Queue
elif PYTHON_VERSION == 3:
    from queue import Queue

# Porta TCP para escutar conexões de clientes

SERVER_PORT = 4000

# Fila com as operações a serem realizadas

queue = Queue()

# Função que retorna uma estampa de tempo (usada pelas mensagens de log)

def time_string():
    return(time.strftime("%d/%m/%Y, %H:%M:%S - ", time.localtime()))


# Verifica se um determinado processo esta rodando e retorna uma lista com os PIDs encontrados

def process_id(proc):
    ps = subprocess.Popen("ps -eaf", shell=True, stdout=subprocess.PIPE)
    output = ps.stdout.read().decode()
    ps.stdout.close()
    ps.wait()
    pids = []
    for line in output.split("\n"):
        if line != "" and line != None:
            if proc in line:
                pids.append(line.split()[1])
    return pids


# Verifica se IOC está rodando e para qual aplicação as PVs de controle de porta serial apontam

def control_PRUserial485():
    # Master: quem controla a porta serial
    master = "Ponte-py"
    # IOC rodando?
    if (process_id("sirius-ioc-as-ps.py") != []):
        # Verifica status de PVs de controle
        bbbname = socket.gethostname().replace('--', ':')
        bsmp_devs = PSSearch.conv_bbbname_2_psnames(bbbname)
        psnames, bsmp_ids = zip(*bsmp_devs)
        # Se BSMPComm == 1, interface serial esta desbloqueada para o IOC
        if (any(caget(psname + ':BSMPComm-Sts') == 1 for psname in psnames)):
            master = "PS_IOC"
    return master

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

    if PYTHON_VERSION == 2:
        mode = "M"
    elif PYTHON_VERSION == 3:
        mode = b"M"

    PRUserial485_open(6, mode)
    PRUserial485_sync_stop()

    while (True):

        # Retira a próxima operação da fila

        item = queue.get(block = True)

        # Checa se o controle da inteface está com o IOC. Só continua caso a permissão
        # esteja para Ponte-py
        if (control_PRUserial485() == "Ponte-py"):

            # Envia requisição do cliente através da interface serial PRUserial485, com timeout de
            # resposta de 2 s.
            if PYTHON_VERSION == 2:
                message = list(item[1])
            elif PYTHON_VERSION == 3:
                message = [chr(value) for value in item[1]]

            PRUserial485_write(message, 2000.0)

            # Lê a resposta da interface serial
            answer = PRUserial485_read()

        else:
            answer = "SERIAL INTERFACE BLOCKED FOR IOCS"


        # Formata resposta

        if PYTHON_VERSION == 2:
            answer = "".join(answer)
        if PYTHON_VERSION == 3:
            answer = bytearray([ord(c) for c in answer])

        # Envia a resposta ao cliente

        item[0].sendall(answer)

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
