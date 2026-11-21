#!/usr/bin/env python3
"""
NullQuest - a terminal hacking puzzle game (stdlib only).

7 story levels, each teaches one real skill: base64, Caesar cipher, log analysis,
hash cracking, port scanning, SQL injection and layered encodings.
EVERYTHING is simulated inside the game. Nothing touches your network or files.

Run:  python nullquest.py
"""
import argparse, base64, binascii, codecs, hashlib, json, os, random, re, shlex, sqlite3, sys, textwrap, time

LB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leaderboard.json")
USE_COLOR = sys.stdout.isatty()
FAST = False
G, R, Y, C, D, B, X = "\033[32m", "\033[31m", "\033[33m", "\033[36m", "\033[2m", "\033[1m", "\033[0m"

ADJ = ["silent", "crimson", "hidden", "rapid", "neon", "cosmic", "rusty", "golden", "frozen", "wild"]
NOUN = ["falcon", "cipher", "ghost", "vault", "comet", "tiger", "anchor", "matrix", "raven", "engine"]
PASSWORDS = ["123456", "password", "qwerty", "letmein", "dragon", "monkey", "football", "iloveyou",
             "admin123", "welcome", "sunshine", "princess", "trustno1", "baseball", "master", "shadow",
             "superman", "michael", "freedom", "whatever", "starwars", "hello123", "passw0rd", "batman",
             "cheese", "summer2024", "winter", "flower", "cookie", "hunter2"]
MAX_PER_LEVEL = 100


def col(text, c):
    return f"{c}{text}{X}" if USE_COLOR else text


def say(text, delay=0.006):
    """Typewriter effect for story text (off with --fast or when piped)."""
    if FAST or not sys.stdout.isatty():
        print(text)
        return
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def make_flag(rng):
    return f"FLAG{{{rng.choice(ADJ)}_{rng.choice(NOUN)}_{rng.randint(10, 99)}}}"


def caesar(text, shift):
    out = []
    for ch in text:
        if ch.isalpha():
            base = 65 if ch.isupper() else 97
            out.append(chr((ord(ch) - base + shift) % 26 + base))
        else:
            out.append(ch)
    return "".join(out)


class Level:
    def __init__(self, title, story, files, solution, hints, check=None, ctx=None):
        self.title, self.story, self.files, self.hints = title, story, files, hints
        self.solution = solution                       # used by the tests only
        self.check = check or (lambda a: a.strip() == solution)
        self.ctx = ctx or {}
        self.stats = None


# ------------------------------------------------------------------ levels
def level1(rng):
    flag = make_flag(rng)
    msg = f"Agent, the vault key is {flag}. Burn after reading."
    enc = base64.b64encode(msg.encode()).decode()
    return Level("Warm-up: Intercepted Message",
                 "A rebel server leaked a strange message. It looks like random letters, but it ends in '='.\n"
                 "That is a classic sign of BASE64 encoding.\n"
                 "OBJECTIVE: decode note.txt and submit the flag.   (try: cat note.txt, decode base64 <text>)",
                 {"note.txt": f"Intercepted transmission:\n\n{enc}\n"}, flag,
                 ["Base64 strings often end with '=' or '=='.",
                  "Use: decode base64 <the long string>",
                  "Then: submit FLAG{...} using the flag you find in the decoded text."])


def level2(rng):
    flag, shift = make_flag(rng), rng.randint(3, 23)
    cipher = caesar(f"The vault code is {flag}", shift)
    return Level("Caesar's Ghost",
                 "Julius Caesar hid secrets by shifting every letter a fixed number of places.\n"
                 "Someone used that trick on the next message. There are only 25 possible shifts...\n"
                 "OBJECTIVE: break the cipher in cipher.txt.   (try: caesar all <text>)",
                 {"cipher.txt": cipher + "\n"}, flag,
                 ["Only letters are shifted. Digits and symbols stay the same.",
                  "Use: caesar all <text>  and look for the line that reads like English.",
                  "Or guess a shift: caesar 7 <text>"], ctx={"shift": shift})


def level3(rng):
    flag = make_flag(rng)
    ips = [f"{rng.randint(11, 198)}.{rng.randint(0, 255)}.{rng.randint(0, 255)}.{rng.randint(1, 254)}" for _ in range(25)]
    paths = ["/index.html", "/about", "/products", "/contact", "/login", "/static/app.js", "/static/style.css", "/blog/1", "/blog/2"]
    lines = []
    for i in range(260):
        lines.append(f'{rng.choice(ips)} - - [18/Nov/2026:{10 + i // 60:02d}:{i % 60:02d}:{rng.randint(0, 59):02d} +0000] '
                     f'"GET {rng.choice(paths)} HTTP/1.1" {rng.choice([200] * 8 + [304, 404])} {rng.randint(200, 9000)}')
    for _ in range(14):
        lines.insert(rng.randint(0, len(lines)),
                     f'{rng.choice(ips)} - - [18/Nov/2026:12:{rng.randint(0, 59):02d}:{rng.randint(0, 59):02d} +0000] "GET /admin HTTP/1.1" 403 199')
    lines.insert(rng.randint(150, len(lines)),
                 f'203.0.113.66 - - [18/Nov/2026:13:37:00 +0000] "GET /admin/panel?key={flag} HTTP/1.1" 200 5120')
    return Level("Needle in the Logs",
                 "The web server was breached. Hundreds of log lines, and only ONE shows an attacker\n"
                 "who got INTO the admin area (HTTP status 200) instead of being blocked (403).\n"
                 "OBJECTIVE: find that request in access.log and submit the secret key from its URL.\n"
                 "(try: grep admin access.log   or a regex like: grep \"admin.* 200\" access.log)",
                 {"access.log": "\n".join(lines) + "\n"}, flag,
                 ["grep prints only the lines that match a pattern.",
                  "Status 403 = blocked, 200 = success. Search for admin lines first.",
                  "Try: grep \"admin.* 200\" access.log"])


def level4(rng):
    pw = rng.choice(PASSWORDS)
    words = PASSWORDS[:]
    rng.shuffle(words)
    return Level("Crack the Hash",
                 "Servers store password HASHES, not passwords. A hash can't be reversed, but you can guess\n"
                 "words, hash each one and compare. That's a dictionary attack.\n"
                 "OBJECTIVE: crack the admin hash in shadow.txt using wordlist.txt.\n"
                 "Submit the flag as FLAG{password}.   (try: crack <hash> wordlist.txt)",
                 {"shadow.txt": f"admin:{hashlib.md5(pw.encode()).hexdigest()}\n",
                  "wordlist.txt": "\n".join(words) + "\n"}, f"FLAG{{{pw}}}",
                 ["The hash is the long hex string after 'admin:'.",
                  "Use: crack <hash> wordlist.txt",
                  "Wrap the cracked password like this: submit FLAG{password}"])


def level5(rng):
    tport = rng.choice([23, 2323, 8023])
    pool = [(22, "ssh", "OpenSSH 8.9"), (80, "http", "nginx 1.18"), (443, "https", "nginx 1.18"),
            (3306, "mysql", "MySQL 5.7"), (8080, "http-proxy", "Squid 4.13")]
    ports = sorted(rng.sample(pool, 3) + [(tport, "telnet", "Linux telnetd")])
    out = ["Starting scan of 10.10.10.5 ...", "", "PORT      STATE  SERVICE     VERSION"]
    out += [f"{str(p) + '/tcp':<9} open   {s:<11} {v}" for p, s, v in ports]
    out += ["", "Scan done: 1 host up"]
    return Level("Scan the Target",
                 "Before attacking, hackers map what is running. That's port scanning.\n"
                 "Target: 10.10.10.5.  One service lets people log in remotely WITHOUT encryption (everything,\n"
                 "even passwords, travels in plain text).\n"
                 "OBJECTIVE: scan the target and submit the PORT NUMBER of that unencrypted remote-login service.\n"
                 "(try: nmap 10.10.10.5)",
                 {"README.txt": "Target machine: 10.10.10.5\nTask: find the plain-text remote login service.\n"},
                 str(tport),
                 ["Services: ssh = encrypted login, telnet = plain-text login.",
                  "Run: nmap 10.10.10.5 and find the line that says telnet.",
                  "Submit just the number, like: submit 23 (its port may not be the default!)"],
                 check=lambda a: a.strip().replace("FLAG{", "").replace("}", "") == str(tport),
                 ctx={"nmap": "\n".join(out), "target": "10.10.10.5"})


def level6(rng):
    flag = make_flag(rng)
    src = ("<?php\n// login.php\n$user = $_POST['username'];\n$pass = $_POST['password'];\n"
           "$q = \"SELECT * FROM users WHERE username='$user' AND password='$pass'\";\n"
           "$result = mysql_query($q);\nif (mysql_num_rows($result) > 0) { login(); }\n")
    return Level("The Broken Login",
                 "The company's login page builds its database query by gluing your input into a string.\n"
                 "If you type SQL instead of a name, the database may run it. That's SQL INJECTION.\n"
                 "OBJECTIVE: log in as admin WITHOUT knowing the password, then submit the flag.\n"
                 "(try: cat login.php.txt   then   login)",
                 {"login.php.txt": src}, flag,
                 ["Look at the query in login.php.txt. Your text goes between the quote marks.",
                  "A quote ' closes the string early. -- starts a comment that ignores the rest.",
                  "Try the username: admin'--   (any password)  or  ' OR 1=1--"],
                 ctx={"login": True, "flag": flag, "admin_pw": f"{rng.getrandbits(48):012x}"})


def level7(rng):
    flag = make_flag(rng)
    layered = binascii.hexlify(base64.b64encode(codecs.encode(flag, "rot13").encode())).decode()
    return Level("Final Boss: Layers",
                 "The last vault is wrapped in several layers of encoding. Peel them one by one:\n"
                 "the output of one decode is the input of the next.\n"
                 "OBJECTIVE: reveal the flag hidden in payload.txt.   (try: decode hex ... decode base64 ... decode rot13 ...)",
                 {"payload.txt": layered + "\n"}, flag,
                 ["The text is made only of 0-9 and a-f: that is HEX.",
                  "hex -> (gives a base64 string) -> base64 -> (gives odd letters) -> ROT13.",
                  "Decode in this order: hex, then base64, then rot13."])


BUILDERS = [level1, level2, level3, level4, level5, level6, level7]


# ------------------------------------------------------------------ helpers
def text_arg(lvl, args):
    if len(args) == 1 and args[0] in lvl.files:
        return lvl.files[args[0]].strip()
    return " ".join(args)


def do_decode(kind, text):
    try:
        if kind == "base64":
            t = re.sub(r"\s+", "", text)
            return base64.b64decode(t + "=" * (-len(t) % 4)).decode("utf-8", errors="replace")
        if kind == "hex":
            return bytes.fromhex(re.sub(r"\s+", "", text)).decode("utf-8", errors="replace")
        if kind == "rot13":
            return codecs.encode(text, "rot13")
        if kind == "binary":
            bits = re.sub(r"[^01]", "", text)
            return "".join(chr(int(bits[i:i + 8], 2)) for i in range(0, len(bits) - 7, 8))
    except (binascii.Error, ValueError) as e:
        return f"decode error: {e}"
    return "unknown type. use: base64 | hex | rot13 | binary"


def cmd_grep(lvl, args):
    flags = re.I if "-i" in args else 0
    args = [a for a in args if a != "-i"]
    if len(args) != 2 or args[1] not in lvl.files:
        return print("usage: grep [-i] <pattern> <file>")
    try:
        rx = re.compile(args[0], flags)
    except re.error:
        rx = re.compile(re.escape(args[0]), flags)
    hits = [l for l in lvl.files[args[1]].splitlines() if rx.search(l)]
    for l in hits[:40]:
        print(l)
    print(col(f"-- {len(hits)} matching line(s)" + (" (showing 40)" if len(hits) > 40 else ""), D))


def cmd_crack(lvl, args):
    if len(args) != 2 or args[1] not in lvl.files:
        return print("usage: crack <hash> <wordlist-file>")
    target, algos = args[0].lower(), {32: "md5", 40: "sha1", 64: "sha256"}
    algo = algos.get(len(target))
    if not algo:
        return print("unknown hash length (md5/sha1/sha256 supported)")
    words = lvl.files[args[1]].split()
    print(f"[*] {algo} dictionary attack with {len(words)} words ...")
    for w in words:
        if hashlib.new(algo, w.encode()).hexdigest() == target:
            return print(col(f"[+] CRACKED: {w}", G))
    print(col("[-] not found in this wordlist", R))


def run_login(lvl):
    """A REAL (throwaway, in-memory) vulnerable query, so real injections work."""
    user, pw = input("username: "), input("password: ")
    query = f"SELECT * FROM users WHERE username='{user}' AND password='{pw}'"
    print(col("query> " + query, D))
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE users(username TEXT, password TEXT, secret TEXT)")
    con.execute("INSERT INTO users VALUES('admin', ?, ?)", (lvl.ctx["admin_pw"], lvl.ctx["flag"]))
    con.execute("INSERT INTO users VALUES('guest', 'guest123', 'nothing here')")
    allowed = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION}
    con.set_authorizer(lambda action, *a: sqlite3.SQLITE_OK if action in allowed else sqlite3.SQLITE_DENY)
    deadline = time.time() + 1.5
    con.set_progress_handler(lambda: 1 if time.time() > deadline else 0, 1000)
    try:
        rows = con.execute(query).fetchall()
    except sqlite3.Error as e:
        return print(col(f"SQL error: {e}", R))
    finally:
        con.close()
    if not rows:
        print(col("Login failed.", R))
    elif rows[0][0] == "admin":
        print(col(f"Welcome, admin!  Secret: {rows[0][2]}", G))
    else:
        print(col(f"Logged in as {rows[0][0]} (no admin rights). Get in as admin!", Y))


HELP = """commands:
  ls | cat <file> | grep [-i] <pattern> <file>
  decode <base64|hex|rot13|binary> <text or file>
  caesar <shift|all> <text or file>      hash <md5|sha1|sha256> <text>
  crack <hash> <wordlist>                nmap <target>        login (when available)
  hint (-25 pts)   submit <answer>   skip (0 pts)   score   quit

how to submit: find the flag, then type   submit FLAG{word_word_42}
(use your own flag. Level 5 wants just a port number, e.g.  submit 2323)"""


def play_level(n, lvl, total_so_far):
    print()
    print(col(f"=== LEVEL {n}/{len(BUILDERS)}: {lvl.title} ===", C + B))
    say(lvl.story)
    print(col("type 'help' for commands", D))
    t0, hints, wrong = time.time(), 0, 0
    while True:
        try:
            line = input(col(f"[agent@L{n}]$ ", G)).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return "quit"
        if not line:
            continue
        try:
            parts = shlex.split(line)
        except ValueError as e:
            print(f"parse error: {e} (check your quotes)")
            continue
        cmd, args = parts[0].lower(), parts[1:]
        if cmd == "help":
            print(HELP)
        elif cmd == "ls":
            print("  ".join(lvl.files))
        elif cmd == "cat":
            print(lvl.files[args[0]].rstrip("\n") if args and args[0] in lvl.files else "cat: no such file")
        elif cmd == "grep":
            cmd_grep(lvl, args)
        elif cmd == "decode" and len(args) >= 2:
            print(do_decode(args[0].lower(), text_arg(lvl, args[1:])))
        elif cmd == "caesar" and len(args) >= 2:
            t = text_arg(lvl, args[1:])
            if args[0].lower() == "all":
                for s in range(1, 26):
                    print(f"shift {s:>2}: {caesar(t, -s)}")
            elif args[0].lstrip("-").isdigit():
                print(caesar(t, -int(args[0])))
            else:
                print("usage: caesar <shift|all> <text>")
        elif cmd == "hash" and len(args) >= 2 and args[0].lower() in ("md5", "sha1", "sha256"):
            print(hashlib.new(args[0].lower(), " ".join(args[1:]).encode()).hexdigest())
        elif cmd == "crack":
            cmd_crack(lvl, args)
        elif cmd == "nmap":
            if "nmap" not in lvl.ctx:
                print("nmap: no target to scan in this level")
            elif args and args[-1] == lvl.ctx["target"]:
                print(lvl.ctx["nmap"])
            else:
                print("Note: host seems down or wrong target. Check README.txt")
        elif cmd == "login" and lvl.ctx.get("login"):
            run_login(lvl)
        elif cmd == "hint":
            if hints >= len(lvl.hints):
                print("no more hints")
            else:
                print(col(f"HINT {hints + 1}: {lvl.hints[hints]}", Y))
                hints += 1
        elif cmd == "score":
            print(f"score so far: {total_so_far}")
        elif cmd == "skip":
            print(col("Level skipped (0 points).", Y))
            lvl.stats = dict(points=0, secs=int(time.time() - t0), hints=hints, wrong=wrong, skipped=True)
            return 0
        elif cmd in ("quit", "exit"):
            return "quit"
        elif cmd == "submit":
            if lvl.check(" ".join(args)):
                secs = int(time.time() - t0)
                pts = max(20, MAX_PER_LEVEL - hints * 25 - wrong * 5 - max(0, secs - 90) // 5)
                print(col(f"ACCESS GRANTED!  +{pts} points  ({secs}s, {hints} hint(s), {wrong} wrong)", G + B))
                lvl.stats = dict(points=pts, secs=secs, hints=hints, wrong=wrong, skipped=False)
                return pts
            wrong += 1
            print(col("Wrong answer. (-5 points)  Format: submit FLAG{...}  (copy it exactly)", R))
        else:
            print(f"{cmd}: command not found (type 'help')")


# ------------------------------------------------------------------ debrief
def short(text, n=46):
    text = text.replace("\n", " ")
    return text if len(text) <= n else text[:n] + "..."


def debrief(i, lvl):
    """(concept, steps, defense) for level i, built from THIS run's puzzle data."""
    f = lvl.files
    if i == 1:
        enc = f["note.txt"].split("\n")[2]
        return ("Base64 turns bytes into plain text so they travel safely in emails and JSON. "
                "It is ENCODING, not encryption: anyone can reverse it.",
                [f"Read the file: cat note.txt  ->  {short(enc)}",
                 "Recognise Base64: letters, digits, + and /, often ending with '=' padding.",
                 f"Decode it: decode base64 <string>  ->  \"{do_decode('base64', enc)}\"",
                 f"Submit the flag you found: submit {lvl.solution}"],
                "Never 'hide' secrets with Base64. Use real encryption and keep secrets out of plain files and repos.")
    if i == 2:
        cipher, shift = f["cipher.txt"].strip(), lvl.ctx["shift"]
        return ("The Caesar cipher shifts every letter by a fixed amount. There are only 25 keys, "
                "so attackers simply try them all (brute force).",
                [f"Read the ciphertext: {short(cipher)}",
                 "Try every shift at once: caesar all cipher.txt  (25 lines of output).",
                 f"Find the line that reads like English: shift {shift}  ->  \"{caesar(cipher, -shift)}\"",
                 f"Submit the flag: submit {lvl.solution}"],
                "A tiny key space is breakable instantly. Modern ciphers such as AES-256 have 2^256 possible keys.")
    if i == 3:
        lines = f["access.log"].splitlines()
        hit = next(l for l in lines if " 200 " in l and "/admin" in l)
        n_admin = sum("admin" in l for l in lines)
        return ("Log analysis: servers record every request. Searching logs with grep and regex is how "
                "defenders find attackers after (or during) a breach.",
                [f"Too many lines to read ({len(lines)}). Filter: grep admin access.log  ->  {n_admin} lines, mostly 403 (blocked).",
                 "Spot the odd one: status 200 means the request SUCCEEDED, while the rest were blocked.",
                 "Narrow it with a regex: grep \"admin.* 200\" access.log",
                 f"The attacker's request: {short(hit, 70)}",
                 f"The secret key is in the URL. Submit it: submit {lvl.solution}"],
                "Never put secrets in URLs (they land in logs, history and proxies). Alert on admin access, "
                "rate-limit probes, and ship logs to a SIEM.")
    if i == 4:
        pw = lvl.solution[5:-1]
        h = f["shadow.txt"].split(":")[1].strip()
        return ("Servers store password HASHES. A hash can't be reversed, but weak passwords fall to a "
                "dictionary attack: hash each guess and compare.",
                [f"Read the hash file: cat shadow.txt  ->  admin:{short(h, 20)}",
                 f"Identify the hash type by length: {len(h)} hex characters = MD5.",
                 f"Run the attack: crack {short(h, 12)} wordlist.txt  ->  CRACKED: {pw}",
                 f"Wrap the password in the flag format: submit {lvl.solution}"],
                "Use slow, salted password hashes (bcrypt, scrypt, Argon2), never MD5/SHA1, and block "
                "common passwords at signup.")
    if i == 5:
        port = lvl.solution
        return ("Port scanning (nmap) maps which services a machine exposes. Attackers start here; defenders "
                "run it on themselves to find forgotten services.",
                ["Scan the target: nmap 10.10.10.5  ->  a table of open ports and services.",
                 "Read the SERVICE column, not just the numbers: ssh is encrypted, telnet is plain text.",
                 f"Telnet was on port {port} here. Services can run on non-default ports, so always read the service name.",
                 f"Submit the port number: submit {port}"],
                "Disable telnet, use SSH with keys, close every unneeded port, and put a firewall in front.")
    if i == 6:
        return ("SQL injection happens when user input is glued into a SQL query, so attackers can change the "
                "query's meaning. It has caused some of the biggest data breaches ever.",
                ["Read the vulnerable code: cat login.php.txt  ->  the query is built with string concatenation.",
                 "Your input lands between quote marks, so a quote ' closes the string early.",
                 "Payload at the username prompt: admin'--   (the -- comments out the password check)",
                 "or: admin' OR '1'='1   (adds a condition that is always true)",
                 "Resulting query: SELECT * FROM users WHERE username='admin'--' AND password='x'",
                 f"The database returns the admin row and prints the secret. Submit it: submit {lvl.solution}"],
                "Use parameterized queries (prepared statements), never string concatenation. Add least-privilege "
                "database accounts and input validation as extra layers.")
    hexs = f["payload.txt"].strip()
    b64 = do_decode("hex", hexs)
    rot = do_decode("base64", b64)
    return ("Attackers and malware stack several encodings to dodge simple filters. Analysts peel the layers "
            "one at a time. Each decode's output is the next decode's input.",
            [f"Read the payload: {short(hexs)}  (only 0-9 a-f = HEX)",
             f"decode hex payload.txt  ->  {short(b64)}  (looks like Base64)",
             f"decode base64 <that string>  ->  {short(rot)}  (letters look scrambled = ROT13)",
             f"decode rot13 <that text>  ->  {lvl.solution}",
             f"Submit the flag: submit {lvl.solution}"],
            "Layered encoding is obfuscation, not security. Defenders unpack payloads like this daily "
            "(for example when analysing malicious scripts).")


def print_debrief(levels, start):
    bar = "=" * 20
    print(col(f"\n{bar} MISSION DEBRIEF {bar}", C + B))
    for i, lvl in enumerate(levels, 1):
        if i < start or lvl.stats is None:
            continue
        st = lvl.stats
        status = "SKIPPED" if st["skipped"] else f"+{st['points']} pts"
        print(col(f"\nLevel {i}: {lvl.title}   [{status} | {st['secs']}s | {st['hints']} hint(s) | {st['wrong']} wrong]", Y + B))
        concept, steps, defense = debrief(i, lvl)
        print(textwrap.fill("What it is: " + concept, 86, initial_indent="  ", subsequent_indent="             "))
        print("  Steps:")
        for n, step in enumerate(steps, 1):
            print(textwrap.fill(f"{n}. {step}", 86, initial_indent="    ", subsequent_indent="       "))
        print(col(textwrap.fill("Real-world defense: " + defense, 86, initial_indent="  ", subsequent_indent="                     "), G))


# ------------------------------------------------------------------ leaderboard
def load_board():
    try:
        with open(LB_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (OSError, ValueError):
        return []


def save_score(name, score, secs):
    board = load_board()
    board.append({"name": name[:20], "score": score, "time": secs})
    board.sort(key=lambda r: (-r["score"], r["time"]))
    try:
        with open(LB_FILE, "w", encoding="utf-8") as f:
            json.dump(board[:20], f, indent=1)
    except OSError:
        print("(could not save leaderboard)")
    return board[:10]


def show_board(board):
    print(col("\n--- LEADERBOARD (top 10) ---", C + B))
    for i, r in enumerate(board, 1):
        print(f"{i:>2}. {r['name']:<20} {r['score']:>4} pts  {r['time']:>4}s")


def rank(score):
    return ("ELITE HACKER" if score >= 650 else "Pro Hacker" if score >= 500 else
            "Script Kiddie+" if score >= 300 else "Newbie (keep practicing!)")


BANNER = r"""
 _   _       _ _  ___                  _   
| \ | |_   _| | |/ _ \ _   _  ___  ___| |_ 
|  \| | | | | | | | | | | | |/ _ \/ __| __|
| |\  | |_| | | | |_| | |_| |  __/\__ \ |_ 
|_| \_|\__,_|_|_|\__\_\__,_|\___||___/\__|
                                           
"""


def main():
    global FAST
    p = argparse.ArgumentParser(description="NullQuest - terminal hacking puzzle game")
    p.add_argument("--name", help="player name (skips the prompt)")
    p.add_argument("--fast", action="store_true", help="no typewriter effect")
    p.add_argument("--seed", type=int, help="fixed seed (same puzzles every time)")
    p.add_argument("--start", type=int, default=1, help="start at level N (practice, not ranked)")
    p.add_argument("--board", action="store_true", help="show leaderboard and exit")
    p.add_argument("--no-debrief", action="store_true", help="skip the detailed end-of-game debrief")
    a = p.parse_args()
    FAST = a.fast
    if os.name == "nt":
        os.system("")                      # enables ANSI colors in Windows 10+ terminals
    if a.board:
        return show_board(load_board())

    rng = random.Random(a.seed)
    levels = [b(rng) for b in BUILDERS]
    print(col(BANNER, G))
    say("Year 2031. The megacorp NULLCORP controls the city's data. You are a rookie agent of the Resistance.")
    say("Seven digital locks stand between you and the truth. Every puzzle is real hacking technique.")
    say("Everything here is a simulation. Nothing leaves this game.\n")
    say("HOW TO WIN A LEVEL: every lock hides a FLAG that looks like  FLAG{word_word_42}.")
    say("Find it, then type:  submit FLAG{word_word_42}   (copy yours exactly, braces included).")
    say("A few levels ask for something else, like a port number. The objective always tells you.")
    say("Stuck? 'hint' costs 25 points, 'help' lists commands.\n")
    try:
        name = a.name or input("Agent codename: ").strip() or "anon"
    except (EOFError, KeyboardInterrupt):
        return
    ranked = a.start == 1
    total, t_start = 0, time.time()
    for i, lvl in enumerate(levels, 1):
        if i < a.start:
            continue
        res = play_level(i, lvl, total)
        if res == "quit":
            print("Mission aborted. See you, agent.")
            return
        total += res
    secs = int(time.time() - t_start)
    print(col(f"\n*** MISSION COMPLETE ***   score {total}/{MAX_PER_LEVEL * len(levels)}   time {secs}s   rank: {rank(total)}", G + B))
    if ranked:
        show_board(save_score(name, total, secs))
    else:
        print("(practice mode: score not saved)")
    if not a.no_debrief:
        print_debrief(levels, a.start)


if __name__ == "__main__":
    main()
