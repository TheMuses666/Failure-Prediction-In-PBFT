# Literature Review

Draft notes for the dissertation's Related Work and Methodology chapters.
Six themes, one citation block. Every theme maps to at least one
methodology choice made in Phases 0 – 11b, and every cited work has been
read (or, where marked, is on the to-read list with a clear reason).

This file consolidates the previously scattered notes:

- [phase4c_literature.md](phase4c_literature.md) — fault-injection sources
- [phase10_baseline_references.md](phase10_baseline_references.md) — baseline sources
- [byzantine_realism.md](byzantine_realism.md) — fidelity self-assessment
- [phase9_design_decisions.md](phase9_design_decisions.md) — ML rationale
- [phase11.md](phase11.md) — CV / tuning rationale

If a topic is covered in depth in one of those files, this review
summarises it and cross-links rather than duplicating prose.

---

## 1. PBFT and Byzantine Fault Tolerance

### 1.1 Protocol foundations

Practical Byzantine Fault Tolerance (Castro & Liskov, 1999) is the
canonical reference for the three-phase agreement pattern
(pre-prepare → prepare → commit) and for the `n >= 3f + 1` replica
bound. Our simulator implements exactly this pattern with `n = 7` and
`f = 2`, giving a commit quorum of `2f + 1 = 5`.

> *"We adopt the three-phase agreement pattern of Castro & Liskov (1999)
> with seven replicas (n = 7) and a tolerated-fault bound of f = 2,
> yielding a commit quorum threshold of 2f + 1 = 5 voting nodes."*

### 1.2 Why no view-change implementation?

Castro & Liskov (1999, §4.4) define view-change as the recovery path
when the primary is suspected faulty. Our simulator records
`leader_change_frequency` as a feature but always reports `0`, because
view-change is documented as out of scope (SIMPY_MILESTONES.md:521).
This is honest: simulating view-change correctly requires modelling
new-view certificates and checkpoint state, which is a project of its
own. The feature is kept in the schema so that a future extension can
populate it without breaking downstream code; see also
[phase9_design_decisions.md](phase9_design_decisions.md) for why a
zero-variance feature was retained.

### 1.3 PBFT performance characterisation

Sukhwani et al. (2017) provide an empirical latency study of PBFT
inside Hyperledger Fabric. We cite this in two places: (a) to justify
the Gaussian assumption used by the threshold baseline (Phase 10), and
(b) to anchor our normal-round latency thresholds in measured
production-like behaviour rather than picking numbers out of the air.

---

## 2. Discrete-Event Simulation and SimPy

### 2.1 Why discrete-event simulation at all?

The alternative — spinning up seven real PBFT nodes in containers —
gives the most authentic data but couples experiments to host scheduling
noise, kernel network stack variance, and wall-clock drift. For a
controlled study where we want to isolate the effect of one Byzantine
fault class at a time, DES is the correct abstraction: we keep the
protocol logic identical while making latency, drop, and Byzantine
behaviour first-class parameters. Banks et al. (1996, *Discrete-Event
System Simulation*, 2nd edn) is the standard textbook reference for
this trade-off; the edition consulted is the one held at Lancaster
University Library, and ch. 1 ("Introduction to Simulation") is the
relevant chapter for justifying the methodology choice.

### 2.2 Why SimPy specifically?

SimPy (Matloff, 2008; current docs at simpy.readthedocs.io) is a
process-based DES framework in Python. We picked it over Salabim or
custom event loops for three concrete reasons:

1. **`env.now` replaces `time.sleep()`** — all phase timings are in
   simulated milliseconds, so a 1200-round full run completes in
   seconds of wall-clock time and is exactly reproducible under
   `RANDOM_SEED`.
2. **Process generators model nodes naturally** — each replica is a
   SimPy process; `yield env.timeout(latency)` reads like the
   pseudo-code in PBFT papers.
3. **Python-native** — the rest of the stack (scikit-learn, XGBoost,
   pandas) is Python; no language boundary.

The methodology section will state explicitly that simulated time is
the unit of measurement throughout the dataset and that all latencies
reported are in `env.now` milliseconds, not wall-clock.

### 2.3 Reference simulators we did NOT directly use

- **Talaria** (permissioned-blockchain simulator) — informed our
  per-round result schema but its logging model is JSON-event-stream
  rather than a per-round DataFrame; we use it for methodology framing
  only (SIMPY_MILESTONES.md:38).
- **csienslab/BFT-Simulator** — informed our attacker design but its
  network model is synchronous-round-based, not DES; see
  [phase4c_literature.md](phase4c_literature.md) for the attacker-side
  comparison.

---

## 3. Byzantine Fault Injection

This section is the most heavily backed by external work and is already
written in detail in [phase4c_literature.md](phase4c_literature.md) and
[byzantine_realism.md](byzantine_realism.md). Summary for the review:

### 3.1 Fault taxonomy alignment

Mastromauro et al. (2025) survey attacks and defences on consensus
protocols and propose a four-family taxonomy
(Majority-Disruption / Integrity / Manipulation / Communication). Our
five fault classes map cleanly onto two of these families:

| Our fault class | Survey family | Survey reference |
| --------------- | ------------- | ---------------- |
| silent          | Communication | Mastromauro et al. 2025, §VI.D |
| delay           | Communication | Mastromauro et al. 2025, §VI.D.2 |
| replay (duplicate + stale) | Communication | Mastromauro et al. 2025, §VI.D.2 |
| equivocation    | Manipulation  | Castro & Liskov 1999, §3 (safety) |
| forgery         | Manipulation  | Mastromauro et al. 2025, §V.B |

Using the survey's taxonomy in the dissertation pre-empts the "where
does your fault list come from?" question.

### 3.2 Fault-injection methodology

ByzPlug (Rocha, 2024) is the closest published comparable: a
protocol-agnostic, packet-level fault-injection tool for BFT systems.
Our Phase 4 `replay` mode is functionally equivalent to ByzPlug's
`replay` primitive (`uint32 replay = 3`). Phase 4c additions
(stale-round replay, phase-specific silent, distribution-based delay)
go *beyond* ByzPlug, because we exploit PBFT-specific structure that
ByzPlug deliberately ignores. The full comparison table is in
[phase4c_literature.md](phase4c_literature.md).

### 3.3 Authentication ablation

The `forgery` fault assumes the simulator (or a protocol variant) does
not verify sender identity cryptographically. Castro & Liskov (1999,
§3) require authenticated messages; we therefore frame forgery as an
**authentication-ablation** experiment, not a critique of PBFT.
SIMPY_MILESTONES.md:332 records this framing as a Phase 4b pass
criterion and Phase 12.C will produce the actual ablation evidence.

---

## 4. ML-Based Fault Detection in Distributed Systems

### 4.1 Choice of model family

Three model families are evaluated in this project:

| Family | Specific model | Primary citation |
| ------ | -------------- | ---------------- |
| Tree, single | Decision Tree (CART) | Breiman et al. (1984) |
| Tree, ensemble (bagging) | Random Forest | Breiman (2001) |
| Tree, ensemble (boosting) | XGBoost | Chen & Guestrin (2016) |
| Linear | Logistic Regression | Cox (1958); Pedregosa et al. (2011) for sklearn impl |

The rationale for this exact lineup is in
[notes/phase9_design_decisions.md](phase9_design_decisions.md). Briefly:
trees are invariant under monotonic feature transforms, handle mixed
feature scales naturally, and produce inspectable feature-importance
scores that pair well with the planned Phase 12 SHAP analysis. Logistic
Regression was added in Phase 11b as a linear-baseline tier so the
report can attribute non-linear performance gains to model family
rather than to dataset over-fit.

### 4.2 Why not a neural network?

The dataset is 1200 rows × 11 features. Deep models (e.g. BiLSTM,
which appears as an empty stub at [ml/models/bilstm.py](../ml/models/bilstm.py))
would be both data-starved and harder to interpret on this scale. We
follow standard practice (Pedregosa et al., 2011) of selecting model
complexity to dataset size, and reserve sequence-aware models as a
future-work item.

### 4.3 Comparable work

The closest analog in published research is Kitsune (Mirsky et al.,
2018), an unsupervised ensemble of autoencoders for online network
intrusion detection. We do not adopt Kitsune's method (we are
supervised, batch, and consensus-protocol-specific), but we adopt its
**comparison-table style**: rule-based and ML detectors evaluated on
the same test set with the same metrics. Phase 10 follows this
convention exactly.

"ai-bft-consensus" is mentioned in SIMPY_MILESTONES.md:43 as a
possible inspiration for ML + BFT integration ideas. We have been
unable to locate a verifiable canonical repository for this name, and
therefore do not cite it in the formal bibliography. Any conceptual
overlap (e.g. node-behaviour scoring as a feature-engineering
direction) is noted here for transparency but not relied upon as a
source.

---

## 5. Baseline Comparison

This section is fully covered in
[phase10_baseline_references.md](phase10_baseline_references.md).
Summary:

- **Threshold baseline** = parametric Gaussian on
  `consensus_agreement_time` (Chandola et al., 2009).
- **Rule-based baseline** = encoding of PBFT protocol failure
  conditions (Castro & Liskov, 1999) as if/else.
- **Defence of "weak" baselines** = static thresholds remain the
  dominant deployed monitoring mechanism in industry (Beyer et al.,
  2016, Site Reliability Engineering, Ch. 6).
- **Honest disclosure** = the rule-based baseline shares threshold
  constants with the label generator by design. This is stated openly
  so the comparison is not read as cheating; the ML advantage measures
  *learned multi-feature interactions* against the strongest static
  detector a protocol engineer could plausibly write by hand.

---

## 6. Ablation and Robustness Study Design

### 6.1 What kind of ablations does this project run?

Four planned in Phase 12:

| Ablation | Compared against |
| -------- | ---------------- |
| Feature set: 11 vs 13 features | each other (12.A) |
| Train-set: main vs main+extended | OOD performance on extended (12.B) |
| Fault realism: Phase 4 vs Phase 4c modes | each other (12.B, OOD slice) |
| Authentication: forgery intensity {0.2, 0.5, 1.0} | each other (12.C) |
| Round validation: strict vs relaxed | each other (12.D) |

### 6.2 Methodological references

- **OOD evaluation framing** — ByzFL (González et al., 2025), the
  research framework cited throughout SIMPY_MILESTONES as the reference
  for configurable Byzantine attack experiments, reports per-attack F1
  degradation on attacks that were *not* in the training distribution.
  Phase 12.B follows the same pattern.
- **Multi-seed reporting with std** — we adopt the convention of
  reporting mean ± std across ≥5 seeds, which is the minimum required
  for a defensible confidence claim on a 1200-row dataset (see
  [phase11.md](phase11.md) for why this matters in practice — the
  Phase 9 single-seed point estimate was misleading).
- **Cross-validation choice** — `StratifiedKFold(n_splits=5)` with
  `GridSearchCV` is the scikit-learn default for moderate-class
  imbalance classification (Pedregosa et al., 2011, scikit-learn user
  guide §3.1).
- **Feature-importance interpretation** — SHAP (Lundberg & Lee, 2017)
  is the reference attribution method for tree-ensemble models.
  Phase 12.A will produce SHAP plots; we cite the original paper rather
  than the Python implementation so the report is library-agnostic.

### 6.3 What this project does NOT claim

- **No formal safety/liveness proof** — we are an empirical study of a
  monitoring system, not a protocol-verification project.
- **No real-network validation** — out of scope, deliberately. The
  honesty disclosure in
  [byzantine_realism.md](byzantine_realism.md) covers this.

---

## 7. References (Harvard, ready to paste into Bibliography)

```
Banks, J., Carson, J.S. and Nelson, B.L. (1996) Discrete-event system
simulation. 2nd edn. Upper Saddle River, NJ: Prentice Hall.

Beyer, B., Jones, C., Petoff, J. and Murphy, N.R. (2016)
Site reliability engineering: how Google runs production systems.
Sebastopol, CA: O'Reilly Media.

Breiman, L. (2001) 'Random forests', Machine Learning, 45(1),
pp. 5-32. doi: 10.1023/A:1010933404324.

Breiman, L., Friedman, J.H., Olshen, R.A. and Stone, C.J. (1984)
Classification and regression trees. Belmont, CA: Wadsworth.

Castro, M. and Liskov, B. (1999)
'Practical Byzantine fault tolerance',
in Proceedings of the Third Symposium on Operating Systems Design
and Implementation (OSDI '99). New Orleans, LA: USENIX Association,
pp. 173-186.

Chandola, V., Banerjee, A. and Kumar, V. (2009)
'Anomaly detection: a survey',
ACM Computing Surveys, 41(3), Article 15.
doi: 10.1145/1541880.1541882.

Chen, T. and Guestrin, C. (2016)
'XGBoost: a scalable tree boosting system',
in Proceedings of the 22nd ACM SIGKDD International Conference on
Knowledge Discovery and Data Mining (KDD '16). San Francisco, CA:
ACM, pp. 785-794. doi: 10.1145/2939672.2939785.

Cox, D.R. (1958) 'The regression analysis of binary sequences',
Journal of the Royal Statistical Society. Series B (Methodological),
20(2), pp. 215-242.

Gonzalez, M., Guerraoui, R., Pinot, R., Rizk, G., Stephan, J. and
Taiani, F. (2025) 'ByzFL: research framework for robust federated
learning', arXiv. Available at: https://arxiv.org/abs/2505.24802
(Accessed: 29 June 2026).

Hyperledger Caliper contributors (no date) Hyperledger Caliper
documentation. Available at:
https://hyperledger-caliper.github.io/caliper/ (Accessed: 29 June
2026).

Lundberg, S.M. and Lee, S.-I. (2017)
'A unified approach to interpreting model predictions',
in Advances in Neural Information Processing Systems 30 (NeurIPS
2017). Long Beach, CA: Curran Associates, pp. 4765-4774.

Mastromauro, L., Andrade, D.S., Ozmen, M.O. and Kinsy, M.A. (2025)
'Survey of attacks and defenses on consensus algorithms for secure
data replication in distributed systems',
IEEE Access, 13, pp. 143631-143667.

Matloff, N. (2008) Introduction to discrete-event simulation and
the SimPy language. Davis, CA: University of California, Davis.
(Tutorial accompanying the SimPy library.)

Mirsky, Y., Doitshman, T., Elovici, Y. and Shabtai, A. (2018)
'Kitsune: an ensemble of autoencoders for online network intrusion
detection', in Proceedings of the Network and Distributed System
Security Symposium (NDSS 2018). San Diego, CA: Internet Society.

Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B.,
Grisel, O., Blondel, M., Prettenhofer, P., Weiss, R., Dubourg, V.,
Vanderplas, J., Passos, A., Cournapeau, D., Brucher, M., Perrot, M.
and Duchesnay, E. (2011) 'Scikit-learn: machine learning in Python',
Journal of Machine Learning Research, 12, pp. 2825-2830.

Rocha, R.M.A. (2024) ByzPlug: reliability testing of BFT systems.
MSc dissertation, Instituto Superior Tecnico, Universidade de Lisboa.

Sukhwani, H., Martinez, J.M., Chang, X., Trivedi, K.S. and Rindos, A.
(2017) 'Performance modeling of PBFT consensus process for permissioned
blockchain network (Hyperledger Fabric)', in Proceedings of the 36th
IEEE Symposium on Reliable Distributed Systems (SRDS 2017). Hong Kong,
China: IEEE, pp. 253-255.

Wang, P.-L., Chao, T.-W., Wu, C.-C. and Hsiao, H.-C. (2022) 'Tool: an
efficient and flexible simulator for Byzantine fault-tolerant
protocols', 2022 52nd Annual IEEE/IFIP International Conference on
Dependable Systems and Networks (DSN). Available at:
https://ieeexplore.ieee.org/document/9833775 (Accessed: 29 June 2026).

Xing, J., Fischer, D., Labh, N., Piersma, R., Lee, B.C., Xia, Y.A.,
Sahai, T. and Tarokh, V. (2021) 'Talaria: a framework for simulation
of permissioned blockchains for logistics and beyond', arXiv.
Available at: https://arxiv.org/abs/2103.02260 (Accessed: 29 June
2026).
```

Verify each entry against the official source before final submission —
DOIs, page numbers, and proceedings names can drift.

---

## 8. Pre-submission checklist

- [ ] Every section above has at least one citation
- [ ] Every cited work appears in §7
- [ ] §7 entries match the citation format used in the dissertation
      template (currently Harvard; switch to APA/IEEE if the
      university template requires it — `key_papers.md` will use the
      same style)
- [ ] Cross-links to the existing per-phase notes resolve
