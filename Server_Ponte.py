#!/usr/bin/python-sirius
# -*- coding: utf-8 -*-

"""
Ponte - IOCs
"""

# Módulos necessários

#from PRUserial485 import *
#from epics import caget
import threading
from queue import Queue
from serial import Serial
import argparse
import logging
import socket
import logging.handlers
import struct
import select
import time
from PRUserial485 import *
import redis
import json

if __name__ == '__main__':

    parser = argparse.ArgumentParser("TCP - Serial Bind")
    parser.add_argument('--debug', dest='debug', action='store_true')

    parser.add_argument("--terminator", default='', help='Termination string.', dest="terminator")

    parser.add_argument("--logging-ip", default='10.128.255.5', help='Remote logging server ip.', dest="logging_ip")
    parser.add_argument("--port", "-p", default=4000,type=int, help='TCP Server port', dest="port")
    parser.add_argument("--tcp-buffer", "-tcpb",
            default=1024,type=int, help='TCP recv buffer', dest="tcp_buffer")
    parser.add_argument("--baudrate", "-b",
            default=115200, type=int,
            help='Serial port baudrate', dest="baudrate")
    parser.add_argument("--serial-buffer-timeout",
            default=0.05, type=float,
            help='Maximum time to wait for the input buffer to fill after the first byte is detected inside the buffer.', dest="ser_buff_tout")
    parser.add_argument("--timeout", "-t", default=0.1,
            type=float, help='Serial port timeout', dest="timeout")
    parser.add_argument("--device", "-d", default='/dev/ttyUSB0', help='Serial port full path', dest="device")

    parser.add_argument("--zero-bytes","-zb", default='ZB', help='What to return when a zero lengh response is returned from the serial port.', dest="zero_bytes")
    args = parser.parse_args()

    zb = args.zero_bytes.encode('utf-8')
    terminator = args.terminator.encode('utf-8')

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('[%(levelname)s] %(message)s', datefmt='%d/%m/%Y %H:%M:%S.%f')

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(formatter)
    consoleHandler.setLevel(logging.INFO)
    logger.addHandler(consoleHandler)


    if args.debug:
        socketHandler = logging.handlers.SocketHandler(args.logging_ip, logging.handlers.DEFAULT_TCP_LOGGING_PORT)
        socketHandler.setFormatter(formatter)
        socketHandler.setLevel(logging.DEBUG)
        logger.addHandler(socketHandler)
        logger.info('Network logging enable {}.'.format(args.logging_ip))

# Porta TCP para escutar conexões de clientes
SERVER_PORT = 5003

# Fila com as operações a serem realizadas
queue = Queue()

# Função que retorna uma estampa de tempo (usada pelas mensagens de log)
def time_string():
    return(time.strftime("%d/%m/%Y, %H:%M:%S - ", time.localtime()))


# Procedimento que escuta requisições de um determinado cliente
def client_thread(client_connection, client_address):

    while (True):

        # Lê mensagem do cliente
        data = client_connection.recv(args.tcp_buffer)

        if (data):
            queue.put([client_connection, data])

        else:
            # Caso contrário, registra a desconexão do cliente
            logger.info(time_string() + "Cliente " + client_address[0] + " desconectado.\n")
            break

# Thread que processa a fila de operações a serem realizadas através da interface serial
def queue_processing_thread():

    r = redis.StrictRedis("127.0.0.1",6379)

    while (True):

        item = queue.get(block = True)
        connection = item[0]
        data = {'message': item[1].decode("latin-1"), 'timeout': 1000}
        r.rpush("queue:write", json.dumps(data))

#        while not r.llen("queue:read"):
#            time.sleep(0.001)

        res = json.loads(r.blpop("queue:read")[1])['message'].encode("latin-1")
#        res = (res + terminator if res else zb + terminator)
#        print(ord(data['message'][4]))
#        print((res[4]*256 +res[5])/100.0)
        connection.sendall(res)

# Procedimento principal

if (__name__ == "__main__"):

    # Cria o socket para o servidor TCP/IP
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("", SERVER_PORT))
    server_socket.listen(1)

    # Imprime mensagem inicial
    logger.info("Ponte.py")
    logger.info(time_string() + "Servidor TCP/IP na porta " + str(SERVER_PORT) + " para ponte com interface serial PRUserial485 inicializado.")

    # Cria thread que irá processar a fila de requisições
    new_thread = threading.Thread(target = queue_processing_thread)
    new_thread.setDaemon(True)
    new_thread.start()

    while (True):

        # Espera pela conexão de um cliente
        connection, address  = server_socket.accept()
        #connection.settimeout(10)

        # Imprime mensagem na tela informando uma nova conexão
        logger.info(time_string() + "Cliente " + address[0] + " conectado.")

        # Lança a thread que irá escutar as requisições do cliente
        new_thread = threading.Thread(target = client_thread, args = (connection, address))
        new_thread.setDaemon(True)
        new_thread.start()



