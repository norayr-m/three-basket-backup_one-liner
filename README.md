# Three Basket Egg Save

> This is an amateur engineering project. We are not HPC professionals and make no competitive claims.

**One line. Three baskets. I-frame / P-frame differential backup.**

**[Live Demo →](https://norayr-m.github.io/three-basket-backup_one-liner/)**

```python
tick = lambda f, d: (baskets[d % 3].i_frame() if not f else baskets[f % 3].p_frame())
```

The entire distributed backup scheduler. Two modulos. Coprime rotation handles the rest.

---

## What This Is

A retro-game-style visualizer for a distributed backup protocol that fits in a single Python lambda. A pixel chicken lays eggs into three independent baskets, rotating with coprime arithmetic. Golden eggs = full snapshots (I-frames). Normal eggs = incremental deltas (P-frames).

Inspired by MPEG video encoding: I-frames (keyframes) and P-frames (predicted frames), applied to backup infrastructure across three independent storage targets.

## The Math

Every 2 hours, one basket receives an egg. `f % 3` picks the basket. Frame 0 of each day is an I-frame, `d % 3` rotates which basket gets it. Since 4 and 3 are coprime, rotation is automatic — no scheduling table, no config, no cron. One counter. One modulo. Three baskets.

**Properties:** Fresh I-frame somewhere every day. Each basket independently recoverable. P-frames use hard-link deduplication (kilobytes each). Worst-case data loss: 2 hours.

## Files

| File | What | Live |
|------|------|------|
| `index.html` | Retro pixel chicken visualizer. Clucking included. | [Open →](https://norayr-m.github.io/three-basket-backup_one-liner/) |
| `volume.html` | Phase 16 Volumetric LGA. 4K tetrahedron lattice running the lambda as a 3D lattice gas automaton. | [Open →](https://norayr-m.github.io/three-basket-backup_one-liner/volume.html) |
| `backup.py` | The real scheduler. `--tick`, `--daemon`, `--status`, `--dry-run`. tar/rsync under the hood. | — |

## Run the Backup

```bash
python backup.py --dry-run          # Preview next 24 ticks
python backup.py                    # Single tick (cron / launchd)
python backup.py --daemon           # Continuous (2hr interval)
python backup.py --status           # Check state
python backup.py --config conf.json # Custom config
```

Default config backs up `~/Documents` to three cloud folders (Dropbox, iCloud, Google Drive). Edit `DEFAULT_CONFIG` in `backup.py` or pass a JSON config file.

## 7 More Applications

The same `(mod 3, period 12, I/P)` abstract machine governs at least 7 other production systems. Same lambda. Different substrate.

1. **DNA Codon Reading Frames** — RNA polymerase reads in `[d % 3]` triplets. The reading frame shift is a mod 3 error. Not analogy — biochemistry.
2. **3-Phase Power Grid** — Three phases, 120° apart, 60 Hz. Load recalibration rotates across phases. The grid runs this lambda in copper and iron.
3. **MPEG Video Compression** — Standard 12-frame GOP. 1 I-frame + 11 P-frames. The literal syntax origin.
4. **ZFS / RAID Scrub Rotation** — Rotate the heavy surface scrub across drives. Float parity checks between.
5. **Database Replica Sync** — WAL streaming = P-frames. `pg_basebackup` = I-frame. Every Postgres cluster on Earth.
6. **Distributed Consensus (Raft)** — Rotate which node compacts its log (I-frame). Others stream append entries (P-frames). How etcd keeps Kubernetes alive.
7. **Kissing Number in R³** — 12 is provably optimal for sphere packing in 3D (Schütte & van der Waerdt, 1953). The (3, 12) pair has a geometric reason.

**Bonus: [Volumetric Lattice Gas Automaton →](https://norayr-m.github.io/three-basket-backup_one-liner/volume.html)** — Classical LGAs leak energy through damping multipliers (0.992× per tick). This one doesn't. It runs the same I/P lambda, but rotates absolute state snapshots and 6-neighbor kinetic deltas across three state reels in a 16³ tetrahedron lattice. I-frame resets one reel to ground truth; 11 P-frames propagate entropy between neighbors at zero loss. No damping. No artificial viscosity. Conservation by structure, not by patch. Bayer RGGB coloring maps `(x + y·2 + z·3) % 4` — the same mod arithmetic inside every camera sensor.

---

## Author

**Norayr Matevosyan**

## AI Co-Authorship

All visualizations and the backup scheduler were co-authored with AI assistants: [Claude](https://claude.ai) (Anthropic) for architecture, code, and the chicken; [Gemini](https://gemini.google.com) (Google) for the volumetric LGA and zero-loss conservation proof. The humans defined the math. The machines wrote the code. Both are credited.

## License

GPL-3.0
