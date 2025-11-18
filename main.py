#!/usr/bin/env python3

import os
import shlex
import subprocess

from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.history import InMemoryHistory

# Existing imports
from history import (
    ensure_history_file,
    load_history_list,
    append_history_line,
    clear_history,
    expand_bang_command,
)
from commands import run_builtin, BUILTINS
from autocomplete import NoMenuCompleter, FishAutoSuggest

# NEW NLP IMPORTS
from nlp_engine import (
    is_natural_language,
    interpret_nl,
    fuzzy_fix,
    is_dangerous,
)


def run_external(args):
    try:
        subprocess.run(args)
    except FileNotFoundError:
        print(f"{args[0]}: command not found")
    except Exception as e:
        print("error:", e)


def main():
    ensure_history_file()
    hist_list = load_history_list()

    memory_history = InMemoryHistory()
    for h in hist_list:
        memory_history.append_string(h)

    session = PromptSession(
        history=memory_history,
        completer=NoMenuCompleter(),
        auto_suggest=FishAutoSuggest(),
    )

    kb = KeyBindings()

    @kb.add("tab")
    def _(event):
        buff = event.app.current_buffer
        suggestion = buff.suggestion
        if suggestion:
            buff.insert_text(suggestion.text)

    print("mysh — NLP Enabled Shell using Groq AI")

    while True:
        try:
            prompt = f"mysh:{os.getcwd()}$ "
            text = session.prompt(prompt, key_bindings=kb)
        except EOFError:
            print()
            break
        except KeyboardInterrupt:
            print()
            continue

        if not text.strip():
            continue

        # ----------------------------
        #    HISTORY EXPANSION
        # ----------------------------
        if text.startswith("!"):
            expanded, err = expand_bang_command(text.strip(), hist_list)
            if err:
                print(err)
                continue
            if expanded != text:
                print(expanded)
            text = expanded

        # ----------------------------
        #    NLP DETECTION
        # ----------------------------
        if is_natural_language(text):
            result = interpret_nl(text)

            if not result:
                continue

            cmd = result["command"].strip()
            expl = result["explanation"]
            conf = result["confidence"]

            # Apply fuzzy filename correction
            cmd2, rep = fuzzy_fix(cmd)
            if rep:
                print("Fuzzy fix:", ", ".join(rep))

            if is_dangerous(cmd2):
                print("⚠️ Dangerous command blocked.")
                continue

            print(f"Interpreted as: {cmd2}")
            print(f"Explanation : {expl}")
            print(f"Confidence  : {conf}%")

            # Auto-execute if high confidence
            if conf >= 85:
                print("Auto-executing...")
                for part in cmd2.split(";"):
                    part = part.strip()
                    if not part:
                        continue
                    try:
                        args = shlex.split(part)
                        if args[0] in BUILTINS:
                            run_builtin(args, hist_list, memory_history)
                        else:
                            run_external(args)
                    except Exception as e:
                        print("execution error:", e)
                continue

            # Ask user for execution
            ask = input("Run this? [y/N]: ").lower().strip()
            if ask == "y":
                for part in cmd2.split(";"):
                    part = part.strip()
                    if not part:
                        continue
                    try:
                        args = shlex.split(part)
                        if args[0] in BUILTINS:
                            run_builtin(args, hist_list, memory_history)
                        else:
                            run_external(args)
                    except Exception as e:
                        print("execution error:", e)
            continue

        # ----------------------------
        #     NORMAL SHELL MODE
        # ----------------------------

        try:
            args = shlex.split(text)
        except Exception as e:
            print("syntax error:", e)
            continue

        if not args:
            continue

        # Save command to history BEFORE running
        append_history_line(hist_list, text, memory_history)

        # Run builtins
        if args[0] in BUILTINS:
            res = run_builtin(args, hist_list, memory_history)
            if res == "HISTORY_CLEARED":
                memory_history = InMemoryHistory()
                session = PromptSession(
                    history=memory_history,
                    completer=NoMenuCompleter(),
                    auto_suggest=FishAutoSuggest(),
                )
            continue

        # Run external commands
        run_external(args)


if __name__ == "__main__":
    main()
