# Wallet Risk Scoring Model: Deliverables

This document details the methodology used to develop the wallet risk scoring model, covering data collection, feature selection, the scoring algorithm, and the justification for the risk indicators used.

## 1. Data Collection Method

The data collection process is designed to be scalable and targeted, focusing specifically on transactions interacting with the Compound protocol.

**Source:**
The primary data source is the Etherscan API, which provides comprehensive transaction histories for any given Ethereum wallet address.

**Process:**

1. **Input:** A list of wallet addresses provided in a CSV file (`data/wallets.csv`).
2. **API Query:** For each wallet, a script queries the Etherscan API’s `txlist` endpoint to fetch its entire transaction history. Pagination logic ensures all transactions are retrieved in batches of 1,000.
3. **Filtering:** Raw transaction data is filtered to isolate interactions with a predefined list of Compound V2 and V3 smart contract addresses. Each transaction is tagged with its originating `wallet_address` and inferred `protocol_version` (V2 or V3).
4. **Output:** Filtered transactions are saved to `data/compound_v2_transactions.csv`, serving as the input for the risk analysis model.

**Scalability:**

* Can process any number of wallets by updating the input CSV.
* Includes `time.sleep(0.25)` between API calls to respect Etherscan’s rate limits, enabling robust execution over large datasets.

## 2. Feature Selection Rationale

The feature selection strategy captures a multi-faceted, holistic profile of each wallet from raw on-chain data. Selected features are grouped into logical categories:

* **Financial Indicators (`value`):** Measures transaction amounts to distinguish between high-value (whale) wallets and low-value (spam/testing) wallets. Basis for metrics like `total_value_sent`, `avg_transaction_value`, and `zero_value_ratio`.
* **Technical & Efficiency Indicators (`gas`, `gasPrice`, `gasUsed`, `isError`):**

  * **Gas Metrics:** High or erratic values signal bot behavior or inefficiency.
  * **Error Rate:** High failure rates indicate unsophisticated bots, misconfigured contracts, or probing attacks.
* **Temporal Indicators (`timeStamp`):** Enables calculation of `transaction_frequency`, detection of dormancy and burst patterns, and differentiation between human and programmatic activity.
* **Interaction & Counterparty Indicators (`from`, `to`, `functionName`):**

  * **Flow Analysis:** `from`/`to` fields map fund flows, informing metrics like `unique_recipients` and `send_receive_ratio`.
  * **Function Analysis:** `functionName` captures interaction complexity, forming the basis for `contract_complexity`.

## 3. Scoring Method

A multi-stage pipeline transforms raw transaction data into a final risk score (0–1000):

1. **Wallet-Level Feature Engineering:** Aggregate transaction data per wallet to compute features like `total_transactions`, `avg_transaction_value`, `error_rate`, `transaction_frequency`, `unique_recipients`, and `contract_complexity`.

2. **Weighted Base Score Calculation:**

   * Group features into risk components (Volume, Behavioral, Technical, Temporal, Diversity).
   * Normalize features to 0–1 (MinMaxScaler).
   * Compute each component’s score (mean of its features × predefined weight).
   * Sum component scores for `base_risk_score` (scaled to 0–1000).

3. **ML-Powered Score Refinement:**

   * **Isolation Forest:** Flags \~5% of wallets as anomalies; flagged wallets receive a risk boost.
   * **K-Means Clustering:** Groups wallets into behavioral clusters; cluster average risk provides an adjustment factor.

4. **Final Score & Categorization:**

   * Apply anomaly and cluster adjustments.
   * Clip scores to 0–1000 and convert to integers.
   * Map to qualitative categories: Very Low (<200), Low (<400), Medium (<600), High (<800), Very High (≥800).

## 4. Justification of the Risk Indicators Used

Each engineered feature tests a specific risk hypothesis:

* **High `transaction_frequency` & `burst_ratio`:** Indicative of automated or bot activity (front-running, spamming).
* **High `error_rate`:** Suggests unsophisticated users, misconfigured bots, or probing attacks.
* **High `recipient_concentration`:** Repeated transfers to few addresses signal structuring or laundering.
* **High `zero_value_ratio`:** Zero-value transactions often indicate spam, airdrop farming, or testing activities.
* **Low `contract_complexity`:** Limited function diversity points to simple bots; extreme complexity can also be risky.
* **High `send_receive_ratio`:** Disproportionate send-only or receive-only behavior can indicate mixer/tumbler services.

This framework combines core risk dimensions with anomaly detection and clustering, ensuring a transparent, scalable, and tunable scoring model.
