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
Phase 11 -> Research-quality experiments
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
.venv/bin/python -c "import simpy; from simulation.message import Message; from simulation.simpy_network import SimPyNetwork; env=simpy.Environment(); net=SimPyNetwork(env); print(env.now)"
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
.venv/bin/python -c "from simulation.node import Node; n=Node(0); print(n.node_id)"
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
.venv/bin/python -c "from simulation.pbft import run_pbft_round; print(run_pbft_round(round_id=1, fault_type='normal'))"
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

- [ ] `silent`: Byzantine node does not send selected messages.
- [ ] `delay`: Byzantine messages receive additional simulated latency.
- [ ] `replay`: Byzantine node resends old messages.
- [ ] `equivocation`: Byzantine node sends different content to different receivers.

### Configuration

- [ ] `fault_type`
- [ ] `fault_ratio`
- [ ] `fault_intensity`
- [ ] `byzantine_node_ids`
- [ ] `random_seed`

### Smoke Tests

```text
silent        -> delivered_messages < expected_messages
delay         -> average latency increases
replay        -> replayed_message_count > 0
equivocation  -> message_consistency decreases
```

### Pass Criteria

- [ ] Each fault type produces distinguishable metrics.
- [ ] Fault behaviour is deterministic under fixed random seed.

**Deliverable:** Four controllable Byzantine fault behaviours.

---

## Phase 4b — Advanced Fault Injection: Forgery

**Goal:** Add an optional authentication-ablation fault where Byzantine nodes spoof sender identities.

This does not replace `replay`. It is an additional advanced scenario that models what can happen when a simulator or protocol variant trusts `sender_id` as a plain field without cryptographic signature or authenticated-channel verification.

Mechanism: `prepare_log[round_id][content]` and `commit_log[round_id][content]` are `set[int]` structures keyed by `sender_id`. A replayed message with the same `sender_id` is silently deduplicated, but a forged message claiming a fresh honest `sender_id` adds a new element to the quorum set. This is why forgery can alter quorum behaviour while simple replay mainly increases message volume.

**Primary reference:** PBFT authentication assumptions and this project's BFT simulator design.

**Secondary reference:** csienslab/BFT-Simulator for adversarial message manipulation structure.

### Fault Type

- [ ] `forgery` / `sender_spoofing`: Byzantine node sends a valid-looking prepare or commit message using a forged honest `sender_id`.

### Requirements

- [ ] Implement `_on_forgery()` in `simulation/fault_injector.py`
- [ ] Select forged `sender_id` from honest node IDs, not Byzantine node IDs
- [ ] Forged `sender_id` must differ from the original `msg.sender_id`
- [ ] Mark forged messages with `is_corrupt=True`
- [ ] Mark forged messages with `fault_type='forgery'`
- [ ] Implementation pattern: emit both messages — `return [msg, forged]`
- [ ] The original message preserves the Byzantine node's own vote
- [ ] The forged copy is the attack payload and steals a fresh honest identity
- [ ] `fault_intensity` controls the probability that a Byzantine send produces a forged copy
- [ ] `fault_intensity=1.0` means every Byzantine send creates one forged copy
- [ ] `fault_intensity=0.4` means roughly 40% of Byzantine sends create one forged copy
- [ ] Add `forged` to `round_stats`, matching the existing past-tense naming style: `delivered`, `dropped`, `delayed`, `replayed`, `equivocated`
- [ ] Verify forged sender IDs appear in `prepare_log` or `commit_log`
- [ ] If no honest sender candidate exists, skip forgery and return `[msg]` as a graceful fallback
- [ ] Document that this fault assumes no cryptographic signature verification

### Smoke Test

```text
forgery -> forged > 0
forgery -> message_log contains is_corrupt=True and fault_type='forgery'
forgery -> prepare_log or commit_log contains forged honest sender IDs
forgery -> quorum may be reached with fewer real honest votes than baseline
```

### Pass Criteria

- [ ] Forgery produces distinguishable metrics.
- [ ] Forged votes can affect quorum behaviour in the no-authentication setting.
- [ ] The report clearly explains that real PBFT normally relies on authenticated messages, so forgery is an authentication-ablation scenario.

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

- [ ] Keep same-round duplicate replay as the baseline replay mode
- [ ] Add optional stale-round replay mode
- [ ] Store a small replay buffer of previously sent Byzantine messages
- [ ] Replay a previous valid message with its old round metadata
- [ ] Track same-round duplicates separately from stale-round replays
- [ ] Ensure stale-round replay does not affect quorum unless a deliberate no-round-validation ablation is enabled

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

- [ ] Make delay probabilistic using `delay_probability`
- [ ] Add jitter to Byzantine delay
- [ ] Sample additional delay from a configurable distribution
- [ ] Support at least Gaussian delay jitter
- [ ] Optionally support lognormal delay for long-tail latency experiments
- [ ] Keep lognormal disabled by default for backward-compatible Phase 4 smoke tests

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

- [ ] Support probabilistic omission
- [ ] Support phase-specific omission
- [ ] Allow Byzantine node to omit only prepare messages
- [ ] Allow Byzantine node to omit only commit messages
- [ ] Allow Byzantine node to omit all consensus messages
- [ ] Keep top-level `fault_type='silent'`
- [ ] Add `silent_mode` as an attack parameter rather than expanding the top-level fault taxonomy

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

- [ ] Enhanced behaviours remain deterministic under fixed `RANDOM_SEED`
- [ ] Enhanced behaviours produce richer feature distributions: at least one of `message_latency`, `message_drop_rate`, or `propagation_pattern` shows higher per-round variance under Phase 4c modes than under Phase 4 modes, measured across >=50 seeded runs of the same `fault_type`
- [ ] Existing Phase 4 smoke tests still pass
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

- [ ] `message_latency`: mean of `delivery_time - send_time`
- [ ] `message_drop_rate`: `dropped_messages / expected_messages`
- [ ] `propagation_pattern`: standard deviation of message arrival times
- [ ] `consensus_agreement_time`: `round_end_time - round_start_time`
- [ ] `phase_completion_time`: `commit_phase_end - prepare_phase_start`
- [ ] `timeout_frequency`: number of timeout events in the round
- [ ] `leader_change_frequency`: view-change count, initially 0 if view change is documented as out of scope
- [ ] `response_time`: mean node first response time after receiving pre-prepare
- [ ] `voting_consistency`: nodes with commit quorum divided by total nodes
- [ ] `message_consistency`: majority content count divided by total consensus messages
- [ ] `vote_deviation`: standard deviation of commit counts per node

### Smoke Test

```text
Run normal, silent, delay, replay, and equivocation rounds.
Print all 11 features for each fault type.
```

### Pass Criteria

- [ ] All 11 features are numeric.
- [ ] No feature value is `None`.
- [ ] Fault types produce different feature patterns.

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

- [ ] timeout occurred
- [ ] commit quorum not reached
- [ ] too many honest nodes failed to commit

#### Degraded — Label 1

- [ ] commit quorum reached but latency exceeds degraded threshold
- [ ] message drop rate exceeds warning threshold
- [ ] view change triggered
- [ ] message consistency below warning threshold

#### Normal — Label 0

- [ ] quorum reached
- [ ] no timeout
- [ ] latency below threshold
- [ ] message consistency acceptable

### Smoke Tests

```text
normal round -> 0
delay but committed late -> 1
silent causing no quorum -> 2
```

### Pass Criteria

- [ ] Labels match intended consensus conditions.
- [ ] Labels are generated from simulated state, not wall-clock runtime.

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

- [ ] 400 normal rounds
- [ ] 200 silent rounds
- [ ] 200 replay rounds
- [ ] 200 equivocation rounds
- [ ] 200 delay rounds

### Output

```text
data/raw/consensus_data.csv
```

### Required Columns

- [ ] `round_id`
- [ ] `fault_type`
- [ ] `byzantine_node_ids`
- [ ] `success`
- [ ] `timeout`
- [ ] all 11 features
- [ ] `label`

### Verification

```bash
.venv/bin/python main.py
.venv/bin/python -c "import pandas as pd; df=pd.read_csv('data/raw/consensus_data.csv'); print(df.shape); print(df['fault_type'].value_counts()); print(df['label'].value_counts())"
```

### Pass Criteria

- [ ] 1200 rows in the initial full run
- [ ] all fault types present
- [ ] labels are not all one class
- [ ] no missing feature values

**Deliverable:** `data/raw/consensus_data.csv`

---

## Phase 8 — Simulator Validation Before ML

**Goal:** Verify the simulator before training models.

**Primary reference:** ByzFL for benchmark validation and per-attack comparison style.

**Secondary reference:** Talaria for simulator-level validation framing.

### Checks

- [ ] normal latency distribution
- [ ] delay latency distribution
- [ ] silent message drop rate
- [ ] equivocation message consistency
- [ ] replay duplicate/replay count
- [ ] label balance
- [ ] feature correlation

### Outputs

```text
results/figures/feature_distribution_by_fault.png
results/metrics/simulation_summary.csv
```

### Pass Criteria

- [ ] Fault behaviours are visibly separable.
- [ ] Fault behaviours are not trivially perfect.
- [ ] Feature values are explainable in the report.

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
```

**Goal:** Train and evaluate ML models.

**Primary reference:** This project's A2 methodology.

**Secondary reference:** ai-bft-consensus for ML + consensus integration ideas, and ByzFL for robust experiment reporting style.

### Tasks

- [ ] feature normalisation
- [ ] train / validation / test split: 70 / 10 / 20
- [ ] Decision Tree
- [ ] Random Forest
- [ ] XGBoost
- [ ] validation-set evaluation
- [ ] test-set evaluation

### Metrics

- [ ] accuracy
- [ ] precision
- [ ] recall
- [ ] F1-score
- [ ] confusion matrix
- [ ] response time
- [ ] prediction lead time

### Output

```text
results/metrics/model_metrics.csv
```

### Pass Criteria

- [ ] all models train successfully
- [ ] metrics saved
- [ ] results are reproducible with `RANDOM_SEED = 42`

**Deliverable:** Trained ML models and evaluation metrics.

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

- [ ] threshold-based detection
- [ ] rule-based detection

### Requirements

- [ ] same test set as ML models
- [ ] same evaluation metrics
- [ ] comparison table

### Pass Criteria

- [ ] ML and baseline results are directly comparable.
- [ ] baseline assumptions are documented.

**Deliverable:** Static baseline comparison.

---

## Phase 11 — Research-Quality Experiments

**Goal:** Produce report-ready experimental evidence.

**Primary reference:** ByzFL for robustness and attack-wise benchmarking.

**Secondary reference:** Talaria for simulation-study reporting style, and ai-bft-consensus for ML + consensus discussion angles.

### Experiments

- [ ] ablation test
- [ ] robustness test
- [ ] scalability test
- [ ] per-fault-type analysis
- [ ] prediction lead time analysis
- [ ] SHAP feature importance

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

- [ ] figures are report-ready
- [ ] tables are report-ready
- [ ] results answer the research question

**Deliverable:** Full experimental result package.

---

## Immediate Next Steps

1. [ ] Add `simpy` to `requirements.txt`
2. [ ] Implement `simulation/message.py`
3. [ ] Implement `simulation/simpy_network.py`
4. [ ] Run one-message delivery smoke test
5. [ ] Implement event-driven `simulation/node.py`
6. [ ] Run one normal PBFT round
7. [ ] Run one delay-fault PBFT round
