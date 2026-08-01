import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, roc_curve, classification_report
import warnings
warnings.filterwarnings('ignore')

print("="*70)
print("LEAN SIX SIGMA - DMAIC: Hospital Readmission Reduction")
print("="*70)

# Load real CMS data
readmissions = pd.read_csv('FY_2026_Hospital_Readmissions_Reduction_Program_Hospital.csv')
hospitals = pd.read_csv('Hospital_General_Information.csv')

# Clean facility IDs
readmissions['Facility ID'] = readmissions['Facility ID'].astype(str).str.zfill(6)
hospitals['Facility ID'] = hospitals['Facility ID'].astype(str).str.zfill(6)

# Filter to rows with data
df = readmissions[readmissions['Excess Readmission Ratio'].notna()].copy()

# Merge with hospital info
df = df.merge(hospitals[['Facility ID', 'Hospital Ownership', 'Hospital Type', 'Hospital overall rating']], 
              on='Facility ID', how='left')

print("\n[D - DEFINE]")
print("Problem: CMS penalizes hospitals with excess readmissions (ratio > 1.0)")
print(f"Scope: {len(df)} hospital-condition combinations")
print("Objective: Identify high-risk hospitals for targeted intervention")

print("\n[M - MEASURE]")
print(f"Excess readmission range: {df['Excess Readmission Ratio'].min():.3f} to {df['Excess Readmission Ratio'].max():.3f}")
print(f"Hospitals with excess readmissions: {(df['Excess Readmission Ratio'] > 1.0).sum()} ({100*(df['Excess Readmission Ratio'] > 1.0).sum()/len(df):.1f}%)")
print(f"Mean excess ratio: {df['Excess Readmission Ratio'].mean():.4f}")

# Create target variable
df['excess_flag'] = (df['Excess Readmission Ratio'] > 1.0).astype(int)

print("\n[A - ANALYZE]")
print("Key findings by Hospital Ownership:")
for ownership in df['Hospital Ownership'].dropna().unique():
    subset = df[df['Hospital Ownership'] == ownership]
    if len(subset) > 0:
        mean_ratio = subset['Excess Readmission Ratio'].mean()
        pct_excess = 100 * (subset['Excess Readmission Ratio'] > 1.0).sum() / len(subset)
        print(f"  - {ownership}: avg={mean_ratio:.4f}, {pct_excess:.1f}% with excess")

# Prepare features for model
df['ownership_encoded'] = pd.factorize(df['Hospital Ownership'].fillna('Unknown'))[0]
df['type_encoded'] = pd.factorize(df['Hospital Type'].fillna('Unknown'))[0]
df['measure_encoded'] = pd.factorize(df['Measure Name'].fillna('Unknown'))[0]
df['discharges_clean'] = df['Number of Discharges'].fillna(df['Number of Discharges'].median())

features = ['ownership_encoded', 'type_encoded', 'measure_encoded', 'discharges_clean']
X = df[features].fillna(0)
y = df['excess_flag']

# Build predictive model
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
model.fit(X_train, y_train)

accuracy = model.score(X_test, y_test)
y_pred_proba = model.predict_proba(X_test)[:, 1]
auc = roc_auc_score(y_test, y_pred_proba)

print(f"\n[I - IMPROVE]")
print(f"Predictive Model Performance:")
print(f"  - Accuracy: {accuracy:.3f}")
print(f"  - ROC-AUC: {auc:.3f}")

# Add risk scores to all data
df['risk_score'] = model.predict_proba(X)[:, 1]
df['risk_level'] = pd.cut(df['risk_score'], bins=[0, 0.3, 0.6, 1.0], labels=['Low', 'Medium', 'High'])

print(f"\nTop 10 High-Risk Facilities:")
high_risk = df[df['risk_level'] == 'High'].nlargest(10, 'risk_score')
print(high_risk[['Facility Name', 'Hospital Ownership', 'risk_score', 'Excess Readmission Ratio']].to_string(index=False))

print(f"\n[C - CONTROL]")
print("Monitoring Framework:")
print("  1. Monthly risk score tracking for high-risk facilities")
print("  2. Quarterly model retraining with new data")
print("  3. Benchmark best-performing hospitals by measure")
print("  4. Share improvement strategies across facility network")

# Save results
df.to_csv('hospital_readmissions_with_risk_scores.csv', index=False)
print(f"\nData with risk scores saved: hospital_readmissions_with_risk_scores.csv")

# Visualization
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 1. ROC Curve
fpr, tpr, _ = roc_curve(y_test, y_pred_proba)
axes[0, 0].plot(fpr, tpr, linewidth=2, label=f'ROC (AUC={auc:.3f})')
axes[0, 0].plot([0, 1], [0, 1], 'k--', linewidth=1)
axes[0, 0].set_xlabel('False Positive Rate')
axes[0, 0].set_ylabel('True Positive Rate')
axes[0, 0].set_title('Model Performance (ROC Curve)')
axes[0, 0].legend()
axes[0, 0].grid(alpha=0.3)

# 2. Feature Importance
importance_df = pd.DataFrame({
    'feature': ['Ownership', 'Type', 'Condition', 'Discharges'],
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)
axes[0, 1].barh(importance_df['feature'], importance_df['importance'], color='#3498db')
axes[0, 1].set_title('What Drives Excess Readmissions?')
axes[0, 1].grid(axis='x', alpha=0.3)

# 3. Risk Distribution
risk_counts = df['risk_level'].value_counts()
axes[1, 0].bar(risk_counts.index, risk_counts.values, color=['#2ecc71', '#f39c12', '#e74c3c'])
axes[1, 0].set_ylabel('Count')
axes[1, 0].set_title('Facility Risk Distribution')
axes[1, 0].grid(axis='y', alpha=0.3)

# 4. Risk vs Actual
axes[1, 1].scatter(df['risk_score'], df['Excess Readmission Ratio'], alpha=0.5, s=30)
axes[1, 1].axhline(y=1.0, color='r', linestyle='--', linewidth=2, label='Penalty Threshold')
axes[1, 1].set_xlabel('Predicted Risk Score')
axes[1, 1].set_ylabel('Actual Excess Ratio')
axes[1, 1].set_title('Prediction vs Reality')
axes[1, 1].legend()
axes[1, 1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig('lean_six_sigma_dmaic.png', dpi=300, bbox_inches='tight')
print("Visualization saved: lean_six_sigma_dmaic.png")

print("\n" + "="*70)
print("DMAIC ANALYSIS COMPLETE")
print("="*70)
