#!/usr/bin/env python3
"""
Three Basket Backup — I/P Frame Differential Backup with Coprime Rotation

One lambda. Three baskets. Coprime rotation distributes I-frames (full snapshots)
and P-frames (incremental deltas) across three independent storage targets.

Schedule:
  - P-frame every hour, rotating baskets via f % 3
  - Every 4th frame is an I-frame, rotating via (f // 4) % 3
  - Each basket gets a full I-frame every 3 cycles (12 hours)

Usage:
  python backup.py                          # run one tick (cron / launchd)
  python backup.py --daemon                 # run continuously (Euler Clock mode)
  python backup.py --status                 # show current state
  python backup.py --config config.json     # custom config

The entire scheduling logic:
  tick = lambda f, d: (reels[d%3].i_frame() if not f else reels[f%3].p_frame())
"""

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ─── Configuration ───────────────────────────────────────────────────────────

DEFAULT_CONFIG = {
    "source": "~/Documents",
    "baskets": [
        {"name": "basket_0", "path": "~/Dropbox/backup"},
        {"name": "basket_1", "path": "~/Library/Mobile Documents/com~apple~CloudDocs/backup"},
        {"name": "basket_2", "path": "~/Google Drive/backup"},
    ],
    "interval_seconds": 3600,       # 1 hour between ticks
    "i_frame_every": 4,             # every 4th tick is an I-frame
    "state_file": "~/.three-basket-state.json",
    "log_file": "~/.three-basket.log",
    "exclude": [".DS_Store", "*.tmp", "__pycache__", ".git", "node_modules"],
}


# ─── State ───────────────────────────────────────────────────────────────────

@dataclass
class BackupState:
    frame: int = 0
    day: int = 0
    last_tick: Optional[str] = None
    last_i_frame: dict = field(default_factory=lambda: {"basket_0": None, "basket_1": None, "basket_2": None})
    last_p_frame: dict = field(default_factory=lambda: {"basket_0": None, "basket_1": None, "basket_2": None})
    history: list = field(default_factory=list)

    @classmethod
    def load(cls, path: str) -> "BackupState":
        p = Path(path).expanduser()
        if p.exists():
            with open(p) as f:
                data = json.load(f)
            return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        return cls()

    def save(self, path: str):
        p = Path(path).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w") as f:
            json.dump(asdict(self), f, indent=2)


# ─── Core: The Lambda ────────────────────────────────────────────────────────
#
#   tick = lambda f, d: (reels[d%3].i_frame() if not f else reels[f%3].p_frame())
#
#   f = frame counter (within day), d = day counter
#   f == 0 → I-frame on basket[d % 3]
#   f >  0 → P-frame on basket[f % 3]
#
# Generalized version below supports configurable I-frame frequency.
# ─────────────────────────────────────────────────────────────────────────────


def resolve_tick(frame: int, i_every: int, n_baskets: int = 3) -> tuple:
    """
    Determine basket index and frame type for a given global frame counter.

    Returns (basket_index, is_i_frame)

    Logic:
      - f_in_cycle = frame % (i_every * n_baskets)
      - If f_in_cycle % i_every == 0 → I-frame, basket = (f_in_cycle // i_every) % n_baskets
      - Otherwise → P-frame, basket = f_in_cycle % n_baskets
    """
    cycle_len = i_every * n_baskets
    f = frame % cycle_len

    if f % i_every == 0:
        # I-frame: which basket gets the full snapshot
        basket = (f // i_every) % n_baskets
        return basket, True
    else:
        # P-frame: rotate across baskets
        basket = f % n_baskets
        return basket, False


# ─── Backup Operations ───────────────────────────────────────────────────────

def build_exclude_args(excludes: list) -> list:
    args = []
    for ex in excludes:
        args.extend(["--exclude", ex])
    return args


def i_frame(source: str, dest: str, excludes: list) -> dict:
    """
    Full snapshot backup using tar + gzip.
    Creates: {dest}/i-frame_{timestamp}.tar.gz
    """
    src = Path(source).expanduser().resolve()
    dst = Path(dest).expanduser().resolve()
    dst.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    archive = dst / f"i-frame_{ts}.tar.gz"

    exclude_args = []
    for ex in excludes:
        exclude_args.extend([f"--exclude={ex}"])

    cmd = ["tar", "-czf", str(archive), *exclude_args, "-C", str(src.parent), src.name]

    t0 = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.time() - t0

    size = archive.stat().st_size if archive.exists() else 0

    return {
        "type": "I-frame",
        "archive": str(archive),
        "size_bytes": size,
        "elapsed_s": round(elapsed, 2),
        "returncode": result.returncode,
        "stderr": result.stderr.strip() if result.returncode != 0 else None,
    }


def p_frame(source: str, dest: str, excludes: list, link_dest: Optional[str] = None) -> dict:
    """
    Incremental delta backup using rsync --link-dest.
    Each P-frame directory appears complete via hard links but only stores changed bytes.
    Creates: {dest}/p-frame_{timestamp}/
    """
    src = Path(source).expanduser().resolve()
    dst = Path(dest).expanduser().resolve()
    dst.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    target = dst / f"p-frame_{ts}"
    target.mkdir(parents=True, exist_ok=True)

    cmd = [
        "rsync", "-a", "--delete",
        *build_exclude_args(excludes),
        str(src) + "/",
        str(target) + "/",
    ]

    # --link-dest: previous P-frame or most recent I-frame extraction
    if link_dest and Path(link_dest).exists():
        cmd.insert(3, f"--link-dest={link_dest}")

    t0 = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.time() - t0

    # Approximate size: only new/changed files
    size = sum(f.stat().st_size for f in target.rglob("*") if f.is_file() and f.stat().st_nlink == 1)

    return {
        "type": "P-frame",
        "directory": str(target),
        "new_bytes": size,
        "elapsed_s": round(elapsed, 2),
        "returncode": result.returncode,
        "stderr": result.stderr.strip() if result.returncode != 0 else None,
    }


# ─── Tick ────────────────────────────────────────────────────────────────────

def run_tick(config: dict, state: BackupState) -> dict:
    """Execute one tick of the backup scheduler."""

    baskets = config["baskets"]
    n = len(baskets)
    i_every = config.get("i_frame_every", 4)

    basket_idx, is_i = resolve_tick(state.frame, i_every, n)
    basket = baskets[basket_idx]
    basket_name = basket["name"]

    now = datetime.now(timezone.utc).isoformat()

    if is_i:
        result = i_frame(config["source"], basket["path"], config.get("exclude", []))
        state.last_i_frame[basket_name] = now
    else:
        # Find last P-frame dir for --link-dest
        last_p = state.last_p_frame.get(basket_name)
        result = p_frame(config["source"], basket["path"], config.get("exclude", []), link_dest=last_p)
        if result["returncode"] == 0:
            state.last_p_frame[basket_name] = result.get("directory")

    # Update state
    entry = {
        "frame": state.frame,
        "basket": basket_name,
        "basket_idx": basket_idx,
        **result,
        "timestamp": now,
    }

    state.history.append(entry)
    # Keep last 100 entries
    if len(state.history) > 100:
        state.history = state.history[-100:]

    state.last_tick = now
    state.frame += 1

    return entry


# ─── Logging ─────────────────────────────────────────────────────────────────

def log(msg: str, log_file: Optional[str] = None):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    if log_file:
        p = Path(log_file).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a") as f:
            f.write(line + "\n")


# ─── CLI ─────────────────────────────────────────────────────────────────────

def load_config(config_path: Optional[str]) -> dict:
    if config_path and Path(config_path).expanduser().exists():
        with open(Path(config_path).expanduser()) as f:
            return json.load(f)
    return DEFAULT_CONFIG.copy()


def cmd_status(config: dict, state: BackupState):
    n = len(config["baskets"])
    i_every = config.get("i_frame_every", 4)

    print(f"\n  Three Basket Backup — Status")
    print(f"  {'─' * 40}")
    print(f"  Frame:       {state.frame}")
    print(f"  Last tick:   {state.last_tick or 'never'}")
    print(f"  I-every:     {i_every} ticks")
    print(f"  Baskets:     {n}")

    # Next tick preview
    basket_idx, is_i = resolve_tick(state.frame, i_every, n)
    basket_name = config["baskets"][basket_idx]["name"]
    frame_type = "I-frame (full)" if is_i else "P-frame (delta)"
    print(f"\n  Next tick:   frame {state.frame} → {basket_name} [{frame_type}]")

    # Per-basket status
    print(f"\n  {'Basket':<12} {'Last I-frame':<24} {'Last P-frame':<24}")
    print(f"  {'─' * 60}")
    for b in config["baskets"]:
        name = b["name"]
        li = state.last_i_frame.get(name, "never") or "never"
        lp = state.last_p_frame.get(name, "never") or "never"
        # Truncate paths for display
        if lp != "never":
            lp = Path(lp).name if len(str(lp)) > 20 else lp
        print(f"  {name:<12} {str(li):<24} {str(lp):<24}")

    # Last 5 history entries
    if state.history:
        print(f"\n  Recent history:")
        for entry in state.history[-5:]:
            typ = "I" if entry["type"] == "I-frame" else "P"
            bkt = entry["basket"]
            ts = entry.get("timestamp", "?")[:19]
            size = entry.get("size_bytes", entry.get("new_bytes", 0))
            size_str = f"{size / 1024:.0f}K" if size < 1048576 else f"{size / 1048576:.1f}M"
            rc = entry.get("returncode", "?")
            status = "ok" if rc == 0 else f"err({rc})"
            print(f"    f{entry['frame']:>4} [{typ}] → {bkt:<12} {size_str:>8}  {status}  {ts}")

    print()


def cmd_tick(config: dict, state: BackupState):
    log_file = config.get("log_file")
    state_file = config.get("state_file", DEFAULT_CONFIG["state_file"])

    n = len(config["baskets"])
    i_every = config.get("i_frame_every", 4)
    basket_idx, is_i = resolve_tick(state.frame, i_every, n)
    basket = config["baskets"][basket_idx]

    typ = "I-frame" if is_i else "P-frame"
    log(f"tick f={state.frame} → {basket['name']} [{typ}]", log_file)

    result = run_tick(config, state)

    if result.get("returncode", 1) == 0:
        size = result.get("size_bytes", result.get("new_bytes", 0))
        log(f"  done in {result['elapsed_s']}s, {size} bytes", log_file)
    else:
        log(f"  ERROR: {result.get('stderr', 'unknown')}", log_file)

    state.save(state_file)
    return result


def cmd_daemon(config: dict, state: BackupState):
    interval = config.get("interval_seconds", 3600)
    log_file = config.get("log_file")

    log(f"daemon mode — interval {interval}s, Ctrl+C to stop", log_file)

    while True:
        try:
            cmd_tick(config, state)
            time.sleep(interval)
        except KeyboardInterrupt:
            log("daemon stopped by user", log_file)
            break


def main():
    parser = argparse.ArgumentParser(
        description="Three Basket Backup — I/P frame differential backup with coprime rotation",
        epilog="tick = lambda f, d: (reels[d%%3].i_frame() if not f else reels[f%%3].p_frame())",
    )
    parser.add_argument("--config", "-c", help="config JSON file")
    parser.add_argument("--status", "-s", action="store_true", help="show current state")
    parser.add_argument("--daemon", "-d", action="store_true", help="run continuously")
    parser.add_argument("--dry-run", action="store_true", help="show what would happen without executing")

    args = parser.parse_args()
    config = load_config(args.config)
    state_file = config.get("state_file", DEFAULT_CONFIG["state_file"])
    state = BackupState.load(state_file)

    if args.status:
        cmd_status(config, state)
    elif args.dry_run:
        n = len(config["baskets"])
        i_every = config.get("i_frame_every", 4)
        print(f"\nDry run — next 24 ticks:\n")
        print(f"  {'Frame':<8} {'Basket':<12} {'Type':<10}")
        print(f"  {'─' * 30}")
        for i in range(24):
            f = state.frame + i
            idx, is_i = resolve_tick(f, i_every, n)
            name = config["baskets"][idx]["name"]
            typ = "I-frame" if is_i else "P-frame"
            marker = " ◆" if is_i else ""
            print(f"  {f:<8} {name:<12} {typ:<10}{marker}")
        print()
    elif args.daemon:
        cmd_daemon(config, state)
    else:
        cmd_tick(config, state)


if __name__ == "__main__":
    main()
