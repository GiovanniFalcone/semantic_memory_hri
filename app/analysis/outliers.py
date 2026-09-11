import pandas as pd
import scipy.stats as stats
import numpy as np

# fare attenzione ai dati che seguono una distribuzione normale oppure no
# l'esclusione degli outliers può dipendere anche da quello

df = pd.read_excel("Questionnaire_results.xlsx", decimal=',') 

conditions = ['CC', 'CS0', 'CS1', 'CI', 'II']
cols = ['SOC_D', 'SOC_M', 'HLP_D', 'HLP_M', 'TRU_D', 'TRU_M', 
        'PR_D', 'PR_M', 'PTC_D', 'PTC_M', 'PU_D', 'PU_M', 'F_D', 'F_M']

print("\n" + "="*50)

# Calcolo della Deviazione Standard Raggruppata per ogni variabile.
pooled_sds = {}
for col in cols:
    residuals = df[col] - df.groupby("robot_type")[col].transform("mean")
    pooled_sds[col] = residuals.std()

results_outliers = []

for condition in conditions:
    print("\n" + "=" * 50)
    print(f"Analisi per la condizione: {condition}")
    print("=" * 50)

    df_condition = df[df["robot_type"] == condition]

    for col in cols:
        media = df_condition[col].mean()
        dev_standard = pooled_sds[col]

        lower_bound = media - 2 * dev_standard
        upper_bound = media + 2 * dev_standard

        print("\n" + "-" * 40)
        print(f"Analisi per la variabile: {col}")
        print(f"Media di condizione: {media:.4f}")
        print(f"Deviazione Standard (Pooled della colonna): {dev_standard:.4f}")
        print(f"Distanza dalla media (2 deviazioni standard): [{lower_bound:.4f}, {upper_bound:.4f}]")
        print("-" * 40)

        print("Valori dei partecipanti:")
        print(df_condition[["id", "robot_type", col]].to_string(index=False))

        # Verifica degli outlier rispetto alla media della specifica condizione
        outliers = df_condition[
            (df_condition[col] < lower_bound) | (df_condition[col] > upper_bound)
        ]

        if not outliers.empty:
            outliers_info = {
                "Condizione": condition,
                "Colonna": col,
                "Media": media,
                "Deviazione Standard": dev_standard,
                "Outliers": outliers[["id", "robot_type", col]].to_dict(
                    orient="records"
                ),
            }
            results_outliers.append(outliers_info)
            print(
                f"\n!!! OUTLIER RILEVATI nella colonna '{col}' per la condizione '{condition}':"
            )
            print(outliers[["id", "robot_type", col]].to_string(index=False))

print("\n" + "=" * 50)
print("RISULTATI OUTLIERS:")
print("=" * 50)

if results_outliers:
    for result in results_outliers:
        print(f"\nCondizione: {result['Condizione']}, Colonna: {result['Colonna']}")
        print(f"Media: {result['Media']:.4f}, Deviazione Standard: {result['Deviazione Standard']:.4f}")
        print("Outliers:")
        for outlier in result["Outliers"]:
            valore = outlier[result["Colonna"]]
            print(f"ID: {outlier['id']}, Robot Type: {outlier['robot_type']}, Valore: {valore:.4f}")
else:
    print("\nNessun outlier rilevato oltre la soglia delle 2 Deviazioni Standard.")