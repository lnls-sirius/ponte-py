#!/usr/bin/python-sirius
# -*- coding: utf-8 -*-

# Módulos necessários

from PRUserial485 import *
from epics import caget
import socket
import threading
import time
import sys
import subprocess
from queue import Queue
import struct
import serial
import logging
from logging.handlers import RotatingFileHandler


# LOGS
LOG_PATH_BBB = "/var/www/html/serial/serial.log"
logger = logging.getLogger("Pontepy")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(levelname)s:%(asctime)s:\t%(message)s")
file_handler = RotatingFileHandler(LOG_PATH_BBB, maxBytes=10000000, backupCount=5)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Porta TCP para escutar conexões de clientes

SERVER_PORT = 5002

# Fila com as operações a serem realizadas

queue = Queue()



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
            logger.info("Cliente " + client_address[0] + " desconectado.\n")
            break


# Thread que processa a fila de operações a serem realizadas através da interface serial

def queue_processing_thread():
    s = serial.Serial("/dev/ttyUSB0", 115200, timeout = 0.1)
    while True:
        try:
            while True:
                
                    # Retira a próxima operação da fila PONTE-PY
                    item = queue.get(block = True)
                    
                    message = item[1]
                    s.write(message)
                    time.sleep(0.1)
                    payload = s.read(100)
                    logger.info("OUT: {}\tIN: {}\n".format(message, payload))

                    # Envia a resposta ao cliente PONTE-PY
                    item[0].sendall(payload)
        except:
            time.sleep(1)

# Procedimento principal

if (__name__ == "__main__"):

    # Cria o socket para o servidor TCP/IP

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("", SERVER_PORT))
    server_socket.listen(5)

    # Imprime mensagem inicial

    logger.info("Ponte.py\n")
    logger.info("Servidor TCP/IP na porta " + str(SERVER_PORT) + " para ponte com interface serial PRUserial485 inicializado.\n")

    # Cria thread que irá processar a fila de requisições

    new_thread = threading.Thread(target = queue_processing_thread)
    new_thread.setDaemon(True)
    new_thread.start()

    while (True):

        # Espera pela conexão de um cliente

        connection, address  = server_socket.accept()

        # Imprime mensagem na tela informando uma nova conexão

        logger.info("Cliente " + address[0] + " conectado.\n")

        # Lança a thread que irá escutar as requisições do cliente

        new_thread = threading.Thread(target = client_thread, args = (connection, address))
        new_thread.setDaemon(True)
        new_thread.start()
