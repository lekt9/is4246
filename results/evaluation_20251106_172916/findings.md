# AFAAP Model Performance Evaluation - Findings

**Generated:** 2025-11-06 17:29:17

**Total Decisions Analyzed:** 16,000

**Number of Models Evaluated:** 3

---

## Executive Summary

This evaluation analyzes the performance of fraud detection models deployed in the AFAAP framework. Each model was tested with exactly 10,000 decisions to ensure fair comparison. The analysis focuses on two critical metrics:

- **F1 Score** (≥ 0.85): Harmonic mean of precision and recall, measuring overall classification accuracy
- **False Positive Rate** (≤ 0.01): Proportion of legitimate transactions incorrectly flagged as fraud

**Overall Results:**
- 0/3 models meet F1 score threshold (≥ 0.85)
- 0/3 models meet FPR threshold (≤ 0.01)

⚠️ **Some models require improvement to meet performance thresholds.**

---

## Per-Model Performance Analysis

### fraud_detector_v1 (v1.0.0)

| Metric | Value | 95% Confidence Interval | Threshold | Status |
|--------|-------|------------------------|-----------|--------|
| **F1 Score** | 0.8412 | [0.8147, 0.8657] | ≥ 0.85 | ❌ FAIL |
| **False Positive Rate** | 0.0085 | [0.0067, 0.0105] | ≤ 0.01 | ❌ FAIL |
| **Precision** | 0.8340 | [0.7996, 0.8675] | - | - |
| **Recall** | 0.8485 | [0.8151, 0.8800] | - | - |

**Confusion Matrix:**

```
                 Predicted
                FRAUD    LEGIT
Actual  FRAUD      392       70
        LEGIT       78     9064
```

- **True Positives (TP):** 392 - Correctly identified fraud cases
- **False Positives (FP):** 78 - Legitimate transactions incorrectly flagged
- **True Negatives (TN):** 9,064 - Correctly identified legitimate transactions
- **False Negatives (FN):** 70 - Fraud cases missed by the model

**Interpretation:**

- ⚠️ The F1 score of 0.8412 falls below the target threshold. Low precision (0.8340) suggests many false positives. Low recall (0.8485) indicates the model is missing fraud cases. 
- ⚠️ The false positive rate of 0.0085 exceeds the 1% threshold. This means 0.85% of legitimate transactions are incorrectly flagged, which could frustrate customers.
- 📊 **Business Impact:** This model catches 84.8% of fraud cases while flagging 78 legitimate transactions for review.

---

### fraud_detector_beta (v3.0.0)

| Metric | Value | 95% Confidence Interval | Threshold | Status |
|--------|-------|------------------------|-----------|--------|
| **F1 Score** | 0.8045 | [0.7356, 0.8636] | ≥ 0.85 | ❌ FAIL |
| **False Positive Rate** | 0.0125 | [0.0075, 0.0182] | ≤ 0.01 | ❌ FAIL |
| **Precision** | 0.7826 | [0.6966, 0.8646] | - | - |
| **Recall** | 0.8276 | [0.7429, 0.9029] | - | - |

**Confusion Matrix:**

```
                 Predicted
                FRAUD    LEGIT
Actual  FRAUD       72       15
        LEGIT       20     1574
```

- **True Positives (TP):** 72 - Correctly identified fraud cases
- **False Positives (FP):** 20 - Legitimate transactions incorrectly flagged
- **True Negatives (TN):** 1,574 - Correctly identified legitimate transactions
- **False Negatives (FN):** 15 - Fraud cases missed by the model

**Interpretation:**

- ⚠️ The F1 score of 0.8045 falls below the target threshold. Low precision (0.7826) suggests many false positives. Low recall (0.8276) indicates the model is missing fraud cases. 
- ⚠️ The false positive rate of 0.0125 exceeds the 1% threshold. This means 1.25% of legitimate transactions are incorrectly flagged, which could frustrate customers.
- 📊 **Business Impact:** This model catches 82.8% of fraud cases while flagging 20 legitimate transactions for review.

---

### fraud_detector_v2 (v2.0.0)

| Metric | Value | 95% Confidence Interval | Threshold | Status |
|--------|-------|------------------------|-----------|--------|
| **F1 Score** | 0.7984 | [0.7591, 0.8355] | ≥ 0.85 | ❌ FAIL |
| **False Positive Rate** | 0.0123 | [0.0092, 0.0156] | ≤ 0.01 | ❌ FAIL |
| **Precision** | 0.7860 | [0.7362, 0.8354] | - | - |
| **Recall** | 0.8112 | [0.7608, 0.8584] | - | - |

**Confusion Matrix:**

```
                 Predicted
                FRAUD    LEGIT
Actual  FRAUD      202       47
        LEGIT       55     4411
```

- **True Positives (TP):** 202 - Correctly identified fraud cases
- **False Positives (FP):** 55 - Legitimate transactions incorrectly flagged
- **True Negatives (TN):** 4,411 - Correctly identified legitimate transactions
- **False Negatives (FN):** 47 - Fraud cases missed by the model

**Interpretation:**

- ⚠️ The F1 score of 0.7984 falls below the target threshold. Low precision (0.7860) suggests many false positives. Low recall (0.8112) indicates the model is missing fraud cases. 
- ⚠️ The false positive rate of 0.0123 exceeds the 1% threshold. This means 1.23% of legitimate transactions are incorrectly flagged, which could frustrate customers.
- 📊 **Business Impact:** This model catches 81.1% of fraud cases while flagging 55 legitimate transactions for review.

---

## Fairness Analysis by Transaction Type

This section examines whether the models treat different transaction types fairly by analyzing false positive rates across transaction categories.

| Transaction Type | False Positives | Total Legitimate | FPR | Status |
|-----------------|----------------|------------------|-----|--------|
| wire_transfer | 29 | 2,162 | 0.0134 | ⚠️ WARN |
| ach | 26 | 2,130 | 0.0122 | ⚠️ WARN |
| cryptocurrency | 25 | 2,146 | 0.0116 | ⚠️ WARN |
| mobile_payment | 20 | 2,110 | 0.0095 | ✅ PASS |
| check | 20 | 2,260 | 0.0088 | ✅ PASS |
| credit_card | 17 | 2,194 | 0.0077 | ✅ PASS |
| atm_withdrawal | 16 | 2,200 | 0.0073 | ✅ PASS |

**⚠️ Fairness Concerns:**

- **wire_transfer** transactions have an elevated FPR of 0.0134 (1.34%), with 29 false positives out of 2,162 legitimate transactions.
- **ach** transactions have an elevated FPR of 0.0122 (1.22%), with 26 false positives out of 2,130 legitimate transactions.
- **cryptocurrency** transactions have an elevated FPR of 0.0116 (1.16%), with 25 false positives out of 2,146 legitimate transactions.

These disparities may indicate model bias or need for additional feature engineering for specific transaction types.

---

## Recommendations

### Models Requiring Improvement

**fraud_detector_beta:**
- Improve F1 score from 0.8045 to ≥ 0.85
  - Focus on reducing false positives (current precision: 0.7826)
- Reduce false positive rate from 0.0125 to ≤ 0.01
  - Consider adjusting classification threshold or adding features to better distinguish legitimate transactions

**fraud_detector_v1:**
- Improve F1 score from 0.8412 to ≥ 0.85
  - Focus on reducing false positives (current precision: 0.8340)
- Reduce false positive rate from 0.0085 to ≤ 0.01
  - Consider adjusting classification threshold or adding features to better distinguish legitimate transactions

**fraud_detector_v2:**
- Improve F1 score from 0.7984 to ≥ 0.85
  - Focus on reducing false positives (current precision: 0.7860)
- Reduce false positive rate from 0.0123 to ≤ 0.01
  - Consider adjusting classification threshold or adding features to better distinguish legitimate transactions

### General Recommendations

1. **Continuous Monitoring:** Track these metrics over time to detect model degradation
2. **A/B Testing:** Test model improvements with controlled experiments before full deployment
3. **Feature Analysis:** Investigate which features contribute most to false positives
4. **Threshold Tuning:** Experiment with classification thresholds to optimize the precision-recall trade-off
5. **Transaction Type Analysis:** Pay special attention to transaction types with elevated FPR

---

## Methodology

**Data Source:** Synthetic fraud detection dataset with ground truth labels

**Decisions per Model:** 10,000 (equal distribution for fair comparison)

**Bootstrap Confidence Intervals:** 1,000 iterations with stratified sampling to preserve class distribution

**Metrics Calculated:**
- **F1 Score:** 2 × (Precision × Recall) / (Precision + Recall)
- **Precision:** TP / (TP + FP)
- **Recall:** TP / (TP + FN)
- **False Positive Rate:** FP / (FP + TN)

**Thresholds:**
- F1 Score: ≥ 0.85 (lower bound of 95% CI must exceed threshold)
- FPR: ≤ 0.01 (upper bound of 95% CI must be below threshold)

---

*Report generated by AFAAP Performance Metrics Module on 2025-11-06 at 17:29:17*
