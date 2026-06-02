# Three Basket Egg Save

> This is an amateur engineering project. We are not HPC professionals and make no competitive claims.

**A small backup tool that spreads your files across three storage locations on a rotating schedule.**

**[Live Demo →](https://norayr-m.github.io/three-basket-backup_one-liner/)**

---

## What it is

A simple backup scheduler. Every two hours, it copies your data to one of three storage locations (for example: Dropbox, iCloud, and Google Drive). Most copies are small — they only record what changed since the last copy. One copy a day is a full snapshot. The pattern rotates so a fresh full snapshot lives in each location at least every three days.

Three locations is the point. If one fails — service outage, account locked, drive dies, laptop stolen — the other two still have your data. There is no central scheduler that can break; the timing is decided by a single line of Python doing two simple modulo operations on a counter. Two hours of data is the worst-case loss.

The whole scheduler is one line:

```python
tick = lambda f, d: (baskets[d % 3].i_frame() if not f else baskets[f % 3].p_frame())
```

The "egg save" name is the visualizer: a pixel-style chicken lays eggs into three baskets, golden eggs are the full snapshots, normal eggs are the smaller incremental ones. Same idea video codecs use — full keyframes (I-frames) and delta frames (P-frames).

---

## Why three baskets

Three things go wrong with most backup setups:

1. **One location fails and takes everything.** If your only backup is the same cloud account that holds the live data, a single password compromise or service incident loses both copies. Three independent providers means no single failure mode wipes you out.
2. **Full backups are slow, so they happen rarely.** A 100 GB folder is not going to be re-uploaded in full every two hours. This tool does small delta backups most of the time and one full snapshot per location every three days, so each individual operation is fast and the schedule actually keeps running.
3. **Schedulers drift, get reconfigured, get forgotten.** A complex schedule (cron jobs, config tables, retry logic) is a thing that can break silently. This scheduler is a counter and two modulos. There is nothing to drift.

A side property of using three baskets and a four-tick cycle (one full + three deltas) is that the rotation works automatically without a lookup table. 4 and 3 share no common factors, so just incrementing the counter walks every (basket, frame-type) combination in turn.

---

## How it works

### The math

`f` is the in-day frame counter (resets to 0 at midnight). `d` is the day counter. Every two hours, run `tick(f, d)`:

- If `f == 0` (start of day): write a full snapshot to basket `d % 3`. Tomorrow that lands in a different basket.
- Otherwise: write an incremental delta to basket `f % 3`.

Properties:
- A fresh full snapshot lands in each basket at least every three days.
- Each basket is independently recoverable from its own full + the deltas after it.
- Deltas use hard-link deduplication, so they cost kilobytes each.
- Worst-case data loss is two hours (the next tick window).

### Files

| File | What | Live |
|------|------|------|
| `index.html` | The retro-pixel visualizer. Chicken, eggs, baskets, clucking sounds. | [Open →](https://norayr-m.github.io/three-basket-backup_one-liner/) |
| `volume.html` | A 3D variant — a 16³ tetrahedron lattice running the same one-line scheduler as a zero-loss physics simulation. | [Open →](https://norayr-m.github.io/three-basket-backup_one-liner/volume.html) |
| `backup.py` | The real backup scheduler. Uses `tar` and `rsync` under the hood. | — |

### Running it

```bash
python backup.py --dry-run          # Preview the next 24 ticks
python backup.py                    # Run a single tick (call from cron / launchd)
python backup.py --daemon           # Continuous (2-hour interval)
python backup.py --status           # Show what is in each basket
python backup.py --config conf.json # Custom config (different paths or providers)
```

Default config backs up `~/Documents` to three cloud folders (Dropbox, iCloud, Google Drive). Edit `DEFAULT_CONFIG` in `backup.py` or pass a JSON config file with your own paths.

---

## Where else the same pattern shows up

The same abstract pattern — rotate a heavy operation and a light operation across three slots on a coprime cycle — appears in at least seven other production systems. Same one-line scheduler, different substrate:

1. **DNA codon reading frames** — RNA polymerase reads genetic code in groups of three nucleotides. A reading-frame shift is a mod-3 error. Not an analogy; the same arithmetic.
2. **Three-phase power grid** — Three voltage phases at 120° offsets, 60 Hz. Load rebalancing rotates across phases. The grid runs this scheduler in copper and iron.
3. **MPEG video compression** — Standard 12-frame group-of-pictures: 1 keyframe (I-frame) + 11 predicted frames (P-frames). The naming origin for this tool.
4. **ZFS / RAID scrub rotation** — Heavy disk-integrity scans rotate across drives; light parity checks float in between.
5. **Postgres replica sync** — Write-ahead log streaming is the P-frame; `pg_basebackup` is the I-frame. Every Postgres replication cluster on Earth runs a version of this.
6. **Raft consensus** — One node compacts its log (an I-frame); the others stream append entries (P-frames). This is how etcd keeps Kubernetes alive.
7. **Kissing number in 3D** — 12 is provably the maximum number of unit spheres that can touch a central unit sphere in three dimensions (Schütte & van der Waerdt, 1953). The (3, 12) pair has a geometric reason.

**Bonus: the [volumetric variant](https://norayr-m.github.io/three-basket-backup_one-liner/volume.html).** Classical lattice-gas automata leak energy on every step (a damping multiplier, ~0.992×). This one doesn't. The same I/P scheduler rotates absolute state snapshots and 6-neighbour kinetic deltas across three state reels on a tetrahedron lattice. The I-frame resets one reel to a known ground truth; the next eleven P-frames propagate state between neighbours with zero loss. Conservation comes from the structure itself, not from a patch. The Bayer-style RGGB coloring uses `(x + y·2 + z·3) % 4` — the same mod arithmetic that lives inside every camera sensor.

---

## Author

**Norayr Matevosyan**

## AI Co-Authorship

All visualizations and the backup scheduler were co-authored with AI assistants: [Claude](https://claude.ai) (Anthropic) for architecture, code, and the chicken; [Gemini](https://gemini.google.com) (Google) for the volumetric variant and the zero-loss conservation argument. The humans defined the math. The machines wrote the code. Both are credited.

## License

Apache-2.0
