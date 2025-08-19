import os
import ctypes
import subprocess
def spellcheck(word):
    result = subprocess.run(
        ["wsl", "voikkospell", "-s", "-d", "fi"],
        input=word.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    print(result.stdout.decode("utf-8"))
    if result.stderr:
        print("ERROR:", result.stderr.decode("utf-8"))


spellcheck("tietokonessa")
