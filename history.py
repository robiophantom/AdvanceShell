import os
import re

HISTORY_FILE = os.path.expanduser("~/.myshell_history")


def ensure_history_file():
    d = os.path.dirname(HISTORY_FILE)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)
    if not os.path.exists(HISTORY_FILE):
        open(HISTORY_FILE, "a").close()


def load_history_list():
    ensure_history_file()
    with open(HISTORY_FILE, "r", encoding="utf-8", errors="ignore") as f:
        return [l.rstrip("\n") for l in f.readlines() if l.strip()]


def append_history_line(hist_list, line, memory_history):
    if not line.strip():
        return
    if hist_list and hist_list[-1] == line:
        return  # avoid consecutive duplicates

    with open(HISTORY_FILE, "a", encoding="utf-8", errors="ignore") as f:
        f.write(line + "\n")

    hist_list.append(line)
    memory_history.append_string(line)


def clear_history(hist_list, memory_history):
    hist_list.clear()
    open(HISTORY_FILE, "w").close()
    return "CLEARED"


# --------------------------
# History Expansion
# --------------------------

def expand_bang_command(text, hist_list):
    if text == "!!":
        if not hist_list:
            return None, "No history."
        return hist_list[-1], None

    # !N
    m = re.match(r"^!(\d+)$", text)
    if m:
        n = int(m.group(1))
        if n < 1 or n > len(hist_list):
            return None, f"No such event: {text}"
        return hist_list[n - 1], None

    # !prefix
    m2 = re.match(r"^!(.+)$", text)
    if m2:
        prefix = m2.group(1)
        for cmd in reversed(hist_list):
            if cmd.startswith(prefix):
                return cmd, None
        return None, f"No such event starting with {prefix}"

    return text, None
