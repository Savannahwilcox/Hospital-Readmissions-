import pandas as pd 

readmissions = pd.read_csv('FY_2026_Hospital_Readmissions_Reduction_Program_Hospital.csv')
hospitals = pd.read_csv('Hospital_General_Information.csv')

readmissions['Facility ID'] = readmissions['Facility ID'].astype(str).str.zfill(6)
hospitals['Facility ID'] = hospitals['Facility ID'].astype(str)

# keep only heart failure rows that have a ratio 
hf = readmissions[readmissions['Measure Name'] == 'READM-30-HF-HRRP']
hf = hf[hf['Excess Readmission Ratio'].notna()]

print(f"Heart failure hospitals with data: {len(hf)}")

# attach ownership and hospital type from other file 
info = hospitals[['Facility ID', 'Hospital Ownership', 'Hospital Type',
		'Hospital overall rating', 'State']]

df = hf.merge(info, on='Facility ID', how='left')

print(f"After merge: {len(df)} rows")
print(f"Missing ownership after merge: {df['Hospital Ownership'].isna().sum()}")

# drop those with no ownership data 
df = df[df['Hospital Ownership'].notna()]
print(f"Analysis set: {len(df)} hospitals")
print()

# penalized means readmitting more than expected 
df['penalized'] = df['Excess Readmission Ratio'] > 1.0
print(f"Above expected: {df['penalized'].sum()} ({df['penalized'].mean():.1%})")

by_owner = df.groupby('Hospital Ownership').agg(
	hospitals=('Facility ID', 'count'),
	mean_ratio=('Excess Readmission Ratio', 'mean'), 
	pct_above=('penalized', 'mean')
).sort_values('mean_ratio', ascending=False)

by_owner['mean_ratio'] = by_owner['mean_ratio'].round(4)
by_owner['pct_above'] = (by_owner['pct_above'] * 100).round(1)

print()
print("BY OWNERSHIP")
print(by_owner)

print()
print("BY HOSPITAL TYPE")
print(df.groupby('Hospital Type')['Excess Readmission Ratio'].agg(['count', 'mean']).round(4))

print()
print("DISCHARGES BY OWNERSHIP (size proxy)")
sizes = df.groupby('Hospital Ownership')['Number of Discharges'].median()
sizes = sizes.round(0).sort_values(ascending=False)
print(sizes)

print()
print("BY HOSPITAL SIZE")

df['size_group'] = pd.qcut(df['Number of Discharges'], 4, 
				labels=['Smallest', 'Small-mid', 'Mid-large', 'Largest'])

by_size = df.groupby('size_group', observed=True).agg(
		hospitals=('Facility ID', 'count'),
		mean_ratio=('Excess Readmission Ratio', 'mean'),
		pct_above=('penalized', 'mean')
).round(4)

print(by_size)

print()
print("OWNERSHIP WITHIN SIZE GROUPS")

two_types = df[df['Hospital Ownership'].isin(
	['Proprietary', 'Voluntary non-profit - Private'])]

cross = two_types.groupby(['size_group', 'Hospital Ownership'], observed=True).agg(
	hospitals=('Facility ID', 'count'), 
	mean_ratio=('Excess Readmission Ratio', 'mean')
).round(4)

print(cross)

print()
print("PROPRIETARY VS NONPROFIT, ALL CONDITIONS")

all_conditions = readmissions[readmissions['Excess Readmission Ratio'].notna()]
all_conditions = all_conditions.merge(info, on='Facility ID', how='left')

two = all_conditions[all_conditions['Hospital Ownership'].isin(
	['Proprietary', 'Voluntary non-profit - Private'])]

by_condition = two.groupby(['Measure Name', 'Hospital Ownership'], observed=True)
result = by_condition['Excess Readmission Ratio'].agg(['count', 'mean'])
result = result.round(4)

print(result)

by_state = df.groupby('State_x')
result = by_state['Excess Readmission Ratio'].agg(['count', 'mean'])
result = result.round(4).sort_values('mean', ascending=False)

print(result.head(15))
