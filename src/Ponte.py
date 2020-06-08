#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Ponte.py
Programa que provê acesso à interface serial RS-485 baseada na PRU através de um socket TCP/IP.

Autores : Eduardo Pereira Coelho / Patricia Nallin

Histórico de versões:
26/07/2019 - Adicionado suporte para execução em paralelo com o IOC remoto (eth-bridge-pru-serial485)
05/12/2018 - Execução em paralelo com IOC das fontes do Sirius (sirius-ioc-as-ps.py). Permissao para acesso a porta serial por PVs.
31/10/2018 - Suporte para python3 (python-sirius)
20/06/2017 - Código reestruturado. Adicionado suporte para mais de um cliente simultaneamente.
24/05/2017 - Versão inicial.
"""

# Módulos necessários

from PRUserial485 import *
from epics import caget
import socket, threading
import time, sys
import subprocess, importlib
from Queue import Queue
import struct


# Porta TCP para escutar conexões de clientes

SERVER_PORT = 4000

# Fila com as operações a serem realizadas

queue = Queue()

# Funcoes eth-bridge
COMMAND_PRUserial485_write = b'\x03'
COMMAND_PRUserial485_read = b'\x04'



# Função que retorna uma estampa de tempo (usada pelas mensagens de log)

def time_string():
    return(time.strftime("%d/%m/%Y, %H:%M:%S - ", time.localtime()))

'''
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

# Verifica se há conexão estabelecida em determinada(s) porta(s) ethernet.
def remote_ioc_connected(ports = []):
    ports_connected = []
    for port in ports:
        ps = subprocess.Popen("netstat -pant | grep ':{}'".format(port), shell=True, stdout=subprocess.PIPE)
        output = ps.stdout.read().decode()
        ps.stdout.close()
        ps.wait()
        if "ESTABLISHED" in output:
            ports_connected.append(port)
    if ports_connected == []:
        return False
    else:
        return True


# Verifica se IOC está rodando e para qual aplicação as PVs de controle de porta serial apontam
def control_PRUserial485():
    # Master: quem controla a porta serial
    master = "Ponte-py"
    # IOC rodando?
    if (process_id("sirius-ioc-as-ps.py") != [] or remote_ioc_connected(ports = [5000,6000])):
        # Verifica status de PVs de controle
        bbbname = socket.gethostname().replace('--', ':')
        bsmp_devs = PSSearch.conv_bbbname_2_psnames(bbbname)
        psnames, bsmp_ids = zip(*bsmp_devs)
        # Se BSMPComm == 1, interface serial esta desbloqueada para o IOC
        if (any(caget(psname + ':BSMPComm-Sts') == 1 for psname in psnames)):
            master = "PS_IOC"
    return master
'''

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

def payload_length(payload):
    """."""
    return(struct.pack("B", payload[0]) +
           struct.pack(">I", (len(payload)-1)) + payload[1:])



# Thread que processa a fila de operações a serem realizadas através da interface serial

def queue_processing_thread():

    while True:

        socket_eth_bridge = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_eth_bridge.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        socket_eth_bridge.connect(('127.0.0.1', 5000))
        socket_eth_bridge.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)

        while (True):
            try:
                # Retira a próxima operação da fila PONTE-PY
                item = queue.get(block = True)
                
                # Envia requisição do cliente através da interface serial PRUserial485, com timeout de
                # resposta de 2 s.
                message = item[1]

                sending_data = COMMAND_PRUserial485_write + struct.pack(">f", 2000.0)
                sending_data += bytearray([ord(i) for i in message])
                socket_eth_bridge.sendall(payload_length(sending_data))

                try:
                    answer = socket_eth_bridge.recv(6)
                except ConnectionResetError:
                    answer = []

                # Receive data/payload
                payload = b''
                if answer:
                    answer = []
                    socket_eth_bridge.sendall(COMMAND_PRUserial485_read + b'\x00\x00\x00\x00')
                    try:
                        answer = socket_eth_bridge.recv(5)
                    except ConnectionResetError:
                        pass

                    if answer:
                        command_recv = answer[0]
                        data_size = struct.unpack(">I", answer[1:])[0]
                    else:
                        command_recv = b''
                        data_size = 0

                    if data_size:
                        try:
                            for _ in range(int(data_size / 4096)):
                                payload += socket_eth_bridge.recv(4096, socket.MSG_WAITALL)
                            payload += socket_eth_bridge.recv(
                                int(data_size % 4096), socket.MSG_WAITALL)
                        except ConnectionResetError:
                            payload = b''
                        
                # Envia a resposta ao cliente PONTE-PY
                item[0].sendall(payload)

            except:
                pass

# Procedimento principal

if (__name__ == "__main__"):

    # Cria o socket para o servidor TCP/IP

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
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
