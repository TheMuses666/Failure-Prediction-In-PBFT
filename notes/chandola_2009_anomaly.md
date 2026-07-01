# Chandola, Banerjee & Kumar (2009) — Anomaly Detection: A Survey

## Citation
Chandola, V., Banerjee, A. and Kumar, V. (2009) 'Anomaly detection:
a survey', ACM Computing Surveys, 41(3), Article 15.
doi: 10.1145/1541880.1541882.

DOI link: http://doi.acm.org/10.1145/1541880.1541882

## What it is (one sentence)
The most widely cited survey of anomaly detection (3,000+ citations
on Google Scholar), organising the field into six technique families
(classification, nearest-neighbour, clustering, statistical,
information-theoretic, spectral) and three anomaly types (point,
contextual, collective).

## Why we cite it (one sentence)
To justify our threshold-based static baseline: §7.1.1
explicitly defines the μ ± 3σ Gaussian outlier rule that our
`baseline/static_detection.py` implements verbatim.

---

## Key takeaways for our dissertation

### Takeaway 1 — The μ ± 3σ Gaussian rule is canonical (§7.1.1, p. 30)

This is **the single most important sentence in the paper** for our
Phase 10 threshold baseline. Direct quote:

> "A simple outlier technique, often used in process quality control
> domain [Shewhart 1931], is to declare all data instances that are
> more than 3σ distance away from the distribution mean μ, where σ
> is the standard deviation for the distribution. The μ ± 3σ region
> contains 99.7% of the data instances." (Chandola et al. 2009, §7.1.1,
> p. 30)

Implication for us: our `baseline/static_detection.py` uses `μ ± 2σ`
(degraded) and `μ ± 3σ` (failure) on `consensus_agreement_time`,
which is the textbook implementation Chandola attributes to Shewhart
(1931) — a 90-year-old canonical method. **This citation single-handedly
defends our threshold baseline against any "this is too simplistic"
critique**: it is simple by design, and the design is industry-standard.

### Takeaway 2 — Anomaly type taxonomy (§2.2, pp. 7-9)

Chandola defines three anomaly types:

| Anomaly type | Definition | Our project |
| ------------ | ---------- | ----------- |
| **Point** (§2.2.1) | "an individual data instance can be considered as anomalous with respect to the rest of data" (p. 7) | ✅ **This is our setting** — each PBFT round is one independent data instance, labelled normal/degraded/failure |
| **Contextual** (§2.2.2) | anomalous only in a specific context (e.g. temperature normal in summer, anomalous in winter) | Not our setting — we don't have temporal context |
| **Collective** (§2.2.3) | a collection of related instances anomalous together (e.g. EKG arrhythmia) | Not our setting — rounds are i.i.d. by design |

**Why this matters:** explicitly stating "our dataset is a point
anomaly detection problem" in the Methodology chapter pre-empts the
reviewer question "should you be doing sequence/temporal modelling?"
Answer: no, because rounds are designed to be independent.

### Takeaway 3 — Supervised mode is our setting (§2.3.1, p. 10)

Direct quote:

> "Techniques trained in supervised mode assume the availability of a
> training data set that has labeled instances for normal as well as
> anomaly classes. A typical approach in such cases is to build a
> predictive model for normal vs. anomaly classes." (Chandola et al.
> 2009, §2.3.1, p. 10)

Implication for us: we generate ground-truth labels from simulator
state (Phase 6), so we operate in **supervised mode**. This is
relevant because most anomaly-detection methods in §4–§9 assume
semi-supervised or unsupervised — we deliberately picked the
supervised setting and should justify it.

Class-imbalance flag from Chandola (§2.3.1, p. 10):
> "the anomalous instances are far fewer compared to the normal
> instances in the training data. Issues that arise due to imbalanced
> class distributions have been addressed in [...references...]"

This validates our use of `class_weight='balanced'` (Phase 11) as a
documented response to a well-known anomaly-detection issue.

### Takeaway 4 — Labels output, not scores (§2.4.2, p. 10)

Chandola distinguishes two output modes:

- **Scores** (§2.4.1): continuous anomaly score, analyst applies cutoff
- **Labels** (§2.4.2): "assign a label (normal or anomalous) to each test instance" (p. 10)

Implication for us: our models (DT, RF, XGB, LR) all output
**labels** directly (three-class). The threshold baseline outputs
**scores → labels via μ ± kσ cutoff**. Both modes co-exist in our
evaluation, which is consistent with §2.4 treating them as equivalent
methodological choices.

### Takeaway 5 — Advantages of statistical techniques (§7, p. 35)

Direct quote (three advantages of statistical anomaly detection):

> "(1) If the assumptions regarding the underlying data distribution
> hold true, statistical techniques provide a statistically justifiable
> solution for anomaly detection.
> (2) The anomaly score provided by a statistical technique is
> associated with a confidence interval, which can be used as
> additional information while making a decision regarding any test
> instance.
> (3) If the distribution estimation step is robust to anomalies in
> data, statistical techniques can operate in a unsupervised setting
> without any need for labeled training data." (Chandola et al. 2009,
> §7, p. 35)

Implication: advantage (1) is **exactly the rationale** for our
threshold baseline — fitting μ, σ on the *normal-subset only* during
training ensures the Gaussian assumption is checked on normal data.
Advantage (2) is why we report confidence intervals (multi-seed
mean ± std) in Phase 11.

### Takeaway 6 — Disadvantages of statistical techniques (§7, p. 35) — limitation framing

Direct quote (the three disadvantages — **gold for our Discussion chapter**):

> "(1) The key disadvantage of statistical techniques is that they
> rely on the assumption that the data is generated from a particular
> distribution. This assumption often does not hold true, especially
> for high dimensional real data sets.
> (2) Even when the statistical assumption can be reasonably
> justified, there are several hypothesis test statistics that can be
> applied to detect anomalies; choosing the best statistic is often
> not a straightforward task [Motulsky 1995].
> (3) Histogram-based techniques are relatively simple to implement,
> but a key shortcoming of such techniques for multivariate data is
> that they are not able to capture the interactions between different
> attributes." (Chandola et al. 2009, §7, p. 35)

Implication: disadvantages (1) and (3) **directly motivate why we
need ML models in addition to the threshold baseline** — Gaussian
assumption is fragile for high-D data (11 features), and the baseline
is single-feature so cannot capture multi-feature interactions. The
ML-vs-baseline gap measures exactly the value Chandola predicts is
needed.

### Takeaway 7 — Statistical vs classification trade-off (§11, p. 43)

Direct quote:

> "Statistical techniques, though unsupervised, are effective only
> when the dimensionality of data is low and statistical assumptions
> hold." (Chandola et al. 2009, §11, p. 43)

> "Classification-based techniques can be a better choice in such
> scenario. But to be most effective, classification-based techniques
> require labels for both normal and anomalous instances, which are
> not often available." (Chandola et al. 2009, §11, p. 43)

Implication: this is the **theoretical justification for our
methodology**. We have:
- Statistical baseline → simple, low-dimensional (single-feature)
- Classification ML models → multi-dimensional (11 features), requires labels (which we generate from simulator)

The whole project sits exactly where Chandola §11 says classification
becomes preferable, and we can quote this directly.

---

## Mapping to our project

| Survey concept (§, p.) | Our implementation |
| ---------------------- | ------------------ |
| Gaussian μ ± 3σ rule (§7.1.1, p. 30) | `baseline/static_detection.py` threshold baseline |
| Box plot rule (1.5 × IQR) (§7.1.1, p. 30) | Alternative not chosen — Gaussian is sufficient |
| Point anomaly (§2.2.1, p. 7) | Per-round labels, no cross-round dependency |
| Supervised mode (§2.3.1, p. 10) | Labels generated from simulator state in Phase 6 |
| Class imbalance addressed (§2.3.1, p. 10) | `class_weight='balanced'` in Phase 11 |
| Label output (§2.4.2, p. 10) | All our models output Normal/Degraded/Failure labels |
| Classification-based techniques (§4) | Decision Tree, Random Forest, XGBoost, LR |
| Statistical techniques (§7) | Threshold baseline |
| Multi-feature interactions limitation (§7, p. 35, disadvantage 3) | Why we need ML over single-feature threshold |

---

## Suggested citation patterns for the dissertation

### For Phase 10 threshold baseline (Methodology / Chapter 6)
> "Our threshold-based static baseline implements the canonical
> Gaussian outlier rule attributed to Shewhart (1931) and codified by
> Chandola et al. (2009, §7.1.1, p. 30): instances more than k
> standard deviations from the fitted mean are flagged as anomalous.
> We fit μ and σ on the training-set normal subset only and use k = 2
> (degraded) and k = 3 (failure) on `consensus_agreement_time`."

### For defending the choice of point-anomaly framing
> "We treat each PBFT round as an independent data instance,
> corresponding to Chandola et al.'s (2009, §2.2.1, p. 7) point
> anomaly setting. Contextual and collective anomalies would require
> cross-round dependency modelling, which is out of scope for this
> dissertation."

### For motivating the ML over the baseline (Methodology / Discussion)
> "Chandola et al. (2009, §7, p. 35) note that statistical anomaly
> detection 'relies on the assumption that the data is generated from
> a particular distribution. This assumption often does not hold true,
> especially for high dimensional real data sets', and that
> single-feature histogram and threshold techniques 'are not able to
> capture the interactions between different attributes'. Our ML
> models address both limitations: they accept the full 11-dimensional
> feature vector and learn non-linear feature interactions directly
> from data."

### For justifying class_weight='balanced'
> "We apply `class_weight='balanced'` during training (Phase 11).
> Class imbalance is a documented challenge in supervised anomaly
> detection (Chandola et al. 2009, §2.3.1, p. 10), and balancing
> sample weights at training time is the standard scikit-learn
> response to this issue."

### For the methodology positioning (Chapter 3 framing)
> "Our methodology sits at the intersection of two technique families
> identified by Chandola et al. (2009): a statistical baseline (§7)
> for the low-dimensional reference point, and classification-based
> ML models (§4) for the high-dimensional learned detector. This
> matches Chandola et al.'s (2009, §11, p. 43) conclusion that
> 'classification-based techniques can be a better choice' than
> statistical techniques when data are high-dimensional and labels
> are available — both conditions hold in our dataset."

---

## Cross-references to existing notes

- [phase10_baseline_references.md §1](phase10_baseline_references.md)
  — original brief mention citing Chandola for the Gaussian rule
- [literature_review.md §5](literature_review.md) — Chandola listed
  as primary citation for the baseline section
- [key_papers.md §7](key_papers.md) — Chandola mapped to threshold
  baseline implementation

This summary file deepens those mentions into a full
Methodology-chapter reference, with direct page-numbered quotes and
explicit limitation framing for the Discussion chapter.

---

## Pages I actually read
- Pages 1-10 (§1 Introduction, §2 Different Aspects — anomaly types,
  data labels, output)
- Pages 30-45 (§7 Statistical Techniques in full, §8 Information
  Theoretic, §9 Spectral, §10 Contextual, §11 Strengths/Weaknesses,
  §12 Conclusion)

## Pages I deliberately did not read
- Pages 11-29 (§3 Applications, §4 Classification-Based, §5
  Nearest-Neighbour, §6 Clustering-Based) — applications section is
  not relevant to a methodology citation; §4 (classification) is
  covered more directly by the model-specific papers (Breiman 2001,
  Chen & Guestrin 2016); §5 and §6 describe methods we do not use.
- Pages 46-58 (rest of References) — bibliography lookup only,
  consult if a secondary citation is needed.

## Open questions / things to verify before submission

1. **Page numbering**: Chandola uses "15:30" style page numbers
   (article 15, page 30 of the article). The dissertation might cite
   as either `p. 30` (article-internal) or the journal's continuous
   pagination. Verify with the dissertation template.
2. **`k=2` vs `k=3` choice**: our baseline uses k=2 for Degraded
   and k=3 for Failure. Chandola only documents k=3 (99.7%). The
   k=2 choice (95%) is a project decision, not from Chandola — make
   sure the Methodology chapter explains this is *our* extension to
   the canonical rule, not Chandola's.
3. **Shewhart 1931 secondary cite**: Chandola attributes the 3σ rule
   to Shewhart 1931. If the dissertation wants a historical primary
   citation as well, add Shewhart's *Economic Control of Quality of
   Manufactured Product* (1931, D. Van Nostrand) to the bibliography.
   For most theses, citing Chandola is sufficient.
