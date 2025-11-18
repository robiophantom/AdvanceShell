# nlp_engine.py
"""
NLP Engine for mysh
--------------------

This module provides all Natural Language Processing functionality for
the shell. It converts natural language instructions into executable
shell commands using Groq LLM (llama-3.3-70b-versatile).

This is a standalone engine that your main.py can import:

    from nlp_engine import (
        is_natural_language,
        interpret_nl,
        fuzzy_fix,
        is_dangerous
    )

Then in main.py, BEFORE running builtins/external commands:

    if is_natural_language(text):
        result = interpret_nl(text)
        ...
"""

import os
import json
import shlex
import difflib
import shutil

from typing import Optional, Tuple, List, Dict, Any
from groq import Groq


# --------------------------------------------
# 1. CONFIGURATION
# --------------------------------------------

GROQ_API_KEY = "enter your api key"
MODEL_NAME = "llama-3.3-70b-versatile"

AUTO_EXECUTE_CONFIDENCE = 85

DANGEROUS = [
    "rm -rf", "mkfs", "dd if", "shutdown", "reboot", ":(){",
    "chmod 777 -R", "killall", "pkill", "systemctl stop"
]


# --------------------------------------------
# 2. NLP DETECTION
# --------------------------------------------

BUILTINS = {
    "cd", "help", "exit", "pwd", "echo", "clear",
    "mkdir", "rmdir", "touch", "rm", "cat", "ls",
    "ping", "dnslookup", "publicip", "hostinfo",
    "ifconfig", "ipaddr", "scan", "whois",
    "traceroute", "netstat", "history"
}

def is_natural_language(text: str) -> bool:
    """
    Determine whether input is likely natural language
    rather than a command.
    """
    if " " not in text:
        return False

    first = text.split()[0]

    if first in BUILTINS:
        return False
    if shutil.which(first):  # real executable
        return False
    if os.path.exists(first):
        return False

    return True


# --------------------------------------------
# 3. FUZZY FILE NAME MATCHING
# --------------------------------------------

def fuzzy_find_filename(token: str) -> Optional[str]:
    try:
        items = os.listdir(".")
    except:
        return None

    if token in items:
        return token

    bare = token.rstrip("/")
    matches = difflib.get_close_matches(bare, items, n=1, cutoff=0.6)
    if matches:
        m = matches[0]
        return m + "/" if os.path.isdir(m) else m
    return None


def fuzzy_fix(cmd: str) -> Tuple[str, List[str]]:
    """
    Fix filenames using fuzzy matching.
    Returns (corrected_command, list_of_replacements)
    """
    replacements = []
    parts = [p.strip() for p in cmd.split(";") if p.strip()]
    out_parts = []

    for part in parts:
        try:
            toks = shlex.split(part)
        except:
            out_parts.append(part)
            continue

        new_tokens = []
        for t in toks:
            if os.path.exists(t):
                new_tokens.append(t)
                continue

            guess = fuzzy_find_filename(t)
            if guess:
                replacements.append(f"{t} → {guess}")
                new_tokens.append(guess)
            else:
                new_tokens.append(t)

        try:
            rebuilt = shlex.join(new_tokens)
        except:
            rebuilt = " ".join(new_tokens)

        out_parts.append(rebuilt)

    return "; ".join(out_parts), replacements


# --------------------------------------------
# 4. SAFETY CHECK
# --------------------------------------------

def is_dangerous(cmd: str) -> bool:
    c = cmd.lower()
    return any(d in c for d in DANGEROUS)


# --------------------------------------------
# 5. NLP → SHELL COMMAND USING LLM
# --------------------------------------------

def interpret_nl(text: str) -> Optional[Dict[str, Any]]:
    """
    Sends the instruction to Groq LLM and receives:
    { "command": "...", "explanation": "...", "confidence": 87 }
    """
    client = Groq(api_key=GROQ_API_KEY)

    prompt = f"""
Convert the natural-language instruction into a shell command.
Return STRICT JSON only:
{{
 "command": "...",
 "explanation": "...",
 "confidence": 92
}}

Avoid dangerous commands.

Instruction: {text}
"""

    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        # Correct attribute access
        content = resp.choices[0].message.content.strip()

        # Extract JSON only
        if not content.startswith("{"):
            content = content[content.find("{"):content.rfind("}") + 1]

        data = json.loads(content)
        data["confidence"] = int(data.get("confidence", 0))
        return data

    except Exception as e:
        print("AI error:", e)
        return None
