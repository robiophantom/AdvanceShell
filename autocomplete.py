import os
from prompt_toolkit.auto_suggest import AutoSuggest, Suggestion
from prompt_toolkit.completion import Completer

from commands import BUILTINS


def list_path_executables():
    out = []
    seen = set()
    for p in os.environ.get("PATH", "").split(os.pathsep):
        if not p:
            continue
        try:
            for name in os.listdir(p):
                full = os.path.join(p, name)
                if name in seen:
                    continue
                if os.path.isfile(full) and os.access(full, os.X_OK):
                    seen.add(name)
                    out.append(name)
        except:
            pass
    return sorted(out)


def list_fs_matches(prefix):
    try:
        names = os.listdir(".")
    except:
        return []
    out = []
    for n in names:
        if n.startswith(prefix):
            out.append(n + "/" if os.path.isdir(n) else n)
    return sorted(out)


class FishAutoSuggest(AutoSuggest):
    def __init__(self):
        self.cached = list_path_executables()

    def refresh(self):
        self.cached = list_path_executables()

    def get_suggestion(self, buffer, document):
        text = document.text_before_cursor
        if not text:
            return None

        parts = text.split()
        last_space = text.rfind(" ")

        if last_space == -1:
            token = text
            token_pos = 0
        else:
            token = text[last_space + 1:]
            token_pos = last_space + 1

        if token_pos == 0:  # suggest commands
            for b in sorted(BUILTINS):
                if b.startswith(token) and b != token:
                    return Suggestion(b[len(token):])

            self.refresh()
            for c in self.cached:
                if c.startswith(token) and c != token:
                    return Suggestion(c[len(token):])
            return None

        # cd: suggest dirs only
        if parts[0] == "cd":
            for x in list_fs_matches(token):
                if x[-1] == "/" and x != token:
                    return Suggestion(x[len(token):])
            return None

        # general file suggestions
        for x in list_fs_matches(token):
            if x != token:
                return Suggestion(x[len(token):])
        return None


class NoMenuCompleter(Completer):
    def get_completions(self, document, complete_event):
        return []
