# SimPy-Based Project Milestones

## ML-Assisted Predictive Monitoring in Byzantine Fault-Tolerant Consensus Protocols

**Goal:** Rebuild the simulator as a high-quality discrete-event PBFT simulation using SimPy.

This plan replaces the lightweight loop-based simulator with a SimPy-first design. The objective is to model PBFT message delivery, Byzantine delay, timeout, and phase completion using simulated time rather than real blocking delays such as `time.sleep()`.

---

## Overview

```text
Phase 0  -> Architecture reset
Phase 1  -> SimPy network foundation
Phase 2  -> Event-driven node replica
Phase 3  -> PBFT protocol orchestration
Phase 4  -> Byzantine fault injection
Phase 4b -> Advanced fault injection: forgery
Phase 4c -> Byzantine behaviour realism upgrade
Phase 5  -> High-quality metrics and feature extraction
Phase 6  -> Label generation upgrade
Phase 7  -> Full dataset generation
Phase 8  -> Simulator validation before ML
Phase 9  -> ML pipeline
Phase 10 -> Baseline comparison
Phase 11 -> Rigorous training (CV + tuning + multi-seed)
Phase 11b -> Lightweight model baseline (Logistic Regression)
Phase 12 -> Research-quality experiments
Phase 12.E -> Optional mixed-N training
Phase 13 -> Future work: graph neural network monitor
Phase 14 -> Future work: temporal BiLSTM monitor
Phase 15 -> Lightweight results dashboard
```

---

## Reference Framework Map

Use these projects as references only. The final simulator should remain a custom SimPy-based PBFT simulator tailored to this research question.

| Reference        | Use For                                                                                                | Do Not Use For                                                                            |
| ---------------- | ------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------- |
| SimPy            | Discrete-event simulation, simulated time, message delay, timeout events, event scheduling             | PBFT logic directly, because SimPy is a generic simulation framework                      |
| Talaria          | Permissioned blockchain simulation design, pBFT-style simulation framing, methodology comparison       | Direct implementation dependency, unless its logging model matches this project           |
| ByzFL            | Configurable Byzantine attack experiments, robustness benchmark structure, adversarial scenario design | PBFT consensus implementation, because it focuses on federated learning                   |
| ai-bft-consensus | ML + consensus proof-of-concept ideas, node scoring or leader-related feature inspiration              | Main simulator architecture, unless its code is verified and aligned with PBFT monitoring |

---

## Phase 0 — Architecture Reset

**Goal:** Define the new simulator architecture before implementation.

**References:** SimPy for simulator architecture; Talaria for permissioned blockchain simulation framing.

### Keep

- [x] `config.py`
- [x] `requirements.txt`
- [x] `collection/label_generator.py` concept
- [x] `ml/`
- [x] `baseline/`
- [x] `experiments/`
- [x] `visualization/`

### Rewrite or Heavily Refactor

- [ ] `simulation/node.py`
- [ ] `simulation/network.py`
- [ ] `simulation/pbft.py`
- [ ] `simulation/fault_injector.py`
- [ ] `collection/feature_extractor.py`
- [ ] `main.py`

### Add

- [x] `simulation/message.py`
- [x] `simulation/simpy_network.py`
- [x] `simulation/round_result.py`

**Deliverable:** Clear file-level architecture for the SimPy simulator.

---

## Phase 1 — SimPy Environment Foundation

**Files:**

```text
simulation/message.py
simulation/simpy_network.py
```

**Goal:** Build the discrete-event message delivery layer.

**Primary reference:** SimPy.

**Reference focus:**

- simulated time with `env.now`
- event scheduling with `env.timeout(...)`
- process-based message delivery
- avoiding real blocking delays

### Requirements

- [x] Use `simpy.Environment`
- [x] Use `env.now` as simulated time
- [x] Do not use `time.sleep()`
- [x] Implement message delivery through scheduled events
- [x] Track sent, delivered, dropped, delayed, replayed, and equivocated messages

### `Message` Fields

- [x] `message_id`
- [x] `message_type`
- [x] `sender_id`
- [x] `receiver_id`
- [x] `round_id`
- [x] `content`
- [x] `send_time`
- [x] `delivery_time`
- [x] `fault_type`
- [x] `is_corrupt`

### `SimPyNetwork` Responsibilities

- [x] `send_message()`
- [x] `broadcast()`
- [x] latency sampling
- [x] message drop simulation
- [x] message delivery log
- [x] per-round message statistics

### Smoke Test

```bash
.venv/bin/python -c "import simpy; from src.simulation.message import Message; from src.simulation.simpy_network import SimPyNetwork; env=simpy.Environment(); net=SimPyNetwork(env); print(env.now)"
```

### Pass Criteria

- [x] One message can be scheduled and delivered at simulated time.
- [x] Delivery time is based on `env.now`, not wall-clock time.

**Deliverable:** Working SimPy message delivery layer.

---

## Phase 2 — Event-Driven Node Replica

**File:**

```text
simulation/node.py
```

**Goal:** Model each PBFT replica as an event-driven participant.

**Primary reference:** SimPy.

**Secondary reference:** ai-bft-consensus, only for high-level ideas about node behaviour scoring or ML-aware consensus monitoring.

### Node State

- [x] `node_id`
- [x] `is_byzantine`
- [x] `fault_type`
- [x] `received_messages`
- [x] `prepare_log`
- [x] `commit_log`
- [x] `phase_times`
- [x] `committed_rounds`
- [x] `first_response_time`

### Behaviour

- [x] receive `pre_prepare`
- [x] receive `prepare`
- [x] receive `commit`
- [x] record message arrival time
- [x] record phase entry time
- [x] detect prepare quorum
- [x] detect commit quorum
- [x] mark round committed

### Smoke Test

```bash
.venv/bin/python -c "from src.simulation.node import Node; print(Node.__name__)"
```

### Pass Criteria

- [x] Node can receive messages.
- [x] Node can count prepare and commit messages per round.
- [x] Node can detect quorum for a round.

**Deliverable:** Event-driven PBFT replica state model.

---

## Phase 3 — PBFT Protocol Orchestration

**File:**

```text
simulation/pbft.py
```

**Goal:** Implement a SimPy-orchestrated PBFT round.

**Primary reference:** PBFT literature and the existing project design.

**Secondary reference:** Talaria, only for how permissioned blockchain simulators frame pBFT-style consensus rounds.

### Required Phases

- [x] client request
- [x] pre-prepare broadcast by primary
- [x] prepare broadcast after receiving pre-prepare
- [x] commit broadcast after prepare quorum
- [x] simplified reply phase after commit quorum
- [x] timeout event

### Normal Round Smoke Test

```bash
.venv/bin/python -c "from src.simulation.pbft import run_pbft_round; print(run_pbft_round(round_id=1, fault_type='normal'))"
```

### Pass Criteria

- [x] Normal round succeeds with 7 nodes and 0 Byzantine nodes.
- [x] Commit quorum is reached.
- [x] Round duration is below `CONSENSUS_TIMEOUT_MS`.
- [x] Honest nodes commit consistently.

**Deliverable:** One successful normal PBFT round using SimPy time.

---

## Phase 4 — Byzantine Fault Injection

**File:**

```text
simulation/fault_injector.py
```

**Goal:** Implement controlled Byzantine behaviours as event-level effects.

**Primary reference:** ByzFL for configurable attack experiment structure.

**Secondary reference:** Talaria for malicious authority simulation in permissioned blockchain settings.

### Fault Types

- [x] `silent`: Byzantine node does not send selected messages.
- [x] `delay`: Byzantine messages receive additional simulated latency.
- [x] `replay`: Byzantine node resends old messages.
- [x] `equivocation`: Byzantine node sends different content to different receivers.

### Configuration

- [x] `fault_type`
- [x] `fault_ratio`
- [x] `fault_intensity`
- [x] `byzantine_node_ids`
- [x] `random_seed`

### Smoke Tests

```text
silent        -> delivered_messages < expected_messages
delay         -> average latency increases
replay        -> replayed_message_count > 0
equivocation  -> message_consistency decreases
```

### Pass Criteria

- [x] Each fault type produces distinguishable metrics.
- [x] Fault behaviour is deterministic under fixed random seed.

**Deliverable:** Four controllable Byzantine fault behaviours.

---

## Phase 4b — Advanced Fault Injection: Forgery

**Goal:** Add an optional authentication-ablation fault where Byzantine nodes spoof sender identities.

This does not replace `replay`. It is an additional advanced scenario that models what can happen when a simulator or protocol variant trusts `sender_id` as a plain field without cryptographic signature or authenticated-channel verification.

Mechanism: `prepare_log[round_id][content]` and `commit_log[round_id][content]` are `set[int]` structures keyed by `sender_id`. A replayed message with the same `sender_id` is silently deduplicated, but a forged message claiming a fresh honest `sender_id` adds a new element to the quorum set. This is why forgery can alter quorum behaviour while simple replay mainly increases message volume.

**Primary reference:** PBFT authentication assumptions and this project's BFT simulator design.

**Secondary reference:** csienslab/BFT-Simulator for adversarial message manipulation structure.

### Fault Type

- [x] `forgery` / `sender_spoofing`: Byzantine node sends a valid-looking prepare or commit message using a forged honest `sender_id`.

### Requirements

- [x] Implement `_on_forgery()` in `simulation/fault_injector.py`
- [x] Select forged `sender_id` from honest node IDs, not Byzantine node IDs
- [x] Forged `sender_id` must differ from the original `msg.sender_id`
- [x] Mark forged messages with `is_corrupt=True`
- [x] Mark forged messages with `fault_type='forgery'`
- [x] Implementation pattern: emit both messages — `return [msg, forged]`
- [x] The original message preserves the Byzantine node's own vote
- [x] The forged copy is the attack payload and steals a fresh honest identity
- [x] `fault_intensity` controls the probability that a Byzantine send produces a forged copy
- [x] `fault_intensity=1.0` means every Byzantine send creates one forged copy
- [x] `fault_intensity=0.4` means roughly 40% of Byzantine sends create one forged copy
- [x] Add `forged` to `round_stats`, matching the existing past-tense naming style: `delivered`, `dropped`, `delayed`, `replayed`, `equivocated`
- [x] Verify forged sender IDs appear in `prepare_log` or `commit_log`
- [x] If no honest sender candidate exists, skip forgery and return `[msg]` as a graceful fallback
- [x] Document that this fault assumes no cryptographic signature verification

### Smoke Test

```text
forgery -> forged > 0
forgery -> message_log contains is_corrupt=True and fault_type='forgery'
forgery -> prepare_log or commit_log contains forged honest sender IDs
forgery -> quorum may be reached with fewer real honest votes than baseline
```

### Pass Criteria

- [x] Forgery produces distinguishable metrics.
- [x] Forged votes can affect quorum behaviour in the no-authentication setting.
- [x] The report clearly explains that real PBFT normally relies on authenticated messages, so forgery is an authentication-ablation scenario.

**Deliverable:** Optional advanced sender-spoofing fault for robustness analysis.

---

## Phase 4c — Byzantine Behaviour Realism Upgrade

**Goal:** Improve the realism of the existing `silent`, `delay`, and `replay` behaviours without expanding the project into execution-layer, view-change, or cryptographic simulation.

This phase refines message-level Byzantine behaviour. It does not replace the Phase 4 fault classes; it makes their behaviour less deterministic and more representative of operational distributed systems.

**Primary reference:** This project's SimPy message-event model.

**Secondary reference:** csienslab/BFT-Simulator for attacker behaviour design; ByzFL for configurable adversarial scenario parameters.

### 4c.1 Replay Upgrade

Current behaviour:

```text
same-round duplicate emission
```

Target behaviour:

- [x] Keep same-round duplicate replay as the baseline replay mode
- [x] Add optional stale-round replay mode
- [x] Store a small replay buffer of previously sent Byzantine messages
- [x] Replay a previous valid message with its old round metadata
- [x] Track same-round duplicates separately from stale-round replays
- [x] Ensure stale-round replay does not affect quorum unless a deliberate no-round-validation ablation is enabled

Prerequisite:

```text
Stale-round replay requires multi-round simulation. Preferred implementation:
run multiple consecutive rounds with a persistent FaultInjector and replay
buffer. Fallback for single-round smoke tests: seed the replay buffer during
FaultInjector construction with synthetic old messages.
```

Round-validation ablation:

```text
STRICT_ROUND_VALIDATION = True by default.

When enabled, stale messages keep their old round_id and are naturally isolated
in prepare_log[old_round_id] / commit_log[old_round_id].

Only an explicit ablation run may disable this validation. Setting
STRICT_ROUND_VALIDATION = False allows stale messages to be evaluated against
the current round's quorum logic, modeling an intentionally weakened protocol.
```

Suggested counters:

```text
replayed             = same_round_replayed + stale_replayed
same_round_replayed = same-round duplicate replay events
stale_replayed      = cross-round stale replay events
```

Smoke tests:

```text
replay_duplicate -> replayed > 0 and stale_replayed == 0
replay_stale -> stale_replayed > 0
replay_stale -> stale messages keep old round_id
```

### 4c.2 Delay Upgrade

Current behaviour:

```text
fixed extra delay, e.g. 300 ms
```

Target behaviour:

- [x] Make delay probabilistic using `delay_probability`
- [x] Add jitter to Byzantine delay
- [x] Sample additional delay from a configurable distribution
- [x] Support at least Gaussian delay jitter
- [x] Optionally support lognormal delay for long-tail latency experiments
- [x] Keep lognormal disabled by default for backward-compatible Phase 4 smoke tests

Parameter semantics:

```text
Deprecated Phase 4 form:
extra_delay_ms * fault_intensity

Phase 4c form:
delay_probability controls WHETHER a Byzantine message is delayed.
delay_mean_ms and delay_jitter_ms control HOW MUCH extra delay is added.
delay_distribution defaults to "gaussian"; "lognormal" is opt-in for
long-tail latency experiments.
```

Suggested parameters:

```text
delay_probability
delay_mean_ms
delay_jitter_ms
delay_distribution = "gaussian" | "lognormal"
```

Smoke tests:

```text
delay_probability=0.0 -> delayed == 0
delay_probability=1.0 -> all Byzantine messages delayed
delay jitter -> delayed message latencies are not all identical
delay_distribution="gaussian" -> default behaviour remains compatible with Phase 4 smoke tests
```

### 4c.3 Silent Upgrade

Current behaviour:

```text
Byzantine sender drops all messages with probability = fault_intensity
```

Target behaviour:

- [x] Support probabilistic omission
- [x] Support phase-specific omission
- [x] Allow Byzantine node to omit only prepare messages
- [x] Allow Byzantine node to omit only commit messages
- [x] Allow Byzantine node to omit all consensus messages
- [x] Keep top-level `fault_type='silent'`
- [x] Add `silent_mode` as an attack parameter rather than expanding the top-level fault taxonomy

Suggested modes:

```text
fault_type = "silent"
silent_mode = "all" | "prepare" | "commit"
```

Smoke tests:

```text
silent_prepare -> prepare messages from Byzantine nodes dropped, commit messages unaffected if generated
silent_commit -> commit messages from Byzantine nodes dropped
silent_all -> all Byzantine consensus messages dropped
```

### Pass Criteria

- [x] Enhanced behaviours remain deterministic under fixed `RANDOM_SEED`
- [ ] Enhanced behaviours produce richer feature distributions: at least one of `message_latency`, `message_drop_rate`, or `propagation_pattern` shows higher per-round variance under Phase 4c modes than under Phase 4 modes, measured across >=50 seeded runs of the same `fault_type`
- [x] Existing Phase 4 smoke tests still pass
- [ ] The report clearly distinguishes simple fault classes from enhanced realism modes

**Deliverable:** More realistic message-level Byzantine behaviours for robustness experiments.

---

## Phase 5 — High-Quality Metrics and Feature Extraction

**Files:**

```text
simulation/round_result.py
collection/feature_extractor.py
```

**Goal:** Compute all 11 features from event logs rather than wall-clock proxies.

**Primary reference:** SimPy event logs and this project's A2 feature definitions.

**Secondary reference:** ai-bft-consensus for possible ML-ready node behaviour features, if relevant.

### Feature Definitions

- [x] `message_latency`: mean of `delivery_time - send_time`
- [x] `message_drop_rate`: `dropped_messages / expected_messages`
- [x] `propagation_pattern`: standard deviation of message arrival times
- [x] `consensus_agreement_time`: `round_end_time - round_start_time`
- [x] `phase_completion_time`: `commit_phase_end - prepare_phase_start`
- [x] `timeout_frequency`: number of timeout events in the round
- [x] `leader_change_frequency`: view-change count, initially 0 if view change is documented as out of scope
- [x] `response_time`: mean node first response time after receiving pre-prepare
- [x] `voting_consistency`: nodes with commit quorum divided by total nodes
- [x] `message_consistency`: majority content count divided by total consensus messages
- [x] `vote_deviation`: standard deviation of commit counts per node

### Smoke Test

```text
Run normal, silent, delay, replay, equivocation, and forgery rounds.
Print all 11 features for each fault type.
```

### Auxiliary Metadata and Counters

These auxiliary fields are recorded for validation, ablation, and report interpretation. They MUST NOT be used as model input features unless the corresponding ablation experiment explicitly opts in (see Phase 12).

- [x] `forged`
- [x] `replayed`
- [x] `same_round_replayed`
- [x] `stale_replayed`
- [x] `equivocated`
- [x] `delayed`
- [x] `silent_mode`
- [x] `delay_probability`
- [x] `delay_distribution`
- [x] `strict_round_validation`

Phase 4c modes must preserve all 11 core features and populate the relevant auxiliary counters.

### Pass Criteria

- [x] All 11 features are numeric.
- [x] No feature value is `None`.
- [x] Fault types produce different feature patterns.

**Deliverable:** ML-ready feature rows derived from SimPy event logs.

---

## Phase 6 — Label Generation Upgrade

**File:**

```text
collection/label_generator.py
```

**Goal:** Label each round using simulated consensus state.

**Primary reference:** This project's A2 label schema and PBFT quorum/timeout behaviour.

**Secondary reference:** ByzFL for thinking about adversarial scenario labels and benchmark consistency.

### Label Rules

#### Failure — Label 2

- [x] timeout occurred
- [x] commit quorum not reached
- [x] too many honest nodes failed to commit
- [x] forgery or equivocation prevents valid quorum
- [ ] stale replay affects current-round quorum when `STRICT_ROUND_VALIDATION` is `False` (ablation runs only)

#### Degraded — Label 1

- [x] commit quorum reached but latency exceeds degraded threshold
- [x] message drop rate exceeds warning threshold
- [x] view change triggered
- [x] message consistency below warning threshold
- [x] `forged > 0` and commit still succeeds: safety is not violated, but suspicious sender activity is present
- [x] `same_round_replayed > 0` or `stale_replayed > 0`, while quorum remains valid
- [x] delay jitter causes a late but successful commit
- [x] `silent_mode` causes partial omission but quorum still reaches commit

#### Normal — Label 0

- [x] quorum reached
- [x] no timeout
- [x] latency below threshold
- [x] message consistency acceptable

### Smoke Tests

```text
normal round -> 0
delay but committed late -> 1
silent causing no quorum -> 2
forgery with successful commit and forged > 0 -> 1
forgery causing no commit or quorum on wrong content -> 2
strict validation blocks stale replay -> not failure solely because stale_replayed > 0
```

### Pass Criteria

- [x] Labels match intended consensus conditions.
- [x] Labels are generated from simulated state, not wall-clock runtime.

**Deliverable:** Reliable 3-class label generator.

---

## Phase 7 — Full Dataset Generator

**File:**

```text
main.py
```

**Goal:** Generate raw CSV data from the SimPy simulator.

**Primary reference:** ByzFL for reproducible experiment configuration and attack scenario organisation.

**Secondary reference:** Talaria for full simulation run framing in permissioned blockchain studies.

### Small Run

- [ ] 10 normal rounds
- [ ] 10 silent rounds
- [ ] 10 delay rounds
- [ ] 10 replay rounds
- [ ] 10 equivocation rounds

### Full Run

Main dataset:

- [ ] 400 normal rounds
- [ ] 200 silent rounds
- [ ] 200 replay rounds
- [ ] 200 equivocation rounds
- [ ] 200 delay rounds
- [ ] total: 1200 rows
- [ ] used for model training, validation, and testing with 70 / 10 / 20 split

Extended robustness dataset:

- [ ] 200 forgery rounds with `fault_intensity = 1.0`
- [ ] 100 silent rounds with `silent_mode = "prepare"`
- [ ] 100 silent rounds with `silent_mode = "commit"`
- [ ] 100 silent rounds with `silent_mode = "all"`
- [ ] 100 delay rounds with `delay_distribution = "gaussian"`
- [ ] 100 delay rounds with `delay_distribution = "lognormal"`
- [ ] 100 stale-replay rounds
- [ ] total: 800 rows
- [ ] used for out-of-distribution robustness evaluation only, not model training

Forgery sensitivity runs:

- [x] `fault_intensity in {0.2, 0.5, 1.0}` (`data/raw/forgery_i{20,50,100}.csv`)
- [x] used for Phase 12 authentication-ablation analysis

Config split:

- [ ] Main dataset uses `config.FAULT_TYPES` (4 classes plus normal)
- [ ] Extended dataset uses `config.EXTENDED_FAULT_TYPES` (forgery plus Phase 4c subtypes)

### Output

```text
data/raw/consensus_data.csv
```

### Required Columns

- [ ] `round_id`
- [ ] `fault_type`
- [ ] `fault_subtype`
- [ ] `silent_mode`
- [ ] `delay_probability`
- [ ] `delay_distribution`
- [ ] `strict_round_validation`
- [ ] `byzantine_node_ids`
- [ ] `success`
- [ ] `timeout`
- [ ] auxiliary counters, including `forged`, `same_round_replayed`, and `stale_replayed`
- [ ] all 11 features
- [ ] `label`

`fault_subtype` should be present in both datasets. The main dataset should set it to `base` or `null` to keep the schema consistent.

### Verification

```bash
.venv/bin/python -m scripts.data_generation.main_dataset
.venv/bin/python -c "import pandas as pd; df=pd.read_csv('data/raw/consensus_data.csv'); print(df.shape); print(df['fault_type'].value_counts()); print(df['label'].value_counts())"
```

### Pass Criteria

- [ ] 1200 rows in the initial full run
- [ ] all fault types present
- [ ] labels are not all one class
- [ ] no missing feature values
- [ ] extended robustness dataset is generated separately from the main training dataset

**Deliverable:** `data/raw/consensus_data.csv`

---

## Phase 7b — Project Structure Refactor and Pipeline Hygiene

**Goal:** Reorganise the project into a cleaner `src/` + `scripts/` layout before Phase 8 validation and Phase 9 ML work.

This phase is a structural refactor only. It should not change simulator semantics, feature definitions, label rules, or generated dataset values except for file paths and import paths.

### Target Structure

```text
bft_project/
├── config.py
├── README.md
├── requirements.txt
├── MILESTONES.md
├── SIMPY_MILESTONES.md
│
├── src/
│   ├── __init__.py
│   ├── simulation/
│   ├── data/
│   └── plotting/
│
├── scripts/
│   ├── __init__.py
│   ├── dashboard.py
│   ├── data_generation/     (main_dataset.py, ...)
│   ├── diagnostics/         (validate_simulator.py, ...)
│   ├── training/            (default.py, tuned.py, ...)
│   ├── feature_ablation/
│   ├── lead_time/
│   ├── robustness/
│   ├── scalability/
│   └── plotting/
│
├── data/
├── results/
│   ├── tables/
│   ├── figures/
│   └── models/
│
├── notes/
├── utils/
├── baseline/
└── ml/
```

### Move / Rename Plan

- [ ] Create `src/`
- [ ] Move `simulation/` to `src/simulation/`
- [ ] Rename `collection/` to `src/data/`
- [ ] Rename `visualization/` to `src/plotting/`
- [ ] Create `scripts/`
- [ ] Move `main.py` to `scripts/data_generation/main_dataset.py` (originally planned as `scripts/generate_main_dataset.py`)
- [ ] Move experiment scripts from `experiments/` to `scripts/`
- [ ] Rename `experiments/simulator_validation.py` to `scripts/validate_simulator.py` if present
- [ ] Rename `experiments/ablation_test.py` to `scripts/ablation.py`
- [ ] Rename `experiments/lead_time_test.py` to `scripts/lead_time.py`
- [ ] Rename `experiments/robustness_test.py` to `scripts/robustness.py`
- [ ] Rename `experiments/scalability_test.py` to `scripts/scalability.py`
- [ ] Rename `results/metrics/` to `results/tables/`
- [ ] Keep `notes/`, `utils/`, `baseline/`, and `ml/` in place

### Import and Path Updates

- [ ] Update imports from `simulation.*` to `src.simulation.*`
- [ ] Update imports from `collection.*` to `src.data.*`
- [ ] Update plotting imports to `src.plotting.*`
- [ ] Update dataset generation entry point to `scripts/data_generation/main_dataset.py`
- [ ] Update validation entry point to `scripts/diagnostics/validate_simulator.py`
- [ ] Update result table paths from `results/metrics/` to `results/tables/`
- [ ] Keep raw and processed datasets under top-level `data/`
- [ ] Keep trained models under `results/models/`

### Smoke Tests

```bash
.venv/bin/python -m scripts.data_generation.main_dataset
.venv/bin/python -c "import pandas as pd; df=pd.read_csv('data/raw/consensus_data.csv'); print(df.shape); print(df['label'].value_counts())"
.venv/bin/python -c "import pandas as pd; df=pd.read_csv('data/raw/extended_robustness.csv'); print(df.shape); print(df['fault_subtype'].value_counts())"
```

### Pass Criteria

- [ ] Main dataset generation still works after import-path changes
- [ ] Extended robustness dataset generation still works after import-path changes
- [ ] Existing Phase 5 feature extraction still passes schema validation
- [ ] Existing Phase 6 label generation still produces labels `0`, `1`, and `2`
- [ ] No generated data files are accidentally deleted during the refactor

**Deliverable:** A cleaner project layout that is ready for Phase 8 validation and Phase 9 ML pipeline work.

---

## Phase 8 — Simulator Validation Before ML

**Goal:** Verify the simulator before training models.

**Primary reference:** ByzFL for benchmark validation and per-attack comparison style.

**Secondary reference:** Talaria for simulator-level validation framing.

### Checks

- [x] normal latency distribution
- [x] delay latency distribution
- [x] silent message drop rate
- [x] equivocation message consistency
- [x] replay duplicate/replay count
- [x] forgery `forged` count and quorum timing
- [x] same-round replay versus stale replay counts
- [x] strict round validation blocks stale replay by default
- [x] delay jitter increases latency variance
- [x] `silent_mode` changes message drop pattern by phase
- [x] label balance
- [x] feature correlation
- [x] Phase 4c variance comparison across >=50 seeded runs

### Outputs

```text
results/figures/feature_distribution_by_fault.png
results/figures/feature_distribution_by_subtype.png
results/figures/phase4c_variance_comparison.png
results/tables/simulation_summary.csv
results/tables/advanced_fault_summary.csv
results/tables/feature_correlation.csv
```

Note: `phase4c_variance_comparison.png` is the operational proof for Phase 4c pass criterion PC2 ("richer feature distributions"). This figure must be generated before declaring Phase 4c complete.

### Pass Criteria

- [x] Fault behaviours are visibly separable.
- [x] Fault behaviours are not trivially perfect.
- [x] Feature values are explainable in the report.

**Deliverable:** Validated simulator summary and feature distribution plots.

---

## Phase 9 — ML Pipeline

**Files:**

```text
ml/preprocessing.py
ml/models/decision_tree.py
ml/models/random_forest.py
ml/models/xgboost_model.py
ml/evaluation.py
scripts/training/default.py
```

**Goal:** Train and evaluate ML models.

**Primary reference:** This project's A2 methodology.

**Secondary reference:** ai-bft-consensus for ML + consensus integration ideas, and ByzFL for robust experiment reporting style.

### Tasks

- [x] feature normalisation (Min-Max, fit on train only)
- [x] train / validation / test split: 70 / 10 / 20 (stratified, `random_state=42`)
- [x] train main ML models on the main dataset by default
- [x] evaluate Phase 4b/4c modes as robustness or out-of-distribution tests by default — **completed in Phase 12.B** (`scripts/advanced_fault.py`; fresh default pipelines were used instead of the persisted 11-feature models, see notes/phase12.md)
- [x] include advanced modes in training only when an explicit Phase 12 robustness experiment opts in, e.g. `train_on_extended=True` — **completed in Phase 12.B** (`--train-on-extended` flag)
- [x] Decision Tree
- [x] Random Forest
- [x] XGBoost
- [x] validation-set evaluation
- [x] test-set evaluation
- [x] persist trained models and fitted scaler to `results/models/*.joblib` for downstream Phase 11/12 reuse

### Metrics

- [x] accuracy
- [x] precision (macro-averaged)
- [x] recall (macro-averaged)
- [x] F1-score (macro-averaged)
- [x] confusion matrix
- [x] response time (per-sample inference latency, batch-averaged)
- [ ] prediction lead time — **deferred to Phase 12.A**

### Output

```text
results/tables/model_metrics.csv          (3 models × 2 splits = 6 rows, with `split` column)
results/models/decision_tree.joblib
results/models/random_forest.joblib
results/models/xgboost.joblib
results/models/scaler.joblib
```

### Entry point

```bash
.venv/bin/python -m scripts.training.default
```

### Pass Criteria

- [x] all models train successfully
- [x] metrics saved
- [x] results are reproducible with `RANDOM_SEED = 42`

### Design notes

Non-obvious decisions made during Phase 9 implementation are recorded in
`notes/phase9_design_decisions.md`. This includes the rationale for:
keeping the zero-variance `leader_change_frequency` feature, the choice of
`macro` averaging, fitting the scaler on train only, default
hyperparameters (Phase 12 ablation baseline), the batch-average response
time approximation, and explicit deferral of lead-time / OOD work to Phase 12.

**Deliverable:** Trained ML models, fitted scaler, and main-dataset evaluation metrics.

---

## Phase 10 — Baseline Comparison

**File:**

```text
baseline/static_detection.py
```

**Goal:** Compare ML against traditional static approaches.

**Primary reference:** This project's A2 methodology.

**Secondary reference:** ByzFL for benchmark-style comparison across adversarial scenarios.

### Baselines

- [x] threshold-based detection
- [x] rule-based detection

### Requirements

- [x] same test set as ML models
- [x] same evaluation metrics
- [x] comparison table

### Pass Criteria

- [x] ML and baseline results are directly comparable.
- [x] baseline assumptions are documented.

**Deliverable:** Static baseline comparison.

---

## Phase 11 — Rigorous Training (CV + Hyperparameter Tuning)

**Goal:** Replace Phase 9's default-hyperparameter baseline with a
cross-validated, hyperparameter-tuned, multi-seed training pipeline.
All Phase 12 experiments build on the tuned models produced here.

**Files:**

```text
ml/preprocessing.py            (extend to expose trainval split)
ml/tuning.py                   (new: GridSearch / CV utilities)
scripts/training/tuned.py      (new: rigorous training entry point)
```

**Primary reference:** scikit-learn `StratifiedKFold`, `GridSearchCV`,
`cross_validate`.

**Secondary reference:** This project's A2 methodology; ai-bft-consensus
for ML + consensus reporting style.

### Motivation

Phase 9 trained each model once with default hyperparameters and reported
a single F1 per (model, split). This is acceptable as a baseline but is
not research-quality, because:

- single-split F1 has high variance and can be misleading
- default hyperparameters under-estimate the true capability of each model
- without per-class metrics or multi-seed reporting, OOD/ablation results
  in Phase 12 cannot be interpreted reliably

Phase 11 closes these gaps before any Phase 12 experiment runs.

### Tasks

- [x] inspect `label` distribution and document class balance
- [x] add `class_weight='balanced'` (or equivalent) where appropriate
- [x] merge train + val into a single `trainval` set (80% of data) for CV;
      keep the existing 20% test set untouched
- [x] implement `StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)`
- [x] run `GridSearchCV` per model on `trainval` with macro-F1 as the
      selection metric
- [x] refit each model on the full `trainval` with the best hyperparameters
- [x] repeat training under multiple seeds (e.g. [42, 0, 1, 2, 3]) and
      report mean ± std of test metrics
- [x] add `classification_report` (per-class precision/recall/F1) to the
      evaluation output
- [x] persist tuned models and the fitted scaler to
      `results/models/*_tuned.joblib`
- [x] keep Phase 9's default-hyperparameter models in place (do not delete
      `decision_tree.joblib` etc.) so Phase 12 can report "default vs tuned"
      as one of its ablations

### Search Space (initial)

```text
Decision Tree
  max_depth        in {None, 5, 10, 20}
  min_samples_leaf in {1, 2, 5}

Random Forest
  n_estimators     in {100, 300}
  max_depth        in {None, 10, 20}
  min_samples_leaf in {1, 2}

XGBoost
  n_estimators     in {100, 300}
  max_depth        in {3, 6, 10}
  learning_rate    in {0.05, 0.1, 0.2}
```

The search space may be expanded once initial CV runs confirm the
infrastructure works end-to-end.

### Output

```text
results/tables/cv_results.csv           (per-model, per-fold, per-metric)
results/tables/best_hyperparameters.csv (per-model best config)
results/tables/model_metrics_tuned.csv  (final test metrics, mean ± std over seeds)
results/tables/per_class_report.csv     (classification_report per model)
results/models/decision_tree_tuned.joblib
results/models/random_forest_tuned.joblib
results/models/xgboost_tuned.joblib
results/models/scaler_tuned.joblib
```

### Entry Point

```bash
.venv/bin/python -m scripts.training.tuned
```

### Pass Criteria

- [x] 5-fold CV completes for all three models
- [x] reported test F1 (mean ± std over >=5 seeds) is documented
- [x] best hyperparameters are saved and reproducible from
      `cv_results.csv`
- [x] tuned model test F1 >= default model test F1 for every model
      (otherwise document why and revisit the search space)
- [x] per-class metrics are saved for every (model, split)
- [x] Phase 9 default models remain on disk for the Phase 12.B
      "default vs tuned" ablation

### Design Notes

- Test set (20%) is **never** seen by CV or GridSearchCV. It is touched
  exactly once at the end, per seed.
- Class weighting is applied uniformly across models; if a model does not
  support `class_weight`, use `sample_weight` at fit time.
- Multi-seed averaging applies only to the **final refit + test
  evaluation** step. CV uses a fixed `random_state=RANDOM_SEED` for
  reproducibility of the search itself.
- Lead time, OOD robustness, and feature ablation remain deferred to
  Phase 12 and explicitly consume `*_tuned.joblib`.

**Deliverable:** Tuned ML models, fitted scaler, CV results, and a
per-class evaluation table that all Phase 12 experiments build on.

---

## Phase 11b — Lightweight Model Baseline

**Goal:** Add a linear ML model (Logistic Regression) alongside the
tree-family models from Phase 11. This provides a third tier in the
overall comparison — static rules (Phase 10) → linear ML (Phase 11b) →
tree-family ML (Phase 11) — and lets the report quantify how much of
the detection capability comes from non-linear structure in the data.

**Files:**

```text
ml/models/logistic_regression.py     (new)
scripts/training/tuned.py            (extend to include LR)
```

**Primary reference:** scikit-learn `LogisticRegression`,
`GridSearchCV`, `StratifiedKFold`.

**Secondary reference:** This project's Phase 10 static baseline and
Phase 11 tuned tree-family pipeline (Phase 11b reuses the same CV /
tuning / multi-seed infrastructure).

### Motivation

The current model lineup jumps from "hand-written thresholds and rules"
(Phase 10) straight to "tree ensembles" (Phase 9 / Phase 11). There is
no linear ML model in between. Without one, the report cannot answer:

- How much of the detection capability comes from non-linear structure
  in the feature space, and how much is already captured by a linear
  decision boundary?
- If Logistic Regression performs close to XGBoost, the fault patterns
  are largely linearly separable and tree ensembles are over-engineered
  for this task.
- If Logistic Regression performs much worse than XGBoost, the fault
  patterns require non-linear interactions, which justifies the tree
  ensemble choice.

Phase 11b answers this question with one additional model.

### Tasks

- [x] implement `train_logistic_regression(X, y)` in
      `ml/models/logistic_regression.py`
- [x] apply `class_weight='balanced'` consistent with Phase 11
- [x] run `GridSearchCV` on `trainval` with macro-F1 as selection metric
- [x] reuse Phase 11's `StratifiedKFold(n_splits=5)` and seed list
- [x] refit on full `trainval` with best hyperparameters
- [x] report multi-seed test metrics (mean ± std)
- [x] add per-class precision/recall/F1 to `per_class_report.csv`
- [x] persist tuned LR model to
      `results/models/logistic_regression_tuned.joblib`
- [x] extend `model_metrics_tuned.csv` with the LR row

### Search Space (initial)

```text
Logistic Regression
  C        in {0.01, 0.1, 1.0, 10.0}
  penalty  in {"l2"}                  (l1 requires solver="liblinear" or "saga")
  solver   in {"lbfgs"}               (default, supports multinomial + l2)
  max_iter in {1000}                  (raise if convergence warnings appear)
```

The search space may be extended to include `penalty="l1"` with
`solver="saga"` once initial runs converge cleanly.

### Output

```text
results/models/logistic_regression_tuned.joblib
(LR row appended to)
results/tables/model_metrics_tuned.csv
results/tables/best_hyperparameters.csv
results/tables/per_class_report.csv
results/tables/cv_results.csv
```

### Pass Criteria

- [x] LR training completes under CV + GridSearchCV without convergence
      warnings (or warnings are documented)
- [x] LR test metrics are reported with the same format as Phase 11
      (mean ± std over >=5 seeds, per-class P/R/F1)
- [x] The "static rules → linear ML → tree ensembles" comparison is
      report-ready in `model_metrics_tuned.csv`

### Design Notes

- **Why only Logistic Regression, not SVM or KNN?** SVM with RBF is
  slow on 1200 samples × 11 features once wrapped in 5-fold CV +
  GridSearchCV, and it does not produce per-feature importance for the
  report. KNN has no feature importance at all and provides no
  interpretability gain over Phase 10's rule-based baseline. LR is the
  only linear ML choice that is fast, interpretable, and directly
  comparable to the tree models via coefficient magnitudes.
- **Scaling:** Phase 9's `MinMaxScaler` (already fit on `train`) is
  required for LR. Tree models did not need it but the contract was
  preserved in Phase 9 precisely so LR can plug in here without
  changes.
- **If LR ≈ XGB:** revisit the conclusion that tree ensembles are
  necessary. Document and discuss in the report rather than hiding
  the result.

**Deliverable:** A tuned Logistic Regression model and its multi-seed
evaluation, integrated into the same metrics tables as Phase 11, so
that Phase 12 experiments can include LR as one of the compared
models when relevant.

---

## Phase 11c — Literature and Project-Management Evidence

**Goal:** Prepare the report-supporting evidence needed to justify the
simulator, dataset, ML methodology, and project management process before
starting the final research-quality experiments in Phase 12.

**Files / Artifacts:**

```text
notes/literature_review.md           (new or extend existing notes)
notes/key_papers.md                  (new: methodology support map)
results/tables/project_plan.csv      (optional export from Excel/Gantt)
results/figures/project_gantt.png    (optional Gantt chart figure)
```

### Tasks

- [ ] complete the literature review
- [ ] identify key papers supporting:
      PBFT / Byzantine fault tolerance; SimPy-based discrete-event
      simulation; Byzantine fault injection; ML-based fault detection;
      baseline comparison; ablation / robustness study design
- [ ] create a project plan or Gantt chart showing completed phases,
      remaining phases, and final submission tasks
- [ ] map each major implementation choice to supporting evidence:
      simulator design, fault models, feature set, label rules, dataset
      generation, model selection, baseline comparison, and evaluation
      metrics
- [ ] prepare report-ready notes for methodology and project management
- [ ] keep this section as supporting evidence only; it must not change
      the Phase 11 training protocol or Phase 12 experimental design

### Pass Criteria

- [ ] literature review draft is complete enough to support the Methodology
      and Related Work sections of the final report
- [ ] at least one key reference is mapped to each major methodology choice
- [ ] project plan / Gantt chart clearly shows progress tracking and
      remaining work
- [ ] report can explain why the simulator, dataset, ML models, baselines,
      and ablation experiments are methodologically justified

**Deliverable:** Literature-review notes, key-paper mapping, and
project-management evidence ready to be reused in the final report.

---

## Phase 12 — Research-Quality Experiments

**Goal:** Produce report-ready experimental evidence.

**Primary reference:** ByzFL for robustness and attack-wise benchmarking.

**Secondary reference:** Talaria for simulation-study reporting style, and ai-bft-consensus for ML + consensus discussion angles.

### 12.A Main Experiments

- [x] ablation test
- [x] feature set ablation: 11 features vs 13 features
      (adds `quorum_margin`, `prepare_count_std`)
- [x] robustness test
- [x] scalability test
- [x] per-fault-type analysis
- [x] prediction lead time analysis
- [x] SHAP feature importance

### 12.B Advanced Fault Robustness

- [x] Train on the main fault set only
- [x] Test on forgery and Phase 4c enhanced modes as out-of-distribution data
- [x] Report degradation in F1-score, recall, and confusion matrix quality
- [x] Optional opt-in run: `train_on_extended=True`

### 12.C Authentication Ablation

- [x] Evaluate forgery as an authentication-ablation scenario
- [x] Compare `fault_intensity in {0.2, 0.5, 1.0}`
- [x] Report whether forged votes alter quorum timing or label distribution — quorum timing: yes (agreement_time 67.8 → 59.2 ms, monotone); label distribution: saturated at i0.2 (existence rule `forged > 0`), see notes/phase12.md
- [x] Clearly state that production PBFT normally relies on authenticated messages

### 12.D Strict-Round-Validation Ablation

- [x] Run stale replay with `STRICT_ROUND_VALIDATION=True`
- [x] Run stale replay with `STRICT_ROUND_VALIDATION=False`
- [x] Compare quorum behaviour, labels, and replay counters
- [x] Report whether stale replay becomes harmful only under the weakened validation setting

### 12.E Optional Mixed-N Training

**Goal:** Test whether exposing the model to multiple network sizes and
Byzantine node counts at a controlled PBFT-safe ratio improves
generalisation compared with training only on the original `N=7, f=2`
main dataset.

**Motivation:** Phase 12.B tests exposure to new attack types
(`train_on_extended=True`). Phase 12.E mirrors that idea for network
configuration diversity: exposure to larger `N` settings may make the
classifier more robust to scale shift.

**Scope rule:** Keep Phase 12.E within PBFT's normal safety envelope and
preserve the Phase 12.A-4 design discipline: vary network size while
holding the Byzantine ratio near the PBFT bound. Do not mix a full
two-axis `(N, f)` grid into this phase. Mixed `f` ratios and
out-of-bound settings such as `N=7, f=3` change the monitoring question
from "scale generalisation" to "attack-concentration and protocol-bound
stress testing"; they remain future work.

**Candidate configurations:**

```text
N=7,  f=2  (main dataset trainval)
N=10, f=3  (matches Phase 12.A-4 scalability test config)
N=13, f=4  (matches Phase 12.A-4 scalability test config)
```

**Tasks:**

- [x] Generate N=10 and N=13 training pools with the same fault taxonomy
      and composition as the scalability test sets, using a dedicated
      `MIXED_N_TRAIN_SEED` (deterministic simulator: reusing the test
      seed would clone the test sets into training data)
- [x] Verify no seed-cloned test-set leakage between each training pool
      and its same-N test set — de-duplicated feature space has exactly
      1 colliding row per N, a degenerate all-Byzantine-silent timeout
      state (message_drop_rate=1.0, response_time=timeout ceiling) that
      any seed converges to once consensus fully fails; not a seed leak,
      see notes/phase12.md
- [x] Train the default model family under two arms per seed: baseline
      (`N=7` trainval only) and mixed (`N=7 + N=10 + N=13` pools)
- [x] Evaluate both arms on the same three test sets: `N=7` 20% holdout,
      `scalability_n10.csv`, and `scalability_n13.csv` (5 seeds,
      protocol identical to Phase 12.A-3/4/5, 12.B, 12.C, and 12.D)
- [x] Report whether mixed exposure improves scale generalisation or
      creates a trade-off with in-distribution performance — tree
      models recover sharply at N=13 (decision_tree 0.824→0.942,
      random_forest 0.906→0.970, xgboost 0.893→0.970) at a small N=7
      cost (roughly 1-1.5 F1 points); see notes/phase12.md
- [x] Document the data-size confound: the mixed arm trains on roughly
      3x rows; this follows the add-data framing used in Phase 12.B,
      while a size-matched control remains an optional follow-up
- [x] Include the three static baselines in both arms: threshold_based
      and count_based are refit per arm (their fitted thresholds are
      N=7-anchored in the baseline arm, mixed-anchored in the mixed
      arm); rule_based uses config constants only and is identical
      across arms (arm-invariant control) — confirmed rule_based F1 is
      bit-for-bit identical between arms at all three N

**Suggested outputs:**

```text
data/raw/mixed_n_train_n10.csv
data/raw/mixed_n_train_n13.csv
results/tables/mixed_n_curve.csv
results/figures/mixed_n_curve.png
```

**Pass Criteria:**

- [x] Baseline-arm F1 reproduces `scalability_curve.csv` bit-for-bit
      (pipeline anchor) — verified, max abs diff = 0.0 across all
      model x N combinations
- [x] Training pools are verified leak-free against test sets — 1
      benign degenerate-state collision per N, documented above and in
      notes/phase12.md; not a seed/pipeline leak
- [x] Results state whether the Phase 12.A-4 tree-model degradation is
      curable by exposure (data-coverage problem) or persists
      (architectural), and what this means for the LR-vs-trees
      deployment discussion — curable: mixed-N exposure closes almost
      all of the N=13 gap for every tree model, so the 12.A-4
      degradation reflects insufficient training coverage rather than
      an architectural ceiling; see notes/phase12.md
- [x] Report clearly separates within-bound mixed-N training from
      out-of-bound (`f > floor((N-1)/3)`) stress testing and two-axis
      `(N, f)` grids, which remain future work
- [x] The static tier separates fitted-threshold detectors from
      constant/ratio-based rules across N, testing the 12.A-4
      "memorised N=7-anchored thresholds" diagnosis — threshold_based
      and count_based shift measurably between arms, rule_based does
      not, consistent with the diagnosis

### Outputs

```text
results/figures/confusion_matrix_*.png
results/figures/model_comparison.png
results/figures/feature_importance.png
results/figures/lead_time_comparison.png
results/figures/robustness_curve.png
results/figures/scalability_curve.png
```

### Pass Criteria

- [x] figures are report-ready
- [x] tables are report-ready
- [x] results answer the research question

**Deliverable:** Full experimental result package.

---

## Phase 13 — Future Work: Graph Neural Network Monitor

**Goal:** Explore whether PBFT monitoring improves when each consensus
round is represented as a graph rather than as aggregate tabular
features.

**Motivation:** The current project deliberately uses lightweight,
interpretable round-level classifiers over engineered features. A GNN
extension would model the protocol more directly: replicas become nodes,
protocol messages become typed edges, and the monitor predicts a
round-level `normal` / `degraded` / `failure` label from node and edge
behaviour.

**Scope rule:** Keep this out of the current main conclusion. Phase 13
is a future research direction, not a requirement for validating the
current early-warning claim.

**Candidate design:**

```text
Nodes: PBFT replicas
Edges: observed protocol messages, optionally typed by phase
Node features: local vote counts, timeout state, received-message counts
Edge features: latency, dropped/delivered status, message type, sender role
Graph label: round label (normal / degraded / failure)
```

**Tasks:**

- [x] Persist per-round node-level and edge-level traces from the
      simulator instead of only aggregate round features
- [x] Build graph datasets that support variable network sizes
      (`N=7`, `N=10`, `N=13`)
- [x] Train a graph-level classifier and compare it against the existing
      tabular ML models
- [x] Check whether graph structure improves scale generalisation beyond
      the mixed-N tabular baseline

**Pass Criteria:**

- [x] GNN is evaluated on the same fault taxonomy and train/test regimes
      as the tabular pipeline
- [x] Results show whether graph structure adds signal beyond engineered
      aggregate features
- [x] The added complexity is justified by measurable gains or clearer
      node-level diagnostics

---

## Plotting Backlog — Report-Complete Figure Set

**Goal:** Maintain a complete figure checklist for the practical project
report and dashboard. Existing performance plots already cover much of
the model comparison story; the remaining gap is mostly dataset
composition, feature-shift explanation, early-warning detail, and graph
dataset interpretability.

### A. Dataset and Simulator Sanity

- [x] `dataset_label_distribution.png` — label counts
      (`normal` / `degraded` / `failure`) across all generated datasets
- [x] `dataset_fault_composition.png` — fault type/subtype counts across
      main, extended, scalability, and mixed-N datasets
- [x] `feature_distribution_by_fault.png` — 13-feature boxplots grouped
      by fault type
- [x] `feature_correlation_heatmap.png` — correlation heatmap for the
      13-feature schema
- [x] `label_by_fault_type.png` — label distribution within each fault
      type, showing which faults produce normal-like, degraded, or
      failure rounds

### B. Main Model Performance

- [ ] `model_comparison.png` — headline accuracy/precision/recall/F1 for
      main ML models
- [ ] `baseline_vs_ml.png` — ML monitors versus static
      threshold/rule/count baselines
- [ ] `confusion_matrix_<model>.png` — normal/degraded/failure confusion
      matrices on the main test split
- [ ] `per_class_f1.png` — class-level F1, especially for the degraded
      class that supports the early degradation claim

### C. Early Prediction

- [ ] `lead_time_comparison.png` — average warning lead time by model and
      fault type
- [ ] `lead_time_false_alarm.png` — false alarm rate on normal rounds
      across prediction cutoffs
- [ ] `lead_time_f1_by_cutoff.png` — macro-F1 at
      `25/50/75/100/125/150 ms`
- [ ] `early_detection_rate_by_cutoff.png` — degraded/failure detection
      rate at each cutoff

### D. Robustness and Generalisation

- [x] `robustness_curve.png` — Byzantine-count/ratio shift
- [x] `scalability_curve.png` — `N=7/10/13` network-size shift
- [x] `mixed_n_curve.png` — N=7-only versus mixed-N training
- [x] `feature_shift_by_network_size.png` — key feature distributions
      across `N=7`, `N=10`, and `N=13`
- [x] `ood_f1_by_fault_subtype.png` — advanced-fault subtype performance
- [x] `ood_exposure_comparison.png` — main-only versus extended-exposure
      OOD performance

### E. Ablations and Security Assumptions

- [x] `feature_ablation.png` — 11 features versus
      `+quorum_margin`, `+prepare_count_std`, and full 13-feature set
- [x] `tuning_ablation.png` — default versus tuned models
- [x] `auth_ablation_detection.png` — forgery intensity detection
- [x] `strict_ablation_detection.png` — strict round validation on/off
      detection
- [x] `strict_ablation_quorum.png` or
      `strict_ablation_success_timeout.png` — protocol-level effect of
      strict validation on quorum, success, or timeout behaviour

### F. GNN Extension

- [x] `gnn_scalability_curve.png` — GNN versus tabular models under
      N=7-only training
- [x] `graph_dataset_summary.png` — graph count, average edge count, node
      count, and label distribution for `N=7/10/13`
- [x] `gnn_confusion_matrix.png` — GNN confusion matrices on
      `N=7`, `N=10`, and `N=13`
- [x] `gnn_mixed_n_curve.png` — baseline GNN versus mixed-N GNN, if
      mixed-N graph training is implemented

### G. Explanatory and Deployment Supplements

Figures outside the original evidence checklist. Groups A-F prove the
results; group G explains the system and the deployment claim in the
report's methodology and discussion sections.

Script-generated:

- [x] `pbft_round_timeline.png` — message send/delivery timeline of one
      normal round versus one delay-fault round, drawn from the
      simulator message log; explains what the simulator models and
      what a delay attack looks like
- [x] `inference_latency_comparison.png` — per-sample inference latency
      of static baselines, LR, tree models, and GNN/BiLSTM (log scale);
      operational evidence for the lightweight-monitor claim
- [x] `learning_curve.png` — test macro-F1 versus training-set size
      (optional); pre-empts the "is 1200 rows enough?" question

Hand-drawn (draw.io / PowerPoint, not script-generated):

- [x] `system_architecture` — simulator module diagram
      (network → node → pbft → fault_injector → features → labels)
- [x] `experiment_pipeline` — end-to-end pipeline diagram
      (simulate → features → labels → train → evaluate → ablations)
- [x] `project_gantt.png` — tracked in Phase 11c; listed here for
      completeness

### Backfill — Figures Promised by Earlier Phases

Output figures listed by earlier phases that are currently missing from
`results/figures/` (the results directory was cleared at some point).
All scripts and input data exist; regenerate with the commands shown.

- [x] `phase4c_variance_comparison.png` — Phase 8; operational proof of
      Phase 4c pass criterion PC2 (`scripts.diagnostics.validate_simulator`)
- [x] `feature_distribution_by_subtype.png` — Phase 8
      (`scripts.diagnostics.validate_simulator`)
- [x] `feature_importance.png` — Phase 12.A SHAP
      (`scripts.diagnostics.shap_analysis`)
- [x] `detection_rate_by_fault_type.png` — Phase 12.A
      (`scripts.diagnostics.per_fault_type` then `scripts.plotting.per_fault_type`)
- [x] `failure_recall_by_fault_type.png` — Phase 12.A
      (same commands as above)

**Priority subset:** If time is limited, prioritise
`dataset_label_distribution.png`, `dataset_fault_composition.png`,
`label_by_fault_type.png`, `feature_distribution_by_fault.png`,
`feature_shift_by_network_size.png`, `baseline_vs_ml.png`,
`lead_time_f1_by_cutoff.png`, and `graph_dataset_summary.png`.

---

## Phase 14 — Future Work: Temporal BiLSTM Monitor

**Goal:** Explore whether temporal sequence models can predict consensus
degradation from trends across consecutive rounds.

**Motivation:** The current pipeline mostly treats each consensus round
as an independent tabular sample. A BiLSTM only becomes conceptually
useful if the task is reframed as sequence monitoring, where previous
rounds provide context for predicting the current or next round state.

**Scope rule:** Do not add BiLSTM as a single-row classifier. Phase 14
should use real multi-round windows; otherwise it does not test a
meaningfully temporal hypothesis.

**Candidate design:**

```text
Input: windows of k previous rounds, e.g. k = 5 or 10
Features: existing round-level feature vectors per timestep
Target: current-round label or next-round label
Split: contiguous simulation segments, not random row leakage
```

**Tasks:**

- [x] Construct sequence datasets from ordered simulation rounds
- [x] Evaluate multiple window sizes and compare against non-temporal
      tabular models
- [x] Use leakage-safe splits that preserve temporal ordering
- [x] Report whether temporal context improves early warning at the
      lead-time cutoffs

**Pass Criteria:**

- [x] BiLSTM is evaluated only under a true sequence formulation
- [x] Results are compared against the existing lead-time experiment
- [x] Any gains are interpreted as temporal-context gains, not just
      higher model capacity

---

## Phase 15 — Lightweight Results Dashboard

**Goal:** Build a compact dashboard for inspecting the generated PBFT
monitoring results without turning the project into a full web
application.

**Motivation:** By Phase 12-14, the project produces many result tables
and figures across model families, ablations, fault modes, scale shifts,
lead-time cutoffs, advanced faults, mixed-N exposure, and graph/temporal
extensions. A lightweight dashboard makes the practical project easier
to demo, reproduce, and explain during review or presentation.

**Scope rule:** Keep this as a results viewer, not an experiment runner.
The dashboard should read existing `results/tables/*.csv` and
`results/figures/*.png` outputs. It should not retrain models, regenerate
datasets, upload arbitrary data, or become a separate frontend project.

**Recommended implementation:** Use Streamlit, because the repository is
already Python-first and the dashboard can directly reuse pandas and the
generated result files.

**Candidate views:**

```text
Overview: research question, dataset sizes, model families, fault modes
Main Results: ML models versus static baselines
Early Prediction: lead-time F1, detection rate, false alarm rate
Generalisation: robustness, scalability, OOD, mixed-N exposure
Ablations: feature set, tuning, authentication, strict-round validation
GNN Extension: in-distribution versus scale-shift graph results
```

**Tasks:**

- [x] Add a lightweight dashboard entry point: `scripts/dashboard.py`
      (kept outside `src/plotting/` so the entry script does not shadow
      the `src/plotting/dashboard/` package)
- [x] Load available CSV tables defensively, showing clear placeholders
      when optional experiments have not been run
- [x] Provide compact charts for headline metrics and scale/lead-time
      curves
- [x] Display generated figures where they already exist instead of
      reimplementing every plot
- [x] Document the launch command in the README

**Suggested command:**

```bash
streamlit run scripts/dashboard.py
```

**Pass Criteria:**

- [x] Dashboard launches from the repository root
- [x] Missing optional result files do not crash the app
- [x] Core Phase 12 results are visible without manual CSV inspection
- [x] Dashboard supports presentation/demo use while preserving the
      project's script-based reproducibility

---
