# AFAAP Model Performance Evaluation - Findings

**Generated:** 2025-11-06 17:45:15

**Total Decisions Analyzed:** 30,000

**Number of Models Evaluated:** 3

---

This evaluation analyzes the performance of fraud detection models deployed in the AFAAP framework. Each model was tested with exactly 10,000 decisions to ensure fair comparison. The analysis focuses on two critical metrics:

- **F1 Score** (≥ 0.85): Harmonic mean of precision and recall, measuring overall classification accuracy
- **False Positive Rate** (≤ 0.01): Proportion of legitimate transactions incorrectly flagged as fraud

**Overall Results:**

- 1/3 models meet F1 score threshold (≥ 0.85)
- 1/3 models meet FPR threshold (≤ 0.01)

---

## Per-Model Performance Analysis

### fraud_detector_v1 (v1.0.0)

| Metric                  | Value  | 95% Confidence Interval | Threshold | Status  |
| ----------------------- | ------ | ----------------------- | --------- | ------- |
| **F1 Score**            | 0.9074 | [0.8887, 0.9252]        | ≥ 0.85    | ✅ PASS |
| **False Positive Rate** | 0.0057 | [0.0042, 0.0073]        | ≤ 0.01    | ✅ PASS |
| **Precision**           | 0.8989 | [0.8722, 0.9236]        | -         | -       |
| **Recall**              | 0.9160 | [0.8919, 0.9395]        | -         | -       |

**Confusion Matrix:**

```
                 Predicted
                FRAUD    LEGIT
Actual  FRAUD      480       44
        LEGIT       54     9422
```

- **True Positives (TP):** 480 - Correctly identified fraud cases
- **False Positives (FP):** 54 - Legitimate transactions incorrectly flagged
- **True Negatives (TN):** 9,422 - Correctly identified legitimate transactions
- **False Negatives (FN):** 44 - Fraud cases missed by the model

**Interpretation:**

- The F1 score of 0.9074 indicates strong overall performance with a good balance between precision and recall.
- The false positive rate of 0.0057 is acceptably low, minimizing customer friction from false fraud alerts.
- **Business Impact:** This model catches 91.6% of fraud cases while flagging 54 legitimate transactions for review.

---

### fraud_detector_v2 (v2.0.0)

| Metric                  | Value  | 95% Confidence Interval | Threshold | Status  |
| ----------------------- | ------ | ----------------------- | --------- | ------- |
| **F1 Score**            | 0.8280 | [0.8012, 0.8524]        | ≥ 0.85    | ❌ FAIL |
| **False Positive Rate** | 0.0093 | [0.0074, 0.0113]        | ≤ 0.01    | ❌ FAIL |
| **Precision**           | 0.8247 | [0.7899, 0.8571]        | -         | -       |
| **Recall**              | 0.8313 | [0.7980, 0.8639]        | -         | -       |

**Confusion Matrix:**

```
                 Predicted
                FRAUD    LEGIT
Actual  FRAUD      414       84
        LEGIT       88     9414
```

- **True Positives (TP):** 414 - Correctly identified fraud cases
- **False Positives (FP):** 88 - Legitimate transactions incorrectly flagged
- **True Negatives (TN):** 9,414 - Correctly identified legitimate transactions
- **False Negatives (FN):** 84 - Fraud cases missed by the model

**Interpretation:**

- The F1 score of 0.8280 falls below the target threshold. Low precision (0.8247) suggests many false positives. Low recall (0.8313) indicates the model is missing fraud cases.
- The false positive rate of 0.0093 exceeds the 1% threshold. This means 0.93% of legitimate transactions are incorrectly flagged, which could frustrate customers.
- **Business Impact:** This model catches 83.1% of fraud cases while flagging 88 legitimate transactions for review.

---

### fraud_detector_beta (v3.0.0)

| Metric                  | Value  | 95% Confidence Interval | Threshold | Status  |
| ----------------------- | ------ | ----------------------- | --------- | ------- |
| **F1 Score**            | 0.7658 | [0.7359, 0.7940]        | ≥ 0.85    | ❌ FAIL |
| **False Positive Rate** | 0.0155 | [0.0130, 0.0180]        | ≤ 0.01    | ❌ FAIL |
| **Precision**           | 0.7308 | [0.6939, 0.7680]        | -         | -       |
| **Recall**              | 0.8044 | [0.7692, 0.8389]        | -         | -       |

**Confusion Matrix:**

```
                 Predicted
                FRAUD    LEGIT
Actual  FRAUD      399       97
        LEGIT      147     9357
```

- **True Positives (TP):** 399 - Correctly identified fraud cases
- **False Positives (FP):** 147 - Legitimate transactions incorrectly flagged
- **True Negatives (TN):** 9,357 - Correctly identified legitimate transactions
- **False Negatives (FN):** 97 - Fraud cases missed by the model

**Interpretation:**

- The F1 score of 0.7658 falls below the target threshold. Low precision (0.7308) suggests many false positives. Low recall (0.8044) indicates the model is missing fraud cases.
- The false positive rate of 0.0155 exceeds the 1% threshold. This means 1.55% of legitimate transactions are incorrectly flagged, which could frustrate customers.
- **Business Impact:** This model catches 80.4% of fraud cases while flagging 147 legitimate transactions for review.

---

## Fairness Analysis by Transaction Type

This section examines whether the models treat different transaction types fairly by analyzing false positive rates across transaction categories.

| Transaction Type | False Positives | Total Legitimate | FPR    | Status  |
| ---------------- | --------------- | ---------------- | ------ | ------- |
| wire_transfer    | 50              | 4,090            | 0.0122 | ⚠️ WARN |
| cryptocurrency   | 47              | 4,178            | 0.0112 | ⚠️ WARN |
| mobile_payment   | 43              | 3,938            | 0.0109 | ⚠️ WARN |
| atm_withdrawal   | 46              | 4,234            | 0.0109 | ⚠️ WARN |
| ach              | 36              | 3,909            | 0.0092 | ✅ PASS |
| credit_card      | 33              | 3,973            | 0.0083 | ✅ PASS |
| check            | 34              | 4,160            | 0.0082 | ✅ PASS |

**Fairness Concerns:**

- **wire_transfer** transactions have an elevated FPR of 0.0122 (1.22%), with 50 false positives out of 4,090 legitimate transactions.
- **cryptocurrency** transactions have an elevated FPR of 0.0112 (1.12%), with 47 false positives out of 4,178 legitimate transactions.
- **mobile_payment** transactions have an elevated FPR of 0.0109 (1.09%), with 43 false positives out of 3,938 legitimate transactions.
- **atm_withdrawal** transactions have an elevated FPR of 0.0109 (1.09%), with 46 false positives out of 4,234 legitimate transactions.

These disparities may indicate model bias or need for additional feature engineering for specific transaction types.

---

## Recommendations

### Models Requiring Improvement

**fraud_detector_beta:**

- Improve F1 score from 0.7658 to ≥ 0.85
  - Focus on reducing false positives (current precision: 0.7308)
- Reduce false positive rate from 0.0155 to ≤ 0.01
  - Consider adjusting classification threshold or adding features to better distinguish legitimate transactions

**fraud_detector_v2:**

- Improve F1 score from 0.8280 to ≥ 0.85
  - Focus on reducing false positives (current precision: 0.8247)
- Reduce false positive rate from 0.0093 to ≤ 0.01
  - Consider adjusting classification threshold or adding features to better distinguish legitimate transactions

---

## CSV and Dashboard

In the same folder is a csv file and dashboard which showcase the results in a different manner.

## Methodology

**Metrics Calculated:**

- **F1 Score:** 2 × (Precision × Recall) / (Precision + Recall)
- **Precision:** TP / (TP + FP)
- **Recall:** TP / (TP + FN)
- **False Positive Rate:** FP / (FP + TN)

**Thresholds:**

- F1 Score: ≥ 0.85 (lower bound of 95% CI must exceed threshold)
- FPR: ≤ 0.01 (upper bound of 95% CI must be below threshold)

---

_Report generated by AFAAP Performance Metrics Module on 2025-11-06 at 17:45:15_
