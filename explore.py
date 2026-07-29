import pandas as pd 

readmissions = pd.read_csv('FY_2026_Hospital_Readmissions_Reduction_Program_Hospital.csv')
hospitals = pd.read_csv('Hospital_General_Information.csv')

print("READMISSIONS FILE")
print(readmissions.shape)
print(readmissions.columns.tolist())
print()

print("HOSPITALS FILE")
print(hospitals.shape)
print(hospitals.columns.tolist())

print()
print("CONDITIONS MEASURED")
print(readmissions['Measure Name'].value_counts())
print()

print("EXCESS READMISSION RATIO")
print(readmissions['Excess Readmission Ratio'].describe())
print()

print("OWNERSHIP TYPES")
print(hospitals['Hospital Ownership'].value_counts())

print()
print("MISSING RATIOS BY CONDITION")
print(readmissions[readmissions['Excess Readmission Ratio'].isna()]['Measure Name'].value_counts())
print()

print("FOOTNOTE REASONS")
print(readmissions['Footnote'].value_counts())
