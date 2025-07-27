# On-Chain Wallet Risk Scoring Model for Compound Protocol

## Project Overview

This project provides a comprehensive framework for analyzing and scoring the risk profiles of Ethereum wallets interacting with the Compound V2 and V3 protocols. Using a multi-stage approach that combines expert-driven feature engineering with unsupervised machine learning, the model assigns a risk score from **0 to 1000** to each wallet, helping to identify potentially anomalous or high-risk actors within the ecosystem.

---

## How to Use This Project

### 1. Methodology & Final Output

* **Methodology:** For detailed explanations of the Data Collection method, Feature Selection rationale, Scoring Method, and Risk Indicator justifications, see `deliverables.md`.
* **Final Scores:** The analysis produces `wallet_risk_scores.csv`, containing two columns: `wallet_id` and its corresponding `score`.

### 2. Scalable File Structure


**Key Scalability Feature:**
All core data processing and modeling functions are centralized in `scripts/risk_utils.py`. This modular design allows notebooks (`MODEL.ipynb`, `VISUALISATIONS.ipynb`, etc.) to import and use a single, tested codebase—avoiding duplication and easing maintenance.

```
.
├── data/
│   ├── compound_v2_v3_transactions.csv  # Raw data fetched from Etherscan
│   └── wallets.csv                      # Input list of wallet addresses
├── scripts/
│   ├── collect_data.py                  # Fetches and filters Etherscan data
│   └── risk_utils.py                    # Core functions for feature engineering & scoring
├── .env                                 # API keys and environment variables
├── deliverables.md                      # Detailed methodology document
├── EDA.ipynb                            # Exploratory Data Analysis notebook
├── MODEL.ipynb                          # Main notebook to run the risk model
├── VISUALISATIONS.ipynb                 # Notebook for plotting results
├── README.md                            # Project overview and instructions (this file)
└── wallet_risk_scores.csv               # Final output with wallet risk scores
```


---

## 3. Mathematical Logic

Detailed mathematical formulas and algorithmic logic are documented directly in markdown cells within `MODEL.ipynb`. You will find step-by-step breakdowns for:

* Feature engineering formulas
* Normalization and weighting schemes
* Base score aggregation
* Anomaly detection and cluster-based adjustments

---

## 4. Running the Analysis

### Data Collection

1. **Configure**: Add your Etherscan API key to the `.env` file:

   ```text
   ETHERSCAN_API_KEY=your_api_key_here
   ```
2. **Prepare Wallet List**: Update `data/wallets.csv` with the `wallet_id` column containing addresses to analyze.
3. **Fetch Data**:

   ```bash
   python scripts/collect_data.py
   ```

### Exploratory Data Analysis

* Open and run `EDA.ipynb` to inspect raw and cleaned data, distributions, and initial insights.

### Run Risk Model

* Open and execute all cells in `MODEL.ipynb`. This will process features, calculate scores, and output `wallet_risk_scores.csv`.

### Visualize Results

* Open and run `VISUALISATIONS.ipynb` to generate charts on risk score distributions, feature importance, anomaly clusters, and more.

---

## Contributing & Extension

* **Adding Features:** Extend `scripts/risk_utils.py` with new feature functions. All notebooks automatically pick up new columns.
* **Tuning Weights:** Adjust component weights or anomaly thresholds directly in `scripts/risk_utils.py`.
* **Parallel Execution:** For large wallet lists, wrap `collect_data.py` calls in a job scheduler or multiprocessing script.

---

*This project structure and documentation ensure clarity, reusability, and scalability for wallet risk analysis on Compound.*
