# Wallet Risk Scoring Model: Deliverables

This document details the methodology used to develop the wallet risk scoring model, covering data collection, feature selection, the scoring algorithm, and the justification for the risk indicators used.

## 1. Data Collection Method

The data collection process is designed to be scalable and targeted, focusing specifically on transactions interacting with the Compound protocol.

**Source:**
The primary data source is the Etherscan API, which provides comprehensive transaction histories for any given Ethereum wallet address.

**Process:**

1. **Input:**

   * A list of wallet addresses provided in a CSV file (`data/wallets.csv`).

2. **API Query:**

   * For each wallet, a script queries the Etherscan API’s `txlist` endpoint to fetch its entire transaction history.
   * Pagination logic ensures retrieval of all transactions in batches of 1,000.

3. **Filtering:**

   * Raw transaction data is filtered to isolate interactions with a predefined list of Compound V2 and V3 smart contract addresses.
   * Each transaction is tagged with its originating `wallet_address` and inferred `protocol_version` (V2 or V3).

4. **Output:**

   * Filtered transactions are saved to `data/compound_v2_transactions.csv`.
   * This CSV becomes the input for the wallet risk analysis model.

**Scalability:**

* The method supports any number of wallets by updating the input CSV.
* A `time.sleep(0.25)` between API calls respects Etherscan’s rate limits, enabling robust, large-scale execution.

---

## 2. Feature Selection Rationale

Initial feature selection transforms raw transaction records into foundational variables that capture financial, technical, and behavioral aspects:

* **value**: ETH amount transferred; indicates economic scale.
* **gas, gasPrice, gasUsed**: technical efficiency and cost; abnormal values hint at bot optimizations or misconfigurations.
* **timeStamp**: enables temporal analyses—frequency, bursts, and activity spans.
* **isError / txreceipt\_status**: failure vs. success rates; high error rates can signal probing or unsophistication.
* **functionName / methodId**: identifies the smart contract methods used; informs complexity and intent.
* **from, to, wallet\_address**: address fields underpin counterparty network analysis—flow direction and interaction scope.

Each selected raw column serves as the basis for one or more higher‑level risk indicators.

---

## 3. Scoring Method

The scoring pipeline converts wallet‑level features into a final risk score (0–1000) through four stages:

1. **Wallet-Level Feature Engineering**

   * Aggregate transaction data per wallet to compute metrics like `total_transactions`, `avg_transaction_value`, `error_rate`, `transaction_frequency`, `unique_recipients`, and `contract_complexity`.

2. **Weighted Base Score Calculation**

   * Group features into risk components (Volume, Behavioral, Technical, Temporal, Diversity).
   * Normalize each feature to a 0–1 range (MinMaxScaler).
   * Compute each component’s score as the mean of its features, multiplied by a predefined weight.
   * Sum all component scores to yield the `base_risk_score`, scaled to 0–1000.

3. **ML-Powered Score Refinement**

   * **Isolation Forest:** flags \~5% of wallets as anomalies; these receive a risk boost.
   * **K-Means Clustering:** groups wallets into behavioral clusters; cluster average risks provide an adjustment factor for each wallet.

4. **Final Score & Categorization**

   * Apply anomaly and cluster adjustments to the base score.
   * Clip scores to 0–1000 and convert to integers.
   * Map scores to qualitative categories: Very Low (<200), Low (<400), Medium (<600), High (<800), Very High (≥800).

---

## 4. Justification of the Risk Indicators Used

Each engineered feature tests a specific risk hypothesis, ensuring transparent, defensible scoring:

* **High `transaction_frequency` & `burst_ratio`:** indicative of scripted or bot activity (front‑running, spam).
* **High `error_rate`:** suggests unsophisticated operation or probing attacks.
* **High `recipient_concentration`:** repeated transfers to few addresses can signal structuring or laundering.
* **High `zero_value_ratio`:** zero‑value transactions often reflect spam, airdrop farming, or testing activity.
* **Low `contract_complexity`:** limited interaction diversity points to single‑purpose bots; extreme complexity can also warrant scrutiny.
* **High `send_receive_ratio`:** disproportionate send‑only or receive‑only behavior is a mixer/tumbler pattern.

This multi‑layered framework combines weighted components with unsupervised refinements, achieving both breadth (via core risk dimensions) and depth (via anomalies/clusters) in a scalable, tunable model.
