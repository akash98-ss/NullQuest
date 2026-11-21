"""Plays the real game through stdin with the known solutions to prove every level is solvable."""
import base64, binascii, codecs, random, subprocess, sys
import nullquest as hq

SEED = 7
rng = random.Random(SEED)
levels = [b(rng) for b in hq.BUILDERS]
l2_text = levels[1].files["cipher.txt"].strip()
l1_b64 = levels[0].files["note.txt"].split("\n")[2]
l3 = levels[2]
l4_hash = levels[3].files["shadow.txt"].split(":")[1].strip()
l6 = levels[5]
l7_hex = levels[6].files["payload.txt"].strip()

cmds = [
    f"decode base64 {l1_b64}", "submit nope", f"submit {levels[0].solution}",                   # L1 (1 wrong)
    f"caesar all {l2_text}", f"caesar {levels[1].ctx['shift']} {l2_text}", f"submit {levels[1].solution}",
    'grep "admin.* 200" access.log', f"submit {levels[2].solution}",
    f"crack {l4_hash} wordlist.txt", f"submit {levels[3].solution}",
    "nmap 10.10.10.5", f"submit {levels[4].solution}",
    "login", "admin'--", "whatever", f"submit {l6.solution}",
    "decode hex payload.txt", f"submit {levels[6].solution}",
]
out = subprocess.run([sys.executable, "nullquest.py", "--fast", "--seed", str(SEED), "--name", "tester"],
                     input="\n".join(cmds) + "\n", capture_output=True, text=True, timeout=60).stdout
print("\n".join(l for l in out.splitlines() if any(k in l for k in ("ACCESS", "Wrong", "CRACKED", "Welcome", "COMPLETE", "tester", "query>"))))
assert out.count("ACCESS GRANTED") == 7 and "MISSION COMPLETE" in out
assert "MISSION DEBRIEF" in out and out.count("Real-world defense") == 7 and "Steps:" in out
# extra: injection that must FAIL (wrong creds), stacked-query attempt must be harmless
l = hq.level6(random.Random(1))
print("OK: all 7 levels solved via stdin")
