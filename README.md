# 🕹️ NullQuest
 
> A terminal hacking puzzle game in **pure Python**: 7 story levels, each one teaches a real security skill. 🐍
> Beat the megacorp NULLCORP, earn points, climb the leaderboard. 🏆
 
![python](https://img.shields.io/badge/python-3.8+-blue?logo=python&logoColor=white)
![deps](https://img.shields.io/badge/dependencies-none-brightgreen)
![status](https://img.shields.io/badge/status-learning%20project-orange)
![license](https://img.shields.io/badge/license-MIT-green)
 
---
 
## 🤔 What is this?
 
You play a rookie agent of the Resistance. Each level is a small puzzle that uses a **real hacking technique**,
inside a safe simulated shell. It is meant for beginners who want to learn by playing. 🎮
 
> ✅ **Everything is simulated.** The game never touches your network, your files or any real server.
 
## 🎯 The 7 levels
 
| # | Level | Skill you learn |
|---|-------|-----------------|
| 1 | Warm-up: Intercepted Message | **Base64** decoding 🔤 |
| 2 | Caesar's Ghost | **Caesar cipher** and brute force 🏛️ |
| 3 | Needle in the Logs | **Log analysis** with `grep` and regex 🔍 |
| 4 | Crack the Hash | **Dictionary attack** on password hashes 🔑 |
| 5 | Scan the Target | **Port scanning** and spotting insecure services 📡 |
| 6 | The Broken Login | **SQL injection** against a real (throwaway) query 💉 |
| 7 | Final Boss: Layers | **Chained encodings** (hex, base64, ROT13) 🧅 |
 
## 🛠️ Install and play
 
```bash
git clone https://github.com/<your-username>/nullquest.git
cd nullquest
python nullquest.py
```
 
No `pip install` needed. Works on Windows, Linux and macOS (Python 3.8+).
 
### ⚙️ Options
 
| Option | What it does |
|--------|--------------|
| `--name NAME` | Skip the name prompt |
| `--fast` | Turn off the typewriter effect |
| `--seed N` | Same puzzles every time (good for racing friends) |
| `--start N` | Practice from level N (score not saved) |
| `--board` | Show the leaderboard |
| `--no-debrief` | Skip the detailed end-of-game debrief |
 
## 🚩 How to submit a flag
 
Every level hides a **flag** that looks like `FLAG{word_word_42}`. When you find it, type `submit` followed by the flag:
 
```
[agent@L1]$ submit FLAG{silent_falcon_42}
ACCESS GRANTED!  +100 points
```
 
- Copy the flag **exactly**, including `FLAG{` and `}`. It is case-sensitive.
- Flags are **random every run**, so use the one from *your* game, not the example above.
- Wrong answers cost 5 points, and you can try again.
- A few levels differ:
  - **Level 4:** the flag is `FLAG{password}` using the password you cracked
  - **Level 5:** submit just the **port number**, e.g. `submit 2323`
  - **Level 6:** log in as admin with `login`, copy the secret it prints, then `submit` it
## 🕹️ In-game commands
 
```
ls | cat <file> | grep [-i] <pattern> <file>
decode <base64|hex|rot13|binary> <text or file>
caesar <shift|all> <text>     hash <md5|sha1|sha256> <text>
crack <hash> <wordlist>       nmap <target>      login
hint (-25 pts)   submit <answer>   skip   score   quit
```
 
## 🏅 Scoring
 
- Each level is worth **100 points**
- **-25** per hint, **-5** per wrong answer, and a small penalty if you take very long
- Skipping a level gives 0 points
- Flags and data are **randomized every run**, so you can't just copy answers from the internet 😉
- Max score: **700**. Ranks: Newbie, Script Kiddie+, Pro Hacker, ELITE HACKER
## 📋 Mission debrief
 
When you finish, NullQuest prints a **detailed debrief for every level**:
- 📊 your result (points, time, hints, wrong answers)
- 🧠 what the technique is
- 🪜 the exact steps to solve it, using **your own run's data**
- 🛡️ how real systems defend against it
Skipped a level? The debrief shows the full solution so you still learn it.
 
## 🧪 Test it
 
```bash
python test_playthrough.py
```
It plays the whole game through stdin with the known solutions to prove every level is solvable.
 
## 🔐 How level 6 stays safe
 
The SQL injection level runs a *real* vulnerable query, but only against a tiny **in-memory** SQLite database.
An authorizer allows `SELECT` only, a progress handler stops runaway queries after 1.5 seconds, and
nothing is written to disk.
 
## 📖 What I learned building this
 
- How Base64, hex and ROT13 differ and how to peel layered encodings 🧅
- How dictionary attacks work against unsalted hashes 🔑
- Why building SQL by string concatenation is dangerous 💉
- Sandboxing an exploit demo (authorizer, timeouts, in-memory DB) 🧰
## 🗺️ Roadmap
 
- [ ] More levels: XSS, JWT forging, steganography, file carving
- [ ] Timed "speedrun" mode
- [ ] Online leaderboard
- [ ] Colored hints per skill level
- [ ] Level editor so friends can add puzzles
## 📄 License
 
MIT
 
