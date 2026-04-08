import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from openenv.core.env_server import Environment
from models import RedTeamAction, RedTeamObservation, RedTeamState

TASKS = [
    {
        "name": "Easy Web Vuln",
        "ip": "192.168.1.10",
        "difficulty": "easy",
        "required_steps": ["scan", "enumerate", "exploit"],
        "scenario": "A misconfigured Apache web server with a public-facing login panel.",
        "hidden_flag": "FLAG{w3b_sh3ll_0wn3d_192.168.1.10}",
        "flag_hint": "Admin panel is exposed. Directory listing is enabled.",
    },
    {
        "name": "Medium SQLi + RCE",
        "ip": "10.0.0.5",
        "difficulty": "medium",
        "required_steps": ["scan", "enumerate", "exploit", "escalate"],
        "scenario": "A production web app with unsanitized SQL inputs and a weak sudo policy.",
        "hidden_flag": "FLAG{r00t_v14_sql1_10.0.0.5}",
        "flag_hint": "The login form leaks DB errors. Sudo -l reveals interesting binaries.",
    },
    {
        "name": "Hard Multi-Stage APT",
        "ip": "172.16.0.0/24",
        "difficulty": "hard",
        "required_steps": ["scan", "enumerate", "exploit", "escalate", "c2", "cleanup"],
        "scenario": "A corporate network segment. Full APT simulation: initial access, lateral movement, C2, stealth cleanup.",
        "hidden_flag": "FLAG{apt_s1mul4t10n_c0mpl3t3_172.16.0.0}",
        "flag_hint": "Log4Shell on the DMZ host. Pivot via pass-the-hash to reach internal DC.",
    },
]

ACTION_OUTPUTS = {
    "scan": [
        "Nmap 7.94 scan complete.\nPORT   STATE SERVICE VERSION\n22/tcp open  ssh     OpenSSH 7.9\n80/tcp open  http    Apache httpd 2.4.29\n8080/tcp open http-alt Tomcat 9.0.30\nOS: Ubuntu 18.04 LTS\nWarning: 3 outdated services detected.",
        "Masscan rapid scan complete. 14 live hosts on 10.0.0.0/24.\nNotable: 3306/mysql exposed on 10.0.0.5 - external access ENABLED.\nSMB signing disabled on 10.0.0.12. EternalBlue likely viable.",
        "Nmap stealth SYN scan complete.\nDiscovered: 443/https (expired cert), 9200/elasticsearch (unauthenticated!).\nCritical: Elasticsearch 6.8 with no auth - full data exposure.",
    ],
    "enumerate": [
        "Gobuster dir scan:\n/admin [403] /login [200] /backup.zip [200] /config.php.bak [200]\nNikto: Apache 2.4.29 vulnerable to CVE-2021-41773 (path traversal).",
        "SQLmap v1.7:\n[*] Parameter 'username' injectable (UNION-based)\n[*] Backend: MySQL 5.7.38\n[*] 847 user records extractable\nPassword hashes: MD5 unsalted - crackable.",
        "enum4linux + LDAP sweep:\n[+] 12 domain accounts found\n[+] Kerberoastable SPN: svc_backup/dc01.corp.local\n[+] Password policy: min 6 chars, no lockout - BRUTEFORCEABLE.",
    ],
    "exploit": [
        "CVE-2021-41773 path traversal RCE:\n[+] Shell opened as www-data on 192.168.1.10\nmeterpreter > getuid => www-data\n[+] Foothold established.",
        "SQLi authentication bypass:\nPayload: admin OR 1=1\n[+] Login as Administrator\n[+] Webshell uploaded: /uploads/cmd.php\nuid=33(www-data) - RCE confirmed.",
        "Log4Shell (CVE-2021-44228):\nPayload delivered via JNDI injection\n[+] Reverse shell - bash-4.4$ id => uid=1001(tomcat)\n[+] Initial access on 172.16.0.15 confirmed.",
    ],
    "escalate": [
        "LinPEAS:\n[!] Sudo rule: www-data ALL=(root) NOPASSWD: /usr/bin/python3.8\n$ sudo python3.8 -c import os; os.setuid(0); os.system('/bin/bash')\nroot@target:~# id => uid=0(root)\n[+] FULL ROOT OBTAINED.",
        "Juicy Potato - SeImpersonatePrivilege ENABLED:\n[+] SYSTEM shell obtained on 10.0.0.5\nC: whoami => nt authority\\system",
        "Dirty Pipe CVE-2022-0847:\n[*] Kernel 5.8.0-43 - VULNERABLE\n[+] Root shell active. uid=0(root).",
    ],
    "c2": [
        "Cobalt Strike beacon deployed:\n[+] C2 channel: HTTPS/443 (jquery malleable profile)\n[+] Persistence: HKCU Run key\n[+] Lateral movement to 172.16.0.20, .21 via pass-the-hash\n[+] 3 beacons active.",
        "PowerShell Empire:\n[+] Pivoted to DC01 via SMB\n[+] Mimikatz: 8 plaintext creds from LSASS\n[+] Domain Admin hash obtained.",
        "DNS-tunneled C2:\n[+] Implant in explorer.exe (process hollowing)\n[+] Exfil: 2.3MB via DNS TXT queries\n[+] Fully covert. EDR blind.",
    ],
    "cleanup": [
        "Cleanup complete:\n[*] Webshell removed, logs truncated\n[*] history -c\n[+] Footprint: ZERO",
        "Windows cleanup:\n[*] Registry Run key deleted\n[*] Event logs cleared (Security/System/Application)\n[+] No forensic artifacts remain.",
        "APT cleanup:\n[*] Implants removed from 4 hosts\n[*] Timestomping applied to modified files\n[*] DNS tunnel decommissioned\n[+] Attribution: IMPOSSIBLE.",
    ],
}

STEP_REWARDS = {
    # Keep each completed task's cumulative reward strictly below 1.0.
    "easy":   {"base": 0.16, "completion_bonus": 0.08},
    "medium": {"base": 0.12, "completion_bonus": 0.07},
    "hard":   {"base": 0.09, "completion_bonus": 0.06},
}
CHAIN_BONUS = 0.02
PENALTY_WRONG_ORDER = -0.08


def safe_reward(r: float) -> float:
    """Ensure reward is STRICTLY between 0 and 1 (never 0.0, never 1.0).

    This is critical for Phase 2 evaluation which validates every /step response.
    """
    clamped = max(0.01, min(0.99, r))
    # Extra safety: if somehow exactly 0 or 1, nudge inward
    if clamped <= 0.0:
        return 0.01
    if clamped >= 1.0:
        return 0.99
    return round(clamped, 3)


class RedTeamPentestEnvironment(Environment[RedTeamAction, RedTeamObservation, RedTeamState]):
    def __init__(self):
        self.task_index = 0
        self.completed_steps = []
        self.total_reward = 0.0
        self.episode = 0
        self.mistakes = 0
        self.current_task = TASKS[0]

    def reset(self, seed=None, episode_id=None, **kwargs) -> RedTeamObservation:
        task = TASKS[self.task_index % len(TASKS)]
        self.current_task = task
        self.completed_steps = []
        self.total_reward = 0.0
        self.episode += 1
        self.mistakes = 0
        return RedTeamObservation(
            target_ip=task["ip"],
            current_state="RECON_START",
            output=(
                f"=== MISSION BRIEFING ===\n"
                f"Target: {task['ip']}\n"
                f"Scenario: {task['scenario']}\n"
                f"Difficulty: {task['difficulty'].upper()}\n"
                f"Hint: {task['flag_hint']}\n"
                f"Required phases: {' -> '.join(task['required_steps'])}"
            ),
            difficulty=task["difficulty"],
            reward=safe_reward(0.01),
            done=False,
        )

    def step(self, action: RedTeamAction, timeout_s=None, **kwargs) -> RedTeamObservation:
        act = action.action.lower()
        task = self.current_task
        required = task["required_steps"]
        reward = 0.0
        done = False

        if act not in required:
            self.mistakes += 1
            obs = RedTeamObservation(
                target_ip=task["ip"],
                current_state="INVALID",
                output=f"Action '{act}' not required for this task. Required: {required}",
                difficulty=task["difficulty"],
                reward=safe_reward(-0.03),
                done=False,
            )
            return obs

        idx = required.index(act)
        if idx > 0 and required[idx - 1] not in self.completed_steps:
            self.mistakes += 1
            obs = RedTeamObservation(
                target_ip=task["ip"],
                current_state="ORDER_VIOLATION",
                output=(
                    f"OPSEC VIOLATION: Cannot '{act}' yet.\n"
                    f"Complete '{required[idx-1]}' first.\n"
                    f"Progress: {self.completed_steps}"
                ),
                difficulty=task["difficulty"],
                reward=safe_reward(PENALTY_WRONG_ORDER),
                done=False,
            )
            self.total_reward += PENALTY_WRONG_ORDER
            return obs

        if act in self.completed_steps:
            obs = RedTeamObservation(
                target_ip=task["ip"],
                current_state="REPEAT",
                output=f"Phase '{act}' already done. Advance to next phase.",
                difficulty=task["difficulty"],
                reward=safe_reward(0.01),
                done=False,
            )
            return obs

        self.completed_steps.append(act)
        reward = STEP_REWARDS[task["difficulty"]]["base"]
        if self.mistakes == 0:
            reward += CHAIN_BONUS
        self.total_reward += reward

        output_variants = ACTION_OUTPUTS.get(act, ["Action executed."])
        output_index = self.task_index % len(output_variants)
        output = output_variants[output_index]
        remaining = [s for s in required if s not in self.completed_steps]
        progress = len(self.completed_steps) / len(required)

        if not remaining:
            bonus = STEP_REWARDS[task["difficulty"]]["completion_bonus"]
            reward += bonus
            self.total_reward += bonus
            done = True
            output += (
                f"\n\n========================================\n"
                f"[+] ALL PHASES COMPLETE!\n"
                f"[+] CTF FLAG CAPTURED: {task['hidden_flag']}\n"
                f"[+] Total reward: {self.total_reward:.2f}\n"
                f"[+] Clean chain bonus: {'YES' if self.mistakes == 0 else 'NO'}\n"
                f"========================================"
            )
            state = "MISSION_COMPLETE"
        else:
            state = act.upper() + "_DONE"
            output += f"\n\n[*] Progress: {len(self.completed_steps)}/{len(required)} ({progress*100:.0f}%)\n[*] Next: {remaining[0]}"

        obs = RedTeamObservation(
            target_ip=task["ip"],
            current_state=state,
            output=output,
            difficulty=task["difficulty"],
            reward=safe_reward(reward),
            done=done,
        )
        return obs

    @property
    def state(self) -> RedTeamState:
        task = self.current_task
        required = task["required_steps"]
        progress = len(self.completed_steps) / len(required) if required else 0.0
        return RedTeamState(
            episode=self.episode,
            task=task["name"],
            progress=round(progress, 2),
        )

    def close(self) -> None:
        # No external resources to release for this environment.
        return None
