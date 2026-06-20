# Phase 4c — Literature Review Notes

Two primary references read in preparation for Phase 4c (Byzantine
realism upgrade for silent, delay, replay). Drafted for direct re-use
in the dissertation's Related Work and Methodology sections.

---

## Reference 1 — ByzPlug (Rocha 2024, MSc Thesis, Técnico Lisboa)

**Full title:** *ByzPlug: Reliability Testing of BFT Systems*

**What it is:** Protocol-agnostic fault-injection tool that intercepts
UDP/IP and TCP/IP traffic at the Linux kernel level via XDP + eBPF +
AF_XDP sockets. Tested on a real C++ HotStuff implementation and
exposed a safety violation in the Two-Chain HotStuff variant.

### Fault taxonomy (Section 4.5)

Three generic packet-level primitives:

| ByzPlug primitive    | Our equivalent          |
| -------------------- | ----------------------- |
| Message Omission     | `silent`                |
| Message Replay       | `replay` (duplicate)    |
| Message Modification | `equivocation`, `forgery` |

Protocol-specific composites built on the three primitives
(Section 4.6): Leader Equivocation, Forced Voting, Double Voting,
Semantically Invalid Messages.

### Replay parameterisation in ByzPlug

Algorithm 2 defines the `TxContent` Protocol Buffers message returned
by the packet manipulator service. The replay field is a single
unsigned integer:

```
required uint32 replay = 3;
```

Semantics: replay the same packet N additional times on the TX ring.
No buffer, no concept of "old" vs "new" messages, no round_id
awareness — ByzPlug is protocol-agnostic by design and cannot reason
about consensus rounds.

### Positioning of our Phase 4c against ByzPlug

| Phase 4c upgrade       | Status vs ByzPlug                                       |
| ---------------------- | ------------------------------------------------------- |
| `replay_mode=duplicate` | Equivalent to ByzPlug's `replay=1`                      |
| `replay_mode=stale`     | **Not in ByzPlug** — requires attacker state            |
| `STRICT_ROUND_VALIDATION` | **Not in ByzPlug** — black-box packet interception     |
| `delay_probability` + jitter + lognormal | **Not in ByzPlug** — no delay distributions |
| `silent_mode=prepare/commit` | **Not in ByzPlug** — protocol-agnostic, cannot distinguish PBFT phases |

### Suggested citation pattern

> Our 'duplicate' replay mode is analogous to ByzPlug's `replay`
> primitive (Rocha 2024). However, ByzPlug operates at the packet
> level and is protocol-agnostic by design, which precludes
> phase-specific omission, cross-round replay, or distribution-based
> delay modelling. Our SimPy-based simulator exploits PBFT-specific
> structure to introduce these refinements.

---

## Reference 2 — Survey on Consensus Attacks (Mastromauro et al. 2025, IEEE Access)

**Full title:** *Survey of Attacks and Defenses on Consensus
Algorithms for Secure Data Replication in Distributed Systems*

**What it is:** First systematic survey covering both classical (Raft,
Paxos, ZAB, 2PC, 3PC, VR) and modern (PBFT, Chain Replication, Gossip)
consensus algorithms, with a four-family attack taxonomy.

### Attack taxonomy (Figure 17)

| Family             | Attacks (subset relevant to PBFT)            |
| ------------------ | -------------------------------------------- |
| Majority Disruption | Partition, Eclipse, DDoS                    |
| Integrity          | Sybil, Buffer Overflow                       |
| Manipulation       | Impersonation, Log Forgery                   |
| **Communication**  | Jamming, **Replay and Message Delay Attack** |

Note: Replay and Message Delay are merged into a single attack family
("timing-based threats targeting the communication layer").

### Replay attack definition (Section VI.D.2) — verbatim

> "In a replay attack, a malicious node intercepts and stores valid
> consensus messages such as client requests, heartbeats, or inter
> node log replication messages and resends them at a later time."

> "An attacker might replay a previously valid leader heartbeat or a
> **stale proposal message** after a new leader has been elected."

> "In the aftermath of a network partition... an attacker can replay
> **outdated PREPARE or COMMIT messages** to confuse the current
> consensus round."

### Mapping to our Phase 4c.1 design

| Survey term                      | Our design element                              |
| -------------------------------- | ----------------------------------------------- |
| "intercepts and stores"          | `self.replay_buffer`                            |
| "resends them at a later time"   | `replay_mode='stale'`                           |
| "stale proposal message"         | replayed Message with old `round_id`            |
| "outdated PREPARE or COMMIT"     | our prepare/commit-typed replays from buffer    |
| "confuse the current consensus round" | the attack effect we model                  |

### PBFT-specific findings

- Table 4 lists "Replay and message delay Attack" as a documented
  PBFT threat (citing [181], [182], [195], [197], [133]) with
  documented defence mechanisms — a high-frequency attack family
  in the PBFT literature.
- Section VII.C notes "replayed messages can lead to view
  inconsistencies or duplicate transaction execution" in PBFT.
- Section V.B mentions "replaying PREPARE messages" as a manipulation
  attack vector, validating phase-specific reasoning.

### Where the survey does *not* go (our differentiators)

| Phase 4c element                 | Survey coverage                              |
| -------------------------------- | -------------------------------------------- |
| Phase-specific `silent_mode`     | No phase-level omission discussed            |
| Probabilistic delay distributions | Treated as a single "delay attack" family   |
| `STRICT_ROUND_VALIDATION` ablation | Not addressed                              |
| Quantitative behavioural feature extraction for ML monitoring | Out of scope (survey is taxonomy, not detection) |

### Suggested citation pattern

> We adopt the taxonomy of Mastromauro et al. (2025), who classify
> Byzantine attacks on consensus protocols into four families. Our
> base fault types span the Communication family (`silent`, `replay`,
> `delay`) and the Manipulation family (`equivocation`, `forgery`).
> The Phase 4c upgrades extend the Communication family with
> persistent-state stale-round replay — directly matching the survey's
> description of "stale proposal messages" replayed after view changes
> — and distribution-based delay modelling.

---

## Terminology Adopted for the Dissertation

To align with the surveyed literature:

| In code (kept as-is)           | In dissertation prose                          |
| ------------------------------ | ---------------------------------------------- |
| `replay_buffer`                | "intercepted-message buffer" / "stale-message reservoir" |
| `replay_mode='stale'`          | "stale-message replay attack" (Mastromauro 2025) |
| `STRICT_ROUND_VALIDATION`      | "round freshness validation"                   |
| `silent_mode='prepare'/'commit'` | "phase-specific omission"                    |
| `delay_distribution='lognormal'` | "long-tail delay attack"                     |

---

## Implementation Reminders for Downstream Phases

### Phase 5 — Feature extractor and the stale-replay round_id quirk

When a Phase 4c.1 stale-replay is emitted, the replayed copy keeps its
ORIGINAL `round_id` (this is the whole point — it lets the message
land in `prepare_log[old_round_id]` and stay isolated from the current
quorum under `STRICT_ROUND_VALIDATION=True`).

Side effect inside `SimPyNetwork._deliver`: the delivery counter is
incremented at `round_stats[msg.round_id]['delivered']` — i.e. using
the SELF-REPORTED round_id. For a stale copy, that means the
`delivered` increment lands in the OLD round bucket, not the round
that's currently executing.

**Implication for Phase 5 feature extraction:** do NOT compute
per-round network activity (e.g. `message_latency`,
`propagation_pattern`, `message_drop_rate`) purely from
`round_stats[current_round_id]` — the stale activity will be
under-counted. Prefer filtering `_network.message_log` by `send_time`
falling inside the current round's wall-clock window.

This is a design feature, not a bug. The asymmetry between
"messages tagged round R" and "messages active during round R" is
exactly what `stale_replayed` measures.

### Phase 11.D — Strict-round-validation ablation

`config.STRICT_ROUND_VALIDATION` currently has no code path that
reads it (other than being recorded in each round result for dataset
metadata). This is intentional:

- True (default) requires no protocol-side code — natural per-round
  log isolation does the job.
- False is reserved for the Phase 11.D ablation experiment, where
  `Node.receive` would need to rewrite incoming `msg.round_id` to the
  current round before depositing into `prepare_log` / `commit_log`.

Do not implement the False branch as part of Phase 4c. The data
column already exists in every row, so Phase 11 can simply flip the
constant and re-run the dataset generator to produce the ablation
arm.

### Phase 7 — Per-round network seed diversity

`run_pbft_simulation` currently passes the same `seed` to every
`run_pbft_round` call, so every round shares an identical
`SimPyNetwork` RNG trajectory (latency samples, drop decisions).
The injector RNG is persistent and varies across rounds, so attack
behaviour does differ, but per-round network noise will look
artificially uniform.

Recommended fix before Phase 7 full-run: pass `seed=seed + i` in the
multi-round loop so each round has an independent network-level
random stream, while the overall simulation remains deterministic
given a single external `seed`.

---

## Papers to Track Down Later (Not Needed Now)

From Mastromauro et al. (2025) Table 4, PBFT row, Replay column:
[181], [182], [195], [197], [133]. Read 1–2 of these only if Phase 11
ablation requires deeper defence-mechanism analysis.

## Papers Rejected as Irrelevant

- *Connected Car Communication by DLT Technologies* (Samuel 2023,
  Université Côte d'Azur PhD): vehicular networks + CUBA consensus
  design. Distant from message-level Byzantine modelling.
- *Collective Consciousness Emergence in Multi-Agent AI Systems*
  (Academia.edu, no peer review): terminology collision only — the
  "replay buffer" there is the RL experience-replay buffer, unrelated
  to network message replay. Likely an LLM-hallucinated suggestion.

---

## Bibliographic Entries (Harvard style, ready for the references list)

Mastromauro, L., Andrade, D.S., Ozmen, M.O. and Kinsy, M.A., 2025.
Survey of Attacks and Defenses on Consensus Algorithms for Secure
Data Replication in Distributed Systems. *IEEE Access*, 13,
pp.143631–143667.

Rocha, R.M.A., 2024. *ByzPlug: Reliability Testing of BFT Systems*.
MSc dissertation, Instituto Superior Técnico, Universidade de Lisboa.
