#!/usr/bin/python3

import argparse
import socket
import sys
from _thread import *
import re

listening_port = 5001

parser = argparse.ArgumentParser()

parser.add_argument('--max_conn', help="Maximum allowed connections", default=5, type=int)
parser.add_argument('--buffer_size', help="Number of samples to be used", default=8192, type=int)

args = parser.parse_args()
max_connection = args.max_conn
buffer_size = args.buffer_size

def start():   
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('127.0.0.1', listening_port))
        sock.listen(max_connection)
        print("[*] Server started successfully [ %d ]" %(listening_port))
    except Exception as e:
        print("[*] Unable to Initialize Socket")
        print(e)
        sys.exit(2)

    while True:
        try:
            conn, addr = sock.accept() 
            data = conn.recv(buffer_size) 
            start_new_thread(conn_string, (conn,data, addr)) 
        except KeyboardInterrupt:
            sock.close()
            print("\n[*] Graceful Shutdown")
            sys.exit(1)

def conn_string(conn, data, addr):
    try:
        data_dec = str(data, 'iso-8859-1')
        method, target, ver = data_dec.split('\r\n')[0].split()
        rep = re.search("(?:http:\/\/)?(.+?)$", target).group(1)
        rep = rep[rep.find("/"):]

        data_dec = data_dec.replace(target, rep)
        data_enc = data_dec.encode('iso-8859-1')
        port_match = re.search(r":(\d{2,5})", target)
        if port_match:
            port = int(port_match.group(1))
            target = target.replace(port_match.group(0), "")
        else:
            port = 80

        target_match = re.search(r"(?:http:\/\/)?(.+?)(?:$|\/)", target)
        target = target_match.group(1)

        proxy_server(target, port, conn, data_enc, addr)
    except Exception as e:
        print(e)

def proxy_server(webserver, port, conn, data, addr):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((webserver, port))
        sock.send(data)

        while 1:
            reply = sock.recv(buffer_size)

            if(len(reply)>0):
                conn.send(reply)
                
                dar = float(len(reply))
                dar = float(dar/1024)
                dar = "%.3s" % (str(dar))
                dar = "%s KB" % (dar)
                print("[*] Request Done: %s => %s <=" % (str(addr[0]), str(dar)))
            else:
                break

        sock.close()
        conn.close()
    except socket.error as e:
        sock.close()
        conn.close()
        print(e)
        sys.exit(1)

if __name__== "__main__":
    start()