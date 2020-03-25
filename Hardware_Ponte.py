#!/usr/bin/python-sirius
# -*- coding: utf-8 -*-

"""
Ponte - IOCs
"""

# Módulos necessários
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
            default=0.02, type=float,
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
SERVER_PORT = 4000

# Fila com as operações a serem realizadas
queue = Queue()

# Função que retorna uma estampa de tempo (usada pelas mensagens de log)
def time_string():
    return(time.strftime("%d/%m/%Y, %H:%M:%S - ", time.localtime()))


# Thread que processa a fila de operações a serem realizadas através da interface serial
def queue_processing_thread():

    # Inicialização da interface PRUserial485 (como mestre serial a 6 Mbps)
#    PRUserial485_open(6, b"M")
#    PRUserial485_sync_stop()
    ser = Serial("/dev/ttyUSB0", 115200, timeout=args.timeout)
    r = redis.StrictRedis("127.0.0.1",6379)

    while (True):

        #item = queue.get(block = True)
        item = json.loads(r.blpop("queue:write")[1])
        message = item["message"].encode('latin-1')
        timeout = float(item["timeout"])

#        PRUserial485_write([chr(i) for i in message], 1)
#        print([chr(i) for i in message])
 
        ser.reset_input_buffer()
        ser.reset_output_buffer()

        ser.write(message)
        res = ser.read(1)
        time.sleep(args.ser_buff_tout)
        if ser.in_waiting > 0:
            res += ser.read_all()

#        res = b'\x00\x11\x00\x02\x00' + (chr(message[4])).encode('latin-1') + (chr(237-message[4])).encode('latin-1')
        res = (res + terminator if res else zb + terminator).decode('latin-1')
#        print((ord(res[4])*256 + ord(res[5]))/100.0)

        r.rpush("queue:read",json.dumps({"message":res}))

# Procedimento principal

if (__name__ == "__main__"):

    # Imprime mensagem inicial
    logger.info("Ponte.py")
    logger.info(time_string() + "Servidor TCP/IP na porta " + str(SERVER_PORT) + " para ponte com interface serial PRUserial485 inicializado.")

    # Cria thread que irá processar a fila de requisições
    new_thread = threading.Thread(target = queue_processing_thread)
    new_thread.setDaemon(True)
    new_thread.start()

    while (True):
        time.sleep(10)

