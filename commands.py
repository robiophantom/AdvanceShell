import os
import subprocess
import shutil
import socket
import urllib.request

MAX_SCAN_PORTS = 65535

BUILTINS = {
    "cd", "help", "exit", "pwd", "echo", "clear",
    "mkdir", "rmdir", "touch", "rm", "cat", "ls",
    "ping", "dnslookup", "publicip", "hostinfo",
    "ifconfig", "ipaddr", "scan", "whois",
    "traceroute", "netstat", "history"
}


def run_builtin(args, hist_list, memory_history):
    cmd = args[0]

    # ------- BASIC BUILTINS -------
    if cmd == "exit":
        raise EOFError()

    if cmd == "help":
        print("Builtins:")
        print(" cd help exit pwd echo clear mkdir rmdir touch rm cat ls")
        print(" network: ping traceroute dnslookup publicip hostinfo ifconfig ipaddr")
        print(" extra: scan whois netstat")
        print(" history (! !) !N !prefix")
        return

    if cmd == "cd":
        path = args[1] if len(args) > 1 else os.path.expanduser("~")
        try:
            os.chdir(os.path.expanduser(path))
        except Exception as e:
            print("cd:", e)
        return

    if cmd == "pwd":
        print(os.getcwd())
        return

    if cmd == "echo":
        print(" ".join(args[1:]))
        return

    if cmd == "clear":
        os.system("clear")
        return

    if cmd == "mkdir":
        try:
            os.mkdir(args[1])
        except Exception as e:
            print("mkdir:", e)
        return

    if cmd == "rmdir":
        try:
            os.rmdir(args[1])
        except Exception as e:
            print("rmdir:", e)
        return

    if cmd == "touch":
        try:
            open(args[1], "a").close()
        except Exception as e:
            print("touch:", e)
        return

    if cmd == "rm":
        try:
            os.remove(args[1])
        except Exception as e:
            print("rm:", e)
        return

    if cmd == "cat":
        try:
            with open(args[1], "r") as f:
                print(f.read(), end="")
        except Exception as e:
            print("cat:", e)
        return

    if cmd == "ls":
        try:
            items = [i for i in sorted(os.listdir(".")) if not i.startswith(".")]
            print("  ".join(items))
        except Exception as e:
            print("ls:", e)
        return

    # ----------- HISTORY BUILTIN -----------

    if cmd == "history":
        # history -c
        if len(args) >= 2 and args[1] == "-c":
            from history import clear_history
            clear_history(hist_list, memory_history)
            print("History cleared.")
            return "HISTORY_CLEARED"

        # print history
        for idx, line in enumerate(hist_list, start=1):
            print(f"{idx}  {line}")
        return

    # ----------- NETWORK BUILTINS -----------

    if cmd == "ping":
        if len(args) < 2:
            print("usage: ping <host>")
        else:
            subprocess.run(["ping", "-c", "4", args[1]])
        return

    if cmd == "traceroute":
        if len(args) < 2:
            print("usage: traceroute <host>")
        else:
            if shutil.which("traceroute"):
                subprocess.run(["traceroute", args[1]])
            elif shutil.which("tracepath"):
                subprocess.run(["tracepath", args[1]])
            else:
                print("traceroute not installed")
        return

    if cmd == "netstat":
        if shutil.which("ss"):
            subprocess.run(["ss", "-tunap"])
        elif shutil.which("netstat"):
            subprocess.run(["netstat", "-tulpn"])
        else:
            print("No netstat or ss available.")
        return

    if cmd == "dnslookup":
        try:
            ip = socket.gethostbyname(args[1])
            print(args[1], "->", ip)
        except Exception as e:
            print("dnslookup:", e)
        return

    if cmd == "publicip":
        try:
            ip = urllib.request.urlopen("https://api.ipify.org").read().decode()
            print("Public IP:", ip)
        except Exception as e:
            print("publicip:", e)
        return

    if cmd == "hostinfo":
        try:
            host = socket.gethostname()
            ip = socket.gethostbyname(host)
            print("Hostname:", host)
            print("Local IP:", ip)
        except Exception as e:
            print("hostinfo:", e)
        return

    if cmd in ("ifconfig", "ipaddr"):
        if shutil.which("ip"):
            subprocess.run(["ip", "addr"])
        else:
            subprocess.run(["ifconfig"])
        return

    if cmd == "scan":
        if len(args) != 4:
            print("usage: scan <host> <start> <end>")
            return
        host = args[1]
        start = int(args[2])
        end = int(args[3])
        for port in range(start, end + 1):
            s = socket.socket()
            s.settimeout(0.2)
            try:
                s.connect((host, port))
                print(f"OPEN: {port}")
            except:
                pass
            finally:
                s.close()
        return

    if cmd == "whois":
        subprocess.run(["whois", args[1]])
        return
