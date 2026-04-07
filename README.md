---
title: Red Team Penetration Testing Lab
emoji: 🔴
colorFrom: red
colorTo: gray
sdk: docker
pinned: false
app_port: 8000
base_path: /web
tags:
  - openenv
  - cybersecurity
  - red-team
  - reinforcement-learning
---

# Red Team Penetration Testing Lab

A Mini-RL environment built on [OpenEnv](https://github.com/meta-pytorch/OpenEnv) where an AI agent acts as an **elite Red Team Penetration Tester**, executing real-world offensive security kill-chains across 3 progressive difficulty levels.

## What Makes This Unique

- **Cybersecurity domain** — Real pentest kill-chain: scan → enumerate → exploit → escalate → c2 → cleanup
- **Hidden CTF flags** — Each task reveals a unique flag only on full completion
- **Dynamic pentest reports** — Auto-generated professional report after every successful engagement
- **Chain bonus rewards** — Agent rewarded for clean OPSEC (zero violations)
- **Realistic tool output** — Nmap, SQLmap, Metasploit, Cobalt Strike style terminal output

## Tasks

| Task | Target | Difficulty | Phases |
|------|--------|-----------|--------|
| Easy Web Vuln | 192.168.1.10 | Easy | scan → enumerate → exploit |
| SQLi + RCE | 10.0.0.5 | Medium | scan → enumerate → exploit → escalate |
| Multi-Stage APT | 172.16.0.0/24 | Hard | scan → enumerate → exploit → escalate → c2 → cleanup |

## Reward Logic

| Event | Reward |
|-------|--------|
| Correct step (easy) | +0.30 |
| Correct step (medium) | +0.20 |
| Correct step (hard) | +0.13 |
| Clean chain bonus (per step) | +0.05 |
| Task completion bonus | +0.20–0.25 |
| Wrong order penalty | -0.20 |

## Quick Start
```bash
pip install openenv-core
python inference.py
```

## Actions
`scan` · `enumerate` · `exploit` · `escalate` · `c2` · `cleanup`

## Built With
- [OpenEnv](https://github.com/meta-pytorch/OpenEnv) by Meta & Hugging Face
- DeepSeek-R1 8B via Ollama
- FastAPI + Pydantic v2
