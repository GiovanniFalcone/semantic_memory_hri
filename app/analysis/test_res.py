import scipy.stats as stats
import pandas as pd

df = pd.read_excel("results.xlsx")

columns = ['turns', 'time to finish_sec', 'avg_find_pair_sec', 
           'board changed times', 
           'token geo', 'token math', 
           'pairs resolved from geo robot', 'pairs resolved from math robot']

kruskal_results = {'variable': [], 
           'kruskal_p-value': [],
           'kruskal_h-statistic': []
        }

anova_results = {'variable': [],
           'anova_p-value': [],
           'anova_f-statistic': []
        }

for col in columns:
    print(f"Analisi della normalità per la colonna: {col}")
    stat, p_val = stats.shapiro(df[col])
    print(f"Statistica: {stat:.4f}, p-value: {p_val:.4f}")
    
    cc = df[df['experiment_condition']=='CC'][col]
    cs0 = df[df['experiment_condition']=='CS0'][col]
    cs1 = df[df['experiment_condition']=='CS1'][col]
    ci = df[df['experiment_condition']=='CI'][col]
    ii = df[df['experiment_condition']=='II'][col]

    if p_val > 0.05:
        print("✅ I dati seguono una distribuzione normale (p > 0.05)")
    
        # when data is normal, we can use ANOVA
        stat, p_val = stats.f_oneway(cc, cs0, cs1, ci, ii)
        print(f"Test ANOVA: Statistica: {stat:.4f}, p-value: {p_val:.4f}")

        anova_results['variable'].append(col)
        anova_results['anova_p-value'].append(p_val)
        anova_results['anova_f-statistic'].append(stat)

        if p_val < 0.05:
            print("✅ Ci sono differenze significative tra le condizioni sperimentali (p <= 0.05)\n")
        else:
            print("❌ Non ci sono differenze significative tra le condizioni sperimentali (p > 0.05)\n")
    else:
        print("❌ I dati NON seguono una distribuzione normale (p <= 0.05)")

        # when data is not normal, we can use the Kruskal-Wallis test
        stat, p_val = stats.kruskal(cc, cs0, cs1, ci, ii)
        print(f"Test di Kruskal-Wallis: Statistica: {stat:.4f}, p-value: {p_val:.4f}")

        kruskal_results['variable'].append(col)
        kruskal_results['kruskal_p-value'].append(p_val)
        kruskal_results['kruskal_h-statistic'].append(stat)

        if p_val < 0.05:
            print("✅ Ci sono differenze significative tra le condizioni sperimentali (p <= 0.05)\n")
        else:
            print("❌ Non ci sono differenze significative tra le condizioni sperimentali (p > 0.05)\n")

# concatena i risultati in un unico DataFrame e mostrali a schermo
kruskal_df = pd.DataFrame(kruskal_results)
anova_df = pd.DataFrame(anova_results)
final_results = pd.concat([kruskal_df, anova_df])
print("Risultati finali dei test statistici:")
print(final_results)