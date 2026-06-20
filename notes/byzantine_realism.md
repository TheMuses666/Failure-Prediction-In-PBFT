# Byzantine Realism Notes

Self-assessment of how faithfully our simulator's Byzantine fault model
reflects real-world Byzantine behavior. Drafted for direct re-use in the
dissertation's Discussion / Limitations sections.

Scope: covers the 5 fault classes implemented (or planned) in Phase 4 —
`silent`, `delay`, `replay`, `equivocation`, `forgery`.

---

## 1. Fidelity Verdict (per fault class)

| Class         | Real-world analog                              | Our implementation                  | Fidelity |
| ------------- | ---------------------------------------------- | ----------------------------------- | -------- |
| silent        | Node crash, partition, firewall, process death | Probabilistic message drop          | High     |
| delay         | Congestion, geo-distance, GC pause             | Fixed extra latency (300 ms)        | Medium   |
| replay        | Cross-round vote reuse / DoS flood             | Same-round duplicate emission       | Low–Mid  |
| equivocation  | Double-voting, conflicting proposals           | Receiver-parity content fork        | Medium   |
| forgery       | No-authentication failure mode                 | Random honest sender_id spoofing    | Medium   |

Mechanism is faithful in every class; sophistication is simplified across
the board.

---

## 2. Deliberate Simplifications

Seven dimensions where our adversary is weaker than a realistic one.
Each is followed by a one-line citation suggestion for the dissertation.

### 2.1 Static, not adaptive
Real attackers adjust strategy based on observed protocol state (e.g.,
ramp up during view-change). Ours commit to a single fault type for the
whole round.

> *Cite:* csienslab/BFT-Simulator vmware-attacker subdirectory implements
> static and adaptive variants — we follow the static variant only.

### 2.2 No collusion between Byzantine nodes
Each Byzantine node acts independently from a shared `FaultInjector` rule,
not from coordinated adversarial state. Real coordinated adversaries are
strictly more powerful (e.g., partitioning the network into faction-aligned
quorum subsets).

> *Cite:* Castro & Liskov (1999) treat Byzantine nodes as a worst-case
> adversarial coalition; our independence assumption is a lower bound.

### 2.3 View-change attacks out of scope
The most disruptive class of timing attacks in PBFT (slow-primary,
forced-view-change loops) is not modeled. The `leader_change_frequency`
feature is retained for completeness but always evaluates to zero in
our experiments.

> *Cite:* Castro & Liskov (1999) §4; csienslab VMware adaptive attacker.

### 2.4 Uniform network model
Real deployments have heterogeneous latency (cross-continent vs.
same-datacenter), long-tail distributions (P99 >> mean), correlated
loss (link failures), and partition events. We use Gaussian(20, 10) ms
with independent 2% drop and no partition events.

> *Cite:* csienslab partitioner.js models partition as a distinct
> topology event; we approximate via delay attack on Byzantine senders.

### 2.5 No economic / rational attacker model
Modern BFT systems on PoS layers introduce slashing penalties and
expected utility. Our adversary is malicious in the classical Byzantine
sense (arbitrary deviation), not rational (utility-maximizing).

### 2.6 No cryptographic layer
sender_id is a plain field, with no MAC vector or signature verification.
This is the precondition that lets `forgery` exist as a valid attack
class — we declare it as an authentication-ablation scenario rather than
an attack against authenticated PBFT.

> *Cite:* Castro & Liskov (1999) §4.1 (authenticator construction);
> Talaria uses a similar no-crypto simplification.

### 2.7 No content-aware censorship
Real adversaries may selectively drop messages based on payload semantics
(e.g., transactions involving a particular account). Our silent attack
drops uniformly without inspecting `msg.content`.

---

## 3. What We Got Right

Counterweight: the simulator gets several methodological choices correct
that many academic prototypes do not.

### 3.1 Discrete-event simulation, not wall-clock
SimPy advances simulated time via `env.timeout(...)`; no `time.sleep()`.
Causality between message emission, network delay, drop, and quorum
detection is preserved. Matches the methodology of Talaria (SciPy event
simulation) and csienslab (JS event loop).

### 3.2 Quorum and safety behavior is correct
Each fault class produces the consensus outcome predicted by PBFT theory
(silent stays committable up to f, equivocation can split quorum, etc.).
Phase 4 end-to-end smoke tests verified this and incidentally surfaced a
Phase 3 quorum-counting bug (primary not participating in prepare),
which we fixed by mirroring csienslab's `pbft.js` design.

### 3.3 Mechanism-level fault injection
Faults operate on real `Message` events through a single `FaultInjector`
hook (`on_send`, `extra_latency`). We do not patch outcomes — we patch
the message-flow mechanism, so downstream features (`message_log`,
`round_stats`) are causally consistent with the attack.

### 3.4 Strict reproducibility
All randomness is funneled through `self.rng = random.Random(seed)`.
A fixed seed makes every run bit-identical, satisfying the reproducibility
requirement for published experiments.

### 3.5 Taxonomy unifies prior simulators
Our 5 fault classes cover the union of csienslab (silent + delay) and
Talaria (silent + equivocation) attack sets, and add two not present
in either (replay as DoS-form, forgery as auth-ablation).

---

## 4. Boilerplate Paragraphs for the Dissertation

Drop-in text for the Limitations section. Lightly edit to fit the surrounding
prose.

### 4.1 Adversary model framing
> Our Byzantine fault model captures the mechanism of five canonical attack
> classes (silent, delay, replay, equivocation, forgery) with
> mechanism-level fidelity: each attack operates on real message events
> through the same `FaultInjector` interface used in csienslab/BFT-Simulator
> (Lin et al., 2023). However, we deliberately simplify the adversary in
> three dimensions: (a) attackers are static rather than adaptive,
> (b) Byzantine nodes act independently rather than colluding, and (c)
> view-change attacks are out of scope. These simplifications follow standard
> practice in BFT simulators (Talaria — Xing et al., 2021; csienslab —
> Lin et al., 2023) and establish a controlled lower bound on attack
> sophistication. A monitor that performs well on this baseline does not
> guarantee performance against adaptive or coordinated adversaries, which
> we identify as future work.

### 4.2 Replay limitation
> Our replay implementation captures the bandwidth-amplification aspect of
> replay attacks. Modeling the cross-round vote-fabrication aspect would
> require multi-round state and a protocol variant that does not strictly
> filter messages by round_id, neither of which is present in our PBFT
> implementation. Even in this simplified form, replay provides a useful
> training signal: it is the only fault class in our taxonomy where
> consensus completes successfully while message volume diverges
> significantly from baseline.

### 4.3 Forgery as authentication ablation
> Forgery is included as a controlled authentication-ablation scenario
> rather than a claim about authenticated PBFT. Production PBFT
> deployments use MAC vectors or digital signatures (Castro & Liskov, 1999)
> that defeat sender-identity spoofing. Our forgery results characterize
> what consensus telemetry looks like when authentication is absent —
> informing the design of monitoring layers that can serve as a
> defense-in-depth complement to cryptographic authentication, rather
> than as a replacement for it.

### 4.4 Network model
> The network layer uses a single Gaussian latency distribution and
> independent uniform drop, in contrast to the heterogeneous,
> long-tailed, correlated-loss characteristics of production deployments.
> Network partition events, modeled as a distinct topology change in
> csienslab/BFT-Simulator's partitioner module, are approximated in our
> work as a delay attack on selected nodes. Extending to richer network
> topologies is left to future work.

---

## 5. Where This Sits Methodologically

The standard playbook for ML-for-systems research is:

1. Train and evaluate in a controlled simulator.
2. Report performance bounded by the simulator's assumptions.
3. Declare the gap to production honestly.
4. Frame real-world deployment as future work.

Our project follows this playbook. The thesis under test is not
*"this monitor works in production"* but *"ML can extract Byzantine
signal from consensus telemetry."* Simulation simplification is a
**methodological prerequisite for causal isolation of the ML
contribution**, not a defect of the approach.

This framing is stronger than claiming high realism — it makes the
limitations a feature of the methodology, not a weakness.

---

## 6. References to Cite

- Castro, M., & Liskov, B. (1999). *Practical Byzantine Fault Tolerance.*
  OSDI '99. (PBFT spec, authenticator construction, view-change attacks.)
- Xing, J., et al. (2021). *Talaria: A Framework for Simulation of
  Permissioned Blockchains for Logistics and Beyond.* arXiv:2103.02260.
  (Byzantine Type 1 / 2 model; SciPy event simulation.)
- Lin et al. *BFT-Simulator.* GitHub: csienslab/BFT-Simulator.
  (`attacker/fail-stop.js`, `partitioner.js`, `vmware-attacker/`;
  `ba-algo/pbft.js` for the primary-also-broadcasts-prepare pattern.)
- Cristian, F. (1991). *Understanding fault-tolerant distributed systems.*
  Communications of the ACM. (Classical fault taxonomy: omission /
  timing / Byzantine.)
