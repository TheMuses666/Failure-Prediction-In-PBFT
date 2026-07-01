# Phase 10 — Baseline References

Purpose: justify why the two static baselines look the way they do, and give
the citations to drop into the report when writing Chapter 6 (Baselines).

This file is a writing aid, not a literature review.

---

## 1. Threshold-based Baseline

### Method recap
- Fit `mu, sigma` of `consensus_agreement_time` on the training-set normal
  subset only (label == 0).
- Flag a test row as:
  - `failure (2)` if `timeout_frequency > 0` or value > `mu + 3*sigma`
  - `degraded (1)` if value > `mu + 2*sigma`
  - `normal (0)` otherwise
- Single feature on purpose. Deliberately weak.

### Primary citation
**Chandola, V., Banerjee, A., & Kumar, V. (2009).**
*Anomaly Detection: A Survey.* ACM Computing Surveys, 41(3), Article 15.

- Section 4 ("Statistical Anomaly Detection Techniques") defines the
  parametric Gaussian model: anything outside `mu +/- k*sigma` is anomalous.
- This is the canonical citation for the `mu + 2*sigma` rule.
- Report sentence:
  > "We adopt a parametric Gaussian threshold (Chandola et al., 2009),
  > fitting mu and sigma on the training-set normal subset and flagging
  > any test sample exceeding mu + 2*sigma as anomalous."

### Secondary citation (justifies the "deliberately simple" framing)
**Beyer, B., Jones, C., Petoff, J., & Murphy, N. R. (2016).**
*Site Reliability Engineering: How Google Runs Production Systems.* O'Reilly.
Chapter 6, "Monitoring Distributed Systems".

- Documents that production monitoring is dominated by static thresholds and
  simple percentile rules, not ML.
- Use this to defend the baseline against the question
  "why didn't you use a smarter statistical method?":
  > "We follow standard SRE practice (Beyer et al., 2016), where static
  > thresholds remain the dominant deployed monitoring mechanism."

---

## 2. Rule-based Baseline

### Method recap
- No fitting. Pure if/else over multiple features.
- Thresholds are read from `config.py`, not invented:
  - `NORMAL_LATENCY_THRESHOLD_MAX = 50`
  - `DEGRADED_LATENCY_THRESHOLD_MAX = 150`
  - `DROP_RATE_WARNING = 0.3`
  - `MESSAGE_CONSISTENCY_WARNING = 0.8`
  - quorum >= `2f + 1` => `voting_consistency >= 5/7 ~= 0.71`
- Uses: `timeout_frequency`, `voting_consistency`, `message_drop_rate`,
  `consensus_agreement_time`, `message_consistency`.

### Primary citation
**Castro, M., & Liskov, B. (1999).**
*Practical Byzantine Fault Tolerance.* In Proceedings of OSDI 1999.

- The original PBFT paper. Already cited elsewhere in the report.
- Defines the protocol-level failure conditions: commit-quorum failure,
  timeout, view change.
- The rule-based baseline is *literally* an encoding of these conditions
  as a classifier.
- Report sentence:
  > "Our rule-based baseline encodes the failure conditions specified by
  > the PBFT protocol itself (Castro & Liskov, 1999) - insufficient commit
  > quorum (< 2f+1), consensus timeout, and message inconsistency - as
  > deterministic if/else rules."

### Honest disclosure to include in the report
The rule-based detector and the label generator share several threshold
constants (drop rate 0.3, latency 50/150 ms). This is intentional and must
be stated explicitly in Chapter 6, so the comparison is read correctly:

> "The rule-based baseline shares threshold constants with the label
> generator. This is by design: both encode the same PBFT specification.
> The baseline therefore represents the strongest static detector that a
> protocol engineer could plausibly write by hand, and any ML advantage
> over it reflects the value of *learned multi-feature interactions* rather
> than tighter threshold tuning."

This sentence pre-empts the reviewer question "isn't the rule-based baseline
just cheating by reusing your labels?".

---

## 3. Experimental Comparison Structure

### Reference for table layout
**Mirsky, Y., Doitshman, T., Elovici, Y., & Shabtai, A. (2018).**
*Kitsune: An Ensemble of Autoencoders for Online Network Intrusion Detection.*
NDSS 2018.

- Not cited for method. Cited for the comparison-table style:
  rule-based IDS (Snort) and ML detectors evaluated on the same test set
  with the same metrics.
- Mirrors Phase 10's pass criterion: "ML and baseline results are directly
  comparable" (SIMPY_MILESTONES.md:941).

---

## 4. Supporting Citations (optional, only if space allows)

### To justify the Gaussian assumption for normal-round latency
**Sukhwani, H., Martinez, J. M., Chang, X., Trivedi, K. S., & Rindos, A. (2017).**
*Performance Modeling of PBFT Consensus Process for Permissioned Blockchain
Network (Hyperledger Fabric).* In Proceedings of SRDS 2017.

- Provides empirical latency distributions for PBFT-like consensus.
- Use only if a reviewer pushes back on `mu + 2*sigma` assuming normality.

### To justify the threshold choices being "industry-realistic"
*Hyperledger Caliper* documentation (https://hyperledger.github.io/caliper/).

- Standard benchmarking tool for permissioned blockchains.
- Defines latency / drop-rate alert conventions used in practice.
- Web reference, not a paper. Cite only if needed in the discussion.

---

## 5. What I Deliberately Did NOT Cite

These came up while searching and were rejected on purpose:

- **PyOD, scikit-multiflow, scikit-learn IsolationForest**: these are
  ML methods (learn a decision boundary). Using them as the "static" baseline
  would blur the static-vs-ML contrast that the whole comparison rests on.
- **EWMA / CUSUM adaptive thresholds**: more sophisticated than `mu + 2*sigma`
  but still single-feature. Would only narrow the ML advantage without
  changing the qualitative conclusion. Not worth the implementation cost.
- **Generic GitHub "anomaly_detection.py" scripts**: format mismatch with
  this project's feature schema; would cost more time to adapt than to
  write 30 lines locally.

If the ML-vs-baseline gap turns out to be implausibly large (F1 difference
> 0.4), revisit EWMA as a stronger baseline before re-running experiments.

---

## 6. Citation Block (Harvard, ready to paste)

```
Beyer, B., Jones, C., Petoff, J. and Murphy, N.R. (2016)
Site reliability engineering: how Google runs production systems.
Sebastopol, CA: O'Reilly Media.

Castro, M. and Liskov, B. (1999)
'Practical Byzantine fault tolerance',
in Proceedings of the Third Symposium on Operating Systems Design
and Implementation (OSDI '99). New Orleans, LA: USENIX Association,
pp. 173-186.

Chandola, V., Banerjee, A. and Kumar, V. (2009)
'Anomaly detection: a survey',
ACM Computing Surveys, 41(3), Article 15.
doi: 10.1145/1541880.1541882.

Mirsky, Y., Doitshman, T., Elovici, Y. and Shabtai, A. (2018)
'Kitsune: an ensemble of autoencoders for online network intrusion
detection', in Proceedings of the Network and Distributed System
Security Symposium (NDSS 2018). San Diego, CA: Internet Society.

Sukhwani, H., Martinez, J.M., Chang, X., Trivedi, K.S. and Rindos, A.
(2017) 'Performance modeling of PBFT consensus process for permissioned
blockchain network (Hyperledger Fabric)', in Proceedings of the 36th
IEEE Symposium on Reliable Distributed Systems (SRDS 2017). Hong Kong,
China: IEEE, pp. 253-255.
```

Verify each entry against the official source before submission - DOIs,
page numbers, and proceedings names can drift.
