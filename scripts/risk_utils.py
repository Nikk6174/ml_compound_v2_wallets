# risk_utils.py
# This file contains the core data processing and risk scoring functions
# for the wallet analysis project.

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest

def load_and_preprocess_data(filepath):
    """Loads and performs basic cleaning and type conversion."""
    try:
        df = pd.read_csv(filepath)
        print(f"Successfully loaded {filepath}")
    except FileNotFoundError:
        print(f"Error: {filepath} not found.")
        return pd.DataFrame()

    relevant_columns = ['from', 'to', 'value', 'gas', 'gasPrice', 'gasUsed',
                        'timeStamp', 'isError', 'txreceipt_status', 'functionName',
                        'wallet_address', 'protocol_version', 'methodId', 'blockNumber']
    existing_columns = [col for col in relevant_columns if col in df.columns]
    df_clean = df[existing_columns].copy()

    # Perform conversions and cleaning
    if 'timeStamp' in df_clean.columns:
        df_clean['timeStamp'] = pd.to_datetime(df_clean['timeStamp'], unit='s')
    if 'value' in df_clean.columns:
        df_clean['value'] = pd.to_numeric(df_clean['value'], errors='coerce')
    for col in ['functionName', 'protocol_version']:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].fillna('unknown')
    if 'methodId' in df_clean.columns:
        df_clean['methodId'] = df_clean['methodId'].fillna('0x00000000')
    for col in ['gas', 'gasPrice', 'gasUsed', 'blockNumber']:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
    df_clean.dropna(subset=['value'], inplace=True)
    return df_clean

def create_advanced_wallet_features(df):
    """Create comprehensive wallet-level features for risk assessment."""
    wallet_features_list = []
    wallet_col = 'wallet_address' if 'wallet_address' in df.columns and df['wallet_address'].notna().any() else 'from'
    all_wallets = df[wallet_col].dropna().unique()

    print(f"Processing features for {len(all_wallets)} wallets using '{wallet_col}' as identifier...")
    for i, wallet in enumerate(all_wallets):
        if i > 0 and i % 2000 == 0:
            print(f"  ...processed {i} wallets")

        wallet_txns = df[df[wallet_col] == wallet]
        sent_txns = wallet_txns[wallet_txns['from'] == wallet] if 'from' in wallet_txns else pd.DataFrame()
        received_txns = df[df['to'] == wallet] if 'to' in df else pd.DataFrame()
        if len(wallet_txns) == 0: continue

        features = {'wallet_id': wallet}
        features['total_transactions'] = len(wallet_txns)
        features['sent_transactions'] = len(sent_txns)
        features['received_transactions'] = len(received_txns)
        features['send_receive_ratio'] = len(sent_txns) / max(len(received_txns), 1)
        features['total_value_sent'] = sent_txns['value'].sum()
        features['total_value_received'] = received_txns['value'].sum()
        features['avg_transaction_value'] = wallet_txns['value'].mean()
        features['max_transaction_value'] = wallet_txns['value'].max()
        features['value_std'] = wallet_txns['value'].std()
        features['zero_value_ratio'] = (wallet_txns['value'] == 0).mean()
        if 'gasUsed' in wallet_txns.columns and 'gasPrice' in wallet_txns.columns:
            gas_costs = wallet_txns['gasUsed'] * wallet_txns['gasPrice']
            features['avg_gas_used'] = wallet_txns['gasUsed'].mean()
            features['total_gas_cost'] = gas_costs.sum()
            features['error_rate'] = wallet_txns['isError'].mean() if 'isError' in wallet_txns else 0
        else:
            features['avg_gas_used'] = features['total_gas_cost'] = features['error_rate'] = 0
        if len(wallet_txns) > 1:
            time_sorted = wallet_txns.sort_values('timeStamp')
            time_diffs = time_sorted['timeStamp'].diff().dt.total_seconds().dropna()
            features['avg_time_between_txns_hr'] = time_diffs.mean() / 3600
            activity_span_days = (time_sorted['timeStamp'].max() - time_sorted['timeStamp'].min()).days
            features['activity_span_days'] = max(activity_span_days, 1)
            features['transaction_frequency'] = len(wallet_txns) / features['activity_span_days']
        else:
            features['avg_time_between_txns_hr'] = 0
            features['activity_span_days'] = 1
            features['transaction_frequency'] = 1
        features['unique_recipients'] = sent_txns['to'].nunique() if len(sent_txns) > 0 else 0
        features['unique_senders'] = received_txns['from'].nunique() if len(received_txns) > 0 else 0
        features['recipient_concentration'] = len(sent_txns) / max(features['unique_recipients'], 1)
        if 'functionName' in wallet_txns.columns:
            features['unique_functions'] = wallet_txns['functionName'].nunique()
            if not wallet_txns['functionName'].empty:
                dominant_func_ratio = wallet_txns['functionName'].value_counts(normalize=True).iloc[0]
                features['contract_complexity'] = 1 - dominant_func_ratio
            else:
                features['contract_complexity'] = 0
        else:
            features['unique_functions'] = 0
            features['contract_complexity'] = 0
        wallet_features_list.append(features)
    print("...feature engineering complete.")
    return pd.DataFrame(wallet_features_list)

def calculate_advanced_risk_score(df):
    """Calculate a sophisticated, weighted risk score."""
    print("Calculating advanced risk scores...")
    feature_cols = [col for col in df.columns if col != 'wallet_id']
    features = df[feature_cols].copy().replace([np.inf, -np.inf], 0)
    scaler = MinMaxScaler()
    features_scaled = pd.DataFrame(scaler.fit_transform(features), columns=feature_cols, index=features.index)

    risk_components = {
        'volume_risk': {'features': ['total_transactions', 'total_value_sent', 'max_transaction_value'], 'weight': 0.20},
        'behavioral_risk': {'features': ['send_receive_ratio', 'recipient_concentration', 'transaction_frequency'], 'weight': 0.25},
        'technical_risk': {'features': ['avg_gas_used', 'total_gas_cost', 'error_rate'], 'weight': 0.20},
        'temporal_risk': {'features': ['avg_time_between_txns_hr'], 'weight': 0.15},
        'diversity_risk': {'features': ['unique_recipients', 'unique_senders', 'unique_functions', 'contract_complexity'], 'weight': 0.20}
    }
    risk_scores = pd.DataFrame(index=df.index)
    for component, config in risk_components.items():
        available_features = [f for f in config['features'] if f in features_scaled.columns]
        if available_features:
            component_score = features_scaled[available_features].mean(axis=1)
            risk_scores[component] = component_score * config['weight']
        else:
            risk_scores[component] = 0

    base_score = risk_scores.sum(axis=1)
    # Adjustments
    if 'error_rate' in features_scaled: base_score[features_scaled['error_rate'] > 0.1] *= 1.3
    if 'zero_value_ratio' in features_scaled: base_score[features_scaled['zero_value_ratio'] > 0.5] *= 1.2
    if 'transaction_frequency' in features_scaled: base_score[features_scaled['transaction_frequency'] > 0.95] *= 1.4

    print("...base risk score calculation complete.")
    return np.minimum(base_score * 1000, 1000)

def apply_ml_refinements(df):
    """Applies Isolation Forest and K-Means to generate adjustments."""
    print("Applying ML refinements (Anomaly Detection and Clustering)...")
    feature_cols_anomaly = [col for col in df.columns if col not in ['wallet_id', 'base_risk_score']]
    X = df[feature_cols_anomaly].fillna(0).replace([np.inf, -np.inf], 0)
    X_scaled = StandardScaler().fit_transform(X)

    # Isolation Forest for anomaly detection
    iso_forest = IsolationForest(contamination=0.05, random_state=42, n_estimators=100)
    df['is_anomaly'] = (iso_forest.fit_predict(X_scaled) == -1)

    # K-means clustering for behavioral grouping
    kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
    df['cluster'] = kmeans.fit_predict(X_scaled)
    cluster_risk_adj = df.groupby('cluster')['base_risk_score'].mean() / df['base_risk_score'].mean()
    df['cluster_risk_adjustment'] = df['cluster'].map(cluster_risk_adj)
    
    print(f"...identified {df['is_anomaly'].sum()} anomalous wallets.")
    print(f"...clustered wallets into 5 groups.")
    return df

def calculate_final_risk_score(df):
    """Combines base score with anomaly and cluster adjustments."""
    final_scores = df['base_risk_score'].copy()
    final_scores[df['is_anomaly']] *= 1.5 # Anomaly boost
    final_scores *= df['cluster_risk_adjustment'] # Cluster adjustment
    return np.minimum(np.maximum(final_scores, 0), 1000).round(0).astype(int)
