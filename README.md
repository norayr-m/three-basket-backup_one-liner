# Three Basket Egg Save

**One line. Three baskets. I-frame / P-frame differential backup.**

```python
tick = lambda f, d: (baskets[d % 3].i_frame() if not f else baskets[f % 3].p_frame())
```

That's the entire distributed backup scheduler. Two modulos. Coprime rotation handles the rest.

---

## What This Is

A retro-game-style visualizer for a distributed backup protocol that fits in a single Python lambda. A pixel chicken lays eggs into three independent baskets, rotating with coprime arithmetic. Golden eggs are full snapshots (I-frames). Normal eggs are incremental deltas (P-frames). The math distributes I-frames evenly across all three baskets without any scheduling logic — the coprime does it for free.

Inspired by video encoding: I-frames (keyframes) and P-frames (predicted frames), applied to backup infrastructure across three independent storage targets.

## The Math

Every 2 hours, one basket receives an egg. `f % 3` picks the basket. Frame 0 of each day is an I-frame (golden egg), and `d % 3` rotates which basket gets it. Since each day has 12 frames across 3 baskets, and the day counter advances independently, every basket gets a golden egg every 3 days — no scheduling table, no config, no cron. One counter. One modulo. Three baskets.

**Properties:** fresh I-frame somewhere every day. Each basket independently recoverable. P-frames use hard-link deduplication (kilobytes each). Worst-case data loss: 2 hours.

## Files

| File | What |
|------|------|
| `backup.py` | The real scheduler. `--tick`, `--daemon`, `--status`, `--dry-run`. tar/rsync under the hood. |
| `index.html` | Retro pixel chicken visualizer. Open in browser. Clucking included. |
| `vote.html` | Claude vs Nova: top 7 + 7 bonus applications of the lambda across 14 domains. |

## Run the Backup

```bash
# Single tick (cron / launchd)
python backup.py

# Daemon mode (Demerzel)
python backup.py --daemon

# Preview next 24 ticks
python backup.py --dry-run

# Check state
python backup.py --status

# Custom config
python backup.py --config my_config.json
```

Default config backs up `~/Documents` to three cloud folders (Dropbox, iCloud, Google Drive). Edit `DEFAULT_CONFIG` in `backup.py` or pass a JSON config file.

## Run the Visualizer

Open `index.html` in a browser. No dependencies.

---

All visualizations and code were co-authored with Claude (Anthropic) and Gemini (Google).

## Author

Norayr Matevosyan

## License

GPL-3.0
