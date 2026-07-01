# Castro & Liskov (1999) — Practical Byzantine Fault Tolerance

## Citation
Castro, M. and Liskov, B. (1999) 'Practical Byzantine fault
tolerance', in Proceedings of the Third Symposium on Operating
Systems Design and Implementation (OSDI '99). New Orleans, LA:
USENIX Association, pp. 173-186.

PDF used: `2.Castro_PBFT_attempt1.pdf` (Ghostscript-recovered, 14 pages).

## What it is (one sentence)
The seminal OSDI'99 paper that introduced PBFT — the first state-
machine replication protocol that tolerates up to f Byzantine
replicas out of n = 3f + 1 in asynchronous networks with practical
throughput (only 3% slower than unreplicated NFS).

## Why we cite it (one sentence)
PBFT *is* the protocol our simulator implements. Every design
decision in [src/simulation/pbft.py](../src/simulation/pbft.py) and
[config.py](../config.py) traces back to a specific construct in
this paper, and three of our most defensible methodology choices
(n=7 / f=2, forgery as authentication-ablation, view-change scoped
out) are framed against direct quotes from this paper.

---

## Key takeaways for our dissertation

### Takeaway 1 — Optimal resiliency 3f + 1 (§3, p. 2)

This is **the single most important fact** for justifying our `n = 7,
f = 2` choice. Direct quote:

> "The resiliency of our algorithm is optimal: 3f + 1 is the minimum
> number of replicas that allow an asynchronous system to provide the
> safety and liveness properties when up to f replicas may be faulty
> [2]. This many replicas are needed because it must be possible to
> proceed after communicating with n − f replicas, since f replicas
> might be faulty and not responding. However, it is possible that
> the f replicas that did not respond are not faulty and, therefore,
> f of those that responded might be faulty. Even so, there must
> still be enough responses that those from non-faulty replicas
> outnumber those from faulty ones, i.e., n − 2f > f. Therefore
> n > 3f." (Castro & Liskov 1999, §3, p. 2)

Implication for us: setting `n = 7, f = 2` gives `n − 2f = 3 > f = 2`
and quorum size = `2f + 1 = 5`. This is the smallest non-trivial
PBFT configuration — citing this paragraph directly justifies the
choice as "minimal but optimal", not arbitrary.

### Takeaway 2 — Safety vs Liveness with async safety / sync liveness (§3, p. 2)

Direct quote (three crucial sentences in a row):

> "The algorithm provides both safety and liveness assuming no more
> than ⌊(n−1)/3⌋ replicas are faulty. Safety means that the
> replicated service satisfies linearizability [14] (modified to
> account for Byzantine-faulty clients [4]): it behaves like a
> centralized implementation that executes operations atomically one
> at a time." (Castro & Liskov 1999, §3, p. 2)

> "The algorithm does not rely on synchrony to provide safety.
> Therefore, it must rely on synchrony to provide liveness;
> otherwise it could be used to implement consensus in an
> asynchronous system, which is not possible [9]." (Castro & Liskov
> 1999, §3, p. 2)

Implication for us: this is the **canonical separation** that maps
exactly onto our label scheme:

| Castro & Liskov term | Our label |
| -------------------- | --------- |
| Safety violation (disagreement on sequence number) | **Failure (label 2)** |
| Liveness violation (timeout, no quorum) | **Failure (label 2)** |
| Both properties hold but performance degraded | **Degraded (label 1)** |
| Both properties hold, fast | **Normal (label 0)** |

We can cite this paragraph as the theoretical backbone of why
"Failure" collapses both safety violations and liveness violations
into a single label class.

### Takeaway 3 — Three-phase protocol: pre-prepare → prepare → commit (§4.2, p. 4)

This is the **exact source code** of our [src/simulation/pbft.py](../src/simulation/pbft.py).
Direct quote:

> "The three phases are pre-prepare, prepare, and commit. The
> pre-prepare and prepare phases are used to totally order requests
> sent in the same view even when the primary, which proposes the
> ordering of requests, is faulty. The prepare and commit phases are
> used to ensure that requests that commit are totally ordered
> across views." (Castro & Liskov 1999, §4.2, p. 4)

And the quorum-counting predicate:

> "We define the predicate prepared(m, v, n, i) to be true if and
> only if replica i has inserted in its log: the request m, a
> pre-prepare for m in view v with sequence number n, and 2f
> prepares from different backups that match the pre-prepare."
> (Castro & Liskov 1999, §4.2, p. 4)

> "committed-local(m, v, n, i) is true if and only if prepared(m, v,
> n, i) is true and i has accepted 2f + 1 commits (possibly
> including its own) from different replicas that match the
> pre-prepare for m." (Castro & Liskov 1999, §4.2, p. 5)

Mapping to our code:

| PBFT quorum (paper) | Our code | f=2 yields |
| ------------------- | -------- | ---------- |
| `2f` prepares to enter committed phase | `prepare_log[round_id][content]` size check | 4 prepares |
| `2f + 1` commits to commit-local | `commit_log[round_id][content]` size check | 5 commits (the **commit quorum**) |
| `f + 1` matching replies at client side | our simplified reply phase | 3 replies |

### Takeaway 4 — Authenticated messages assumption (§2, p. 2)

**This is the key citation for framing our `forgery` fault as an
authentication-ablation experiment**, not as a "PBFT broken" claim.
Direct quote:

> "We use cryptographic techniques to prevent spoofing and replays
> and to detect corrupted messages. Our messages contain public-key
> signatures [33], message authentication codes [36], and message
> digests produced by collision-resistant hash functions [32]. We
> denote a message m signed by node i as ⟨m⟩σi and the digest of
> message m by D(m)." (Castro & Liskov 1999, §2, p. 2)

> "All replicas know the others' public keys to verify signatures."
> (Castro & Liskov 1999, §2, p. 2)

> "We allow for a very strong adversary that can coordinate faulty
> nodes, delay communication, or delay correct nodes in order to
> cause the most damage to the replicated service. ... We also
> assume that the adversary (and the faulty nodes it controls) are
> computationally bound so that (with very high probability) it is
> unable to subvert the cryptographic techniques mentioned above.
> For example, the adversary cannot produce a valid signature of a
> non-faulty node, compute the information summarized by a digest,
> or find two messages with the same digest." (Castro & Liskov 1999,
> §2, p. 2)

Implication for us: PBFT **explicitly assumes** the adversary cannot
forge sender identities. Our `forgery` fault deliberately relaxes
this assumption. Our framing in the dissertation:

> "Castro & Liskov (1999, §2) explicitly require that 'all replicas
> know the others' public keys to verify signatures', and that the
> bounded adversary 'cannot produce a valid signature of a
> non-faulty node'. Our `forgery` fault is an authentication-
> ablation experiment that deliberately removes this assumption to
> study how unverified sender identities propagate through the
> three-phase protocol, not a critique of PBFT under its stated
> threat model."

### Takeaway 5 — View change as the liveness recovery mechanism (§4.4, p. 5)

This is **the citation that scopes view-change out of our project**.
Direct quote:

> "The view-change protocol provides liveness by allowing the system
> to make progress when the primary fails. View changes are triggered
> by timeouts that prevent backups from waiting indefinitely for
> requests to execute. A backup is waiting for a request if it
> received a valid request and has not executed it. A backup starts
> a timer when it receives a request and the timer is not already
> running. It stops the timer when it is no longer waiting to execute
> the request, but restarts it if at that point it is waiting to
> execute some other request." (Castro & Liskov 1999, §4.4, p. 5)

And the new-view machinery (§4.4 cont., p. 5-6):
> "When the primary p of view v + 1 receives 2f valid view-change
> messages for view v + 1 from other replicas, it multicasts a
> ⟨NEW-VIEW, v + 1, n, V, O⟩σp message to all other replicas,
> where V is a set containing the valid view-change messages received
> by the primary plus the view-change message for v + 1 the primary
> sent (or would have sent), and O is a set of pre-prepare messages
> (without the piggybacked request)." (Castro & Liskov 1999, §4.4)

Implication for us: implementing view-change correctly requires
new-view certificates + checkpoint state machinery, which is a
multi-week subproject. We:
1. Do **not** implement view-change in the simulator
2. Keep `leader_change_frequency` as a feature recorded as `0`
   throughout (placeholder)
3. Frame this scope cut by directly citing §4.4's machinery as
   evidence of complexity

Our dissertation framing:

> "View-change machinery (Castro & Liskov 1999, §4.4) requires new-
> view certificate construction, exponential timer back-off, and
> persistent checkpoint state. We treat view-change as out of scope
> and record `leader_change_frequency = 0` throughout. Our timeout-
> driven label assignment captures the *symptom* of view-change
> conditions (no quorum reached within `CONSENSUS_TIMEOUT_MS`)
> without modelling the recovery mechanism itself."

### Takeaway 6 — Timeout-driven progress and exponential back-off (§4.5.2, p. 7)

Direct quote:

> "To provide liveness, replicas must move to a new view if they
> are unable to execute a request. But it is important to maximize
> the period of time when at least 2f + 1 non-faulty replicas are
> in the same view, and to ensure that this period of time increases
> exponentially until some requested operation executes."
> (Castro & Liskov 1999, §4.5.2, p. 7)

> "First, to avoid starting a view change too soon, a replica that
> multicasts a view-change message for view v + 1 waits for 2f + 1
> view-change messages for view v + 1 and then starts its timer to
> expire after some time T. If the timer expires before it receives
> a valid new-view message or before it executes a request that it
> had not executed previously, it starts the view change for view
> v + 2 but this time it will wait 2T before starting a view change
> for v + 3." (Castro & Liskov 1999, §4.5.2, p. 7)

Implication for us: our `CONSENSUS_TIMEOUT_MS` config and
`timeout_frequency` feature implement the simplified version of this
mechanism — a single timeout that, when exceeded, marks the round as
Failure. We deliberately do not model the exponential T → 2T → 4T
back-off because we do not run multi-view recovery.

### Takeaway 7 — Performance optimisations (§5) — what we deliberately skip

Two optimisations in §5 are notable for scope clarity:

> "MACs can be computed three orders of magnitude faster than digital
> signatures." (Castro & Liskov 1999, §5.2, p. 8)

> "The size of authenticators grows linearly with the number of
> replicas." (Castro & Liskov 1999, §5.2, p. 8)

Implication for us: §5 describes message-authentication-code (MAC)
optimisations that replace digital signatures for everything except
view-change messages. **We do not model any of this at the bit/byte
level** — our simulator treats messages as abstract events with
sender_id, content, and round_id fields. This is a *deliberate
abstraction* because our research question is detection of Byzantine
*behaviours*, not cryptographic *throughput*.

Acknowledge this in the Methodology chapter:

> "Castro & Liskov (1999, §5) detail message-authentication-code
> optimisations that reduce signature-verification overhead by three
> orders of magnitude. Our simulator abstracts away the cryptographic
> layer because the research question concerns detection of
> Byzantine behaviour at the consensus-protocol level, not the
> performance of the underlying authentication scheme."

---

## Mapping to our project (consolidated)

| PBFT construct (paper section, page) | Our implementation |
| ------------------------------------ | ------------------ |
| **n = 3f + 1 optimal** (§3, p. 2) | `NUM_NODES = 7`, `FAULT_TOLERANCE = 2` in [config.py](../config.py) |
| **Commit quorum = 2f + 1** (§4.2, p. 5) | quorum check in [src/simulation/node.py](../src/simulation/node.py); equals 5 for f=2 |
| **Prepare quorum = 2f** (§4.2, p. 4) | `prepare_log[round_id][content]` size check; equals 4 for f=2 |
| **Pre-prepare broadcast by primary** (§4.2, p. 4) | [src/simulation/pbft.py](../src/simulation/pbft.py) `pre_prepare` phase |
| **Prepare broadcast** (§4.2, p. 4) | [src/simulation/pbft.py](../src/simulation/pbft.py) `prepare` phase |
| **Commit broadcast** (§4.2, p. 5) | [src/simulation/pbft.py](../src/simulation/pbft.py) `commit` phase |
| **Client waits for f + 1 replies** (§4, p. 3) | simplified reply phase |
| **View change** (§4.4, p. 5) | **NOT IMPLEMENTED**; `leader_change_frequency = 0` placeholder |
| **Authenticated messages** (§2, p. 2) | **NOT enforced** in code; basis for our `forgery` fault as authentication-ablation |
| **Timeout-driven progress** (§4.4 / §4.5.2, p. 5/7) | `CONSENSUS_TIMEOUT_MS` constant + `timeout_frequency` feature; **no exponential back-off** |
| **Safety vs liveness separation** (§3, p. 2) | Failure label conflates both; Degraded label captures soft violations |
| **MAC optimisations** (§5, p. 8) | **NOT MODELLED** — simulator abstracts away cryptography |

---

## Suggested citation patterns for the dissertation

### For Chapter 2 Background / §2.1 Protocol summary (3 sentences)
> "PBFT (Castro & Liskov 1999) was the first state-machine replication
> algorithm to tolerate Byzantine faults with practical throughput in
> asynchronous networks. It uses a three-phase agreement protocol —
> pre-prepare, prepare, and commit — among `n = 3f + 1` replicas to
> reach consensus despite at most f Byzantine failures (Castro &
> Liskov 1999, §4.2, p. 4). Safety is guaranteed regardless of network
> timing; liveness requires partial synchrony (Castro & Liskov 1999,
> §3, p. 2)."

### For justifying our n = 7, f = 2 choice
> "We instantiate the simulator with n = 7 replicas and a Byzantine
> tolerance bound of f = 2. This is the smallest non-trivial PBFT
> configuration — Castro & Liskov (1999, §3, p. 2) show that
> n = 3f + 1 is the optimal resiliency bound, requiring n − 2f > f.
> For f = 2 this yields n > 6, and n = 7 is the tightest choice.
> The resulting commit quorum is 2f + 1 = 5."

### For framing the forgery fault as authentication ablation
> "Castro & Liskov (1999, §2, p. 2) require that 'all replicas know
> the others' public keys to verify signatures' and that the bounded
> adversary 'cannot produce a valid signature of a non-faulty node'.
> Our `forgery` fault deliberately removes this assumption: a
> Byzantine node sends a valid-looking prepare or commit message
> using a forged honest `sender_id`. This is an authentication-
> ablation experiment intended to characterise how unverified
> identities propagate through the three-phase protocol, not a claim
> that PBFT under its stated threat model is vulnerable to this
> attack."

### For scoping view-change out of the project
> "View-change (Castro & Liskov 1999, §4.4) is PBFT's recovery
> mechanism when the primary is suspected faulty. Correct
> implementation requires new-view certificate construction,
> exponential timer back-off, and persistent checkpoint state, all
> of which fall outside the scope of this dissertation. We record
> `leader_change_frequency = 0` throughout the dataset as a documented
> placeholder; our timeout-driven Failure label captures the symptom
> ('no quorum reached within `CONSENSUS_TIMEOUT_MS`') without
> modelling the underlying recovery protocol."

### For label-schema theoretical backing
> "Our three-class label scheme separates two distinct failure modes
> identified by Castro & Liskov (1999, §3, p. 2): safety violation
> (non-faulty replicas disagree on sequence number) and liveness
> violation (no quorum reached within the timeout). Both collapse to
> the Failure class. The Degraded class captures runs where both
> safety and liveness properties hold but a soft performance target
> is exceeded, mirroring the Service Level Objective vocabulary of
> Beyer et al. (2016, ch. 6) used elsewhere in our methodology."

---

## Cross-references to existing notes

- [key_papers.md §1, §2, §3, §4](key_papers.md) — Castro & Liskov is
  primary citation for: three-phase protocol, n=3f+1, quorum sizing,
  view-change scope, label rules, forgery framing (6 distinct rows
  cite this paper)
- [byzantine_realism.md](byzantine_realism.md) — discusses fidelity
  of our simulator's Byzantine model against the paper's adversary
- [literature_review.md §1.1, §1.2, §3.3](literature_review.md) —
  Castro & Liskov is the foundational PBFT citation, used 3 times in
  the review
- [phase4c_literature.md](phase4c_literature.md) — extends the
  authentication-ablation framing for the forgery fault

---

## Pages I actually read
- Pages 1-10 of the 14-page paper (Ghostscript-recovered PDF):
  - §1 Introduction
  - §2 System Model
  - §3 Service Properties
  - §4 The Algorithm in full (§4.1 The Client, §4.2 Normal-Case
    Operation, §4.3 Garbage Collection, §4.4 View Changes, §4.5
    Correctness, §4.5.2 Liveness, §4.6 Non-Determinism)
  - §5 Optimizations (sub-§5.1, §5.2)
  - §6 Implementation overview (BFS file system context)

## Pages I deliberately did not read
- Pages 11-14:
  - §6.3, §6.4 Maintaining Checkpoints / Computing Digests —
    BFS-specific implementation details, not transferable
  - §7 Performance Evaluation — NFS benchmark results; our
    simulator does not target NFS workloads
  - §8 Related Work — covered by [literature_review.md §1](literature_review.md) and Mastromauro et al. (2025)
  - §9 Conclusions — standard end-of-paper summary

## Open questions / things to verify before submission

1. **Page numbers**: the PDF used was generated by Ghostscript from a
   damaged .ps file. Internal page numbers (1-14) appear correct but
   should be cross-checked against the official OSDI '99 proceedings
   pagination (pp. 173-186). If the dissertation uses the proceedings
   page range, add an offset of 172 when citing (e.g. our §3, p. 2
   becomes "p. 174" in proceedings pagination).
2. **Optional: also cite the 2002 journal extension**: Castro &
   Liskov (2002) 'Practical Byzantine fault tolerance and proactive
   recovery', *ACM TOCS* 20(4), pp. 398-461. This is the longer
   journal version with full proofs. Decide whether the dissertation
   wants to cite both versions or just the 1999 conference paper. If
   both, add the 2002 entry to [literature_review.md §7](literature_review.md)
   References list.
3. **Verify `2f` vs `2f + 1` distinction**: the paper distinguishes
   "2f prepares from different backups" (note: backups, not all
   replicas) and "2f + 1 commits". Make sure our code's quorum
   checks match this exactly. Particularly: prepare counts the
   sender's own pre-prepare implicitly, so the effective prepare
   quorum threshold is `2f + 1` when including the primary's
   pre-prepare as a prepare-equivalent.
