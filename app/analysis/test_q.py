import pandas as pd
import scikit_posthocs as sp
from scipy import stats

df = pd.read_excel("Questionnaire_results.xlsx")

# PSI e Trust
variables = ['SOC_D', 'SOC_M', 'HLP_D', 'HLP_M', 'TRU_D', 'TRU_M',
             'PR_D', 'PR_M', 'PTC_D', 'PTC_M', 'PU_D', 'PU_M', 'F_D', 'F_M']

# columns to save
excel_columns = {'Variable': [], 
                 'H-Statistic': [], 'P-Value': [], 'Significant': []}

bonferroni_results = {}

# converte a float i valori decimali
df[variables] = df[variables].map(
        lambda x: (
            float(str(x).replace(",", ".")) if isinstance(x, str) else float(x)
        )
    )

for var in variables:
    # prende i 5 gruppi di dati per ciascun robot_type e li mette in una lista
    groups = [group[var].dropna() for _, group in df.groupby("robot_type")]

    print(f"--- {var} ---")

    # check normality for each robot_type group
    for robot, group in df.groupby("robot_type"):
        print(f"Robot {robot} - {var} - Dati: {group[var].dropna().tolist()}")
        stat, p = stats.shapiro(group[var].dropna())
        print(f"Robot {robot} - Shapiro p-value: {p:.4f}")

    result   = stats.kruskal(*groups)
    print(f"Result: {result}\n")

    excel_columns['Variable'].append(var)
    excel_columns['H-Statistic'].append(result.statistic)
    excel_columns['P-Value'].append(result.pvalue)
    excel_columns['Significant'].append(result.pvalue < 0.05)

    if result.pvalue < 0.05:
        print(
            f"p < 0.05: Calcolo Post-Hoc di Dunn con correzione di Bonferroni..."
        )

        # Calcola la matrice dei p-value aggiustati
        dunn_bonf = sp.posthoc_dunn(
            df, val_col=var, group_col="robot_type", p_adjust="bonferroni"
        )
        bonferroni_results[var] = dunn_bonf

        print("\nMatrice p-values (Bonferroni):")
        print(dunn_bonf.round(4))
        print("\n")
    else:
        print("p >= 0.05: Nessun test post-hoc necessario.\n")

# crea un DataFrame dai risultati e lo salva in un file Excel
results_df = pd.DataFrame(excel_columns)
print(results_df)

# crea il dataframe con i risultati di Bonferroni e li mostra a schermo
for var, bonferroni_df in bonferroni_results.items():
    print(f"\nMatrice dei p-value di Bonferroni per {var}:")
    print(bonferroni_df.round(4))
    # identifica quelli significativi (p < 0.05)
    significant_pairs = bonferroni_df[bonferroni_df < 0.05].stack().index.tolist()
    print(f"Significant pairs (p < 0.05): {significant_pairs}")

# confronto statistico tra le coppie (SOC_D, SOC_M, ecc) per robot_type
pairs = [('SOC_D', 'SOC_M'), ('HLP_D', 'HLP_M'), ('TRU_D', 'TRU_M'),
         ('PR_D', 'PR_M'), ('PTC_D', 'PTC_M'), ('PU_D', 'PU_M'), ('F_D', 'F_M')]

for pair in pairs:
    var1, var2 = pair
    print(f"\nConfronto tra {var1} e {var2} per robot_type:")
    for robot, group in df.groupby("robot_type"):
        stat, p = stats.mannwhitneyu(group[var1].dropna(), group[var2].dropna())
        print(f"Robot {robot} - Mann-Whitney U p-value: {p:.4f} {'Significant' if p < 0.05 else 'Not Significant'}")

