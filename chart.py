import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

readmissions = pd.read_csv('FY_2026_Hospital_Readmissions_Reduction_Program_Hospital.csv')
hospitals = pd.read_csv('Hospital_General_Information.csv')

readmissions['Facility ID'] = readmissions['Facility ID'].astype(str).str.zfill(6)
hospitals['Facility ID'] = hospitals['Facility ID'].astype(str)

hf = readmissions[readmissions['Measure Name'] == 'READM-30-HF-HRRP']
hf = hf[hf['Excess Readmission Ratio'].notna()]

info = hospitals[['Facility ID', 'Hospital Ownership']]
df = hf.merge(info, on='Facility ID', how='left')
df = df[df['Hospital Ownership'].notna()]

df['size_group'] = pd.qcut(df['Number of Discharges'], 4,
                           labels=['Smallest', 'Small-mid', 'Mid-large', 'Largest'])

two = df[df['Hospital Ownership'].isin(
    ['Proprietary', 'Voluntary non-profit - Private'])]

grouped = two.groupby(['size_group', 'Hospital Ownership'], observed=True)
means = grouped['Excess Readmission Ratio'].mean()
table = means.unstack()

table.columns = ['For-profit', 'Nonprofit private']
print(table.round(4))

fig, ax = plt.subplots(figsize=(9, 5.5))

table.plot(kind='bar', ax=ax, color=['#C97B84', '#7B9EA8'], width=0.75)

ax.axhline(1.0, color='#444', linestyle='--', linewidth=1)
ax.text(3.45, 1.001, 'Expected', fontsize=9, color='#444')

ax.set_ylim(0.97, 1.04)
ax.set_ylabel('Mean excess readmission ratio')
ax.set_xlabel('Hospital size (heart failure discharge quartile)')
ax.set_title('For-profit hospitals exceed expected heart failure readmissions\nat every size level',
             fontsize=13, pad=15)

handles, labels = ax.get_legend_handles_labels()
ax.legend(handles[:2], labels[:2], frameon=False)

plt.xticks(rotation=0)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig('readmissions_by_ownership.png', dpi=150)
print("Saved readmissions_by_ownership.png")