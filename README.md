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
| `volume.html` | Phase 16 Volumetric LGA. 4K wireframe tetrahedron lattice running the lambda as a 3D lattice gas automaton. Locks to Euler master clock via WebSocket. |

## Run the Backup

```bash
# Single tick (cron / launchd)
python backup.py

# Daemon mode (Euler Clock)
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

## Oh btw — 7 more applications

The same `(mod 3, period 12, I/P)` abstract machine governs at least 7 other production systems. Same lambda. Different substrate.

1. **DNA Codon Reading Frames** — RNA polymerase reads in `[d % 3]` triplets. The reading frame shift is a mod 3 error. Not analogy — biochemistry.
2. **3-Phase Power Grid** — Three phases, 120° apart, 60 Hz. Load recalibration rotates across phases. The grid runs this lambda in copper and iron.
3. **MPEG Video Compression** — Standard 12-frame GOP. 1 absolute anchor (I-frame) + 11 predicted deltas (P-frames). The literal syntax origin.
4. **ZFS / RAID Scrub Rotation** — Never scrub all drives simultaneously (I/O starvation). Rotate the heavy surface scrub. Float parity checks between.
5. **Database Replica Sync** — WAL streaming = P-frames. `pg_basebackup` = I-frame. Rotate which replica gets the full dump. Every Postgres cluster on Earth.
6. **Distributed Consensus (Raft)** — Rotate which node compacts its log (I-frame). Others stream append entries (P-frames). How etcd keeps Kubernetes alive.
7. **Kissing Number in R³** — 12 is provably optimal for sphere packing in 3D (Schütte & van der Waerdt, 1953). Each sphere touches exactly 12 neighbors. The (3, 12) pair has a geometric reason.

**Bonus: Volumetric Lattice Gas Automaton** — `volume.html` runs the lambda as a 3D physics engine. 4,096 wireframe tetrahedrons in a 16³ lattice, Bayer RGB coloring, 6-neighbor averaging with zero entropy loss. The backup scheduler becomes a thermodynamic simulation. Same tick. Different universe.

---

All visualizations and code were co-authored with Claude (Anthropic) and Gemini (Google).

## Author

Norayr Matevosyan

## License

GPL-3.0
