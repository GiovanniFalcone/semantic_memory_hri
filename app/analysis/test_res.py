import scipy.stats as stats
import pandas as pd
import pingouin as pg

df = pd.read_excel("results.xlsx")

# rimuove il partecipante con id=2 in quanto outlier
print(f"Dimensione del dataset prima della rimozione dell'ID 2: {df.shape}")
df = df[df['id'] != 2] 
print(f"Dimensione del dataset dopo la rimozione dell'ID 2: {df.shape}")
# ********************************+
# rimuove partecipante 31 (papabile outlier)
print(f"**************** rimuovo partecipante id=31 (papabile outlier) ****************")
df = df[df['id'] != 31]
print(f"Dimensione del dataset dopo la rimozione dell'ID 31: {df.shape}")
# ********************************+


columns = ['turns', 'time to finish_sec', 'avg_find_pair_sec', 
           'board changed times', 
           'token geo', 'turns geo', 'token math', 'turns math',
           'pairs resolved from geo robot', 'pairs resolved from math robot', 'board changed times', 'wrong moves']

results = []
conditions = ['CC', 'CS0', 'CS1', 'CI', 'II']

for col in columns:
    print(f"\nAnalisi per la variabile: {col}")
    # estrazione dei dati per ciascun gruppo
    groups = [df[df['experiment_condition'] == cond][col].values for cond in conditions]
    is_normal = True
    for group in groups:
        _, p_shapiro = stats.shapiro(group)
        print(f"Test di Shapiro-Wilk per il gruppo: p-value: {p_shapiro:.4f}")
        if p_shapiro <= 0.05:
            is_normal = False
            break # in quanto almeno un gruppo non segue una distribuzione normale, possiamo interrompere il ciclo

    if is_normal:
        print("✅ I dati seguono una distribuzione normale (p > 0.05)")
        is_normal = True
    else:
        print("❌ I dati NON seguono una distribuzione normale (p <= 0.05)")
        is_normal = False

    # estraggo i dati per ciascun gruppo
    cc = df[df['experiment_condition']=='CC'][col]
    cs0 = df[df['experiment_condition']=='CS0'][col]
    cs1 = df[df['experiment_condition']=='CS1'][col]
    ci = df[df['experiment_condition']=='CI'][col]
    ii = df[df['experiment_condition']=='II'][col]

    if is_normal:
        # la distribuzione dei dati è normale, possiamo usare un test parametrico come ANOVA
        # Test di Levene per omogeneità delle varianze (per verificare omogeneità delle varianze tra i gruppi)
        _, p_levene = stats.levene(cc, cs0, cs1, ci, ii)
        if p_levene > 0.05:
            print("✅ Le varianze sono omogenee (p > 0.05)")
            # applica anova
            stat, p_val = stats.f_oneway(cc, cs0, cs1, ci, ii)
            test_used = 'ANOVA'
            print(f"Test ANOVA: Statistica: {stat:.4f}, p-value: {p_val:.4f}")
        else:
            print("❌ Le varianze non sono omogenee (p <= 0.05)")
            # applica il test di Welch ANOVA in quanto le varianze non sono omogenee
            welch = pg.welch_anova(dv=col, between='experiment_condition', data=df)
            stat = welch['F'].iloc[0]
            p_val = welch['p_unc'].iloc[0]
            test_used = 'Welch ANOVA'
    else:
        print("❌ I dati NON seguono una distribuzione normale (p <= 0.05)")

        # utilizza il test di Kruskal-Wallis per confrontare le medie dei gruppi
        stat, p_val = stats.kruskal(cc, cs0, cs1, ci, ii)
        test_used = 'Kruskal-Wallis'
        print(f"Test di Kruskal-Wallis: Statistica: {stat:.4f}, p-value: {p_val:.4f}")

    if p_val < 0.05:
        print("✅ Ci sono differenze significative tra le condizioni sperimentali (p <= 0.05)\n")
    else:
        print("❌ Non ci sono differenze significative tra le condizioni sperimentali (p > 0.05)\n")

    results.append({
        'Variabile': col,
        'Test Utilizzato': test_used,
        'Statistica': stat,
        'p-value': p_val,
        'Significativo (p<0.05)': p_val < 0.05
    })

# Creazione del DataFrame dei risultati finali
final_results = pd.DataFrame(results)
print("\n" + "="*50)
print("RISULTATI FINALI:")
print("="*50)
print(final_results.to_string(index=False))

# =======
# Confronto fra token geo e token math all'interno di ciascun gruppo sperimentale
print("\n" + "="*50)
print("CONFRONTO TRA TOKEN GEO E TOKEN MATH ALL'INTERNO DI CIASCUN GRUPPO SPERIMENTALE:")
for cond in conditions:
    geo = df[df['experiment_condition'] == cond]['token geo']
    math = df[df['experiment_condition'] == cond]['token math']
    
    # Test di Shapiro-Wilk per la normalità
    _, p_shapiro_geo = stats.shapiro(geo)
    _, p_shapiro_math = stats.shapiro(math)
    
    if p_shapiro_geo > 0.05 and p_shapiro_math > 0.05:
        # Se entrambi i gruppi seguono una distribuzione normale, utilizza il test t di Student
        stat, p_val = stats.ttest_rel(geo, math)
        test_used = 'Test t di Student'
    else:
        # Altrimenti, utilizza il test di Wilcoxon
        stat, p_val = stats.wilcoxon(geo, math)
        test_used = 'Test di Wilcoxon'
    
    print(f"\nCondizione: {cond}")
    print(f"Test utilizzato: {test_used}")
    print("Token geo - Media: {:.4f}, Deviazione Standard: {:.4f}".format(geo.mean(), geo.std()))
    print("Token math - Media: {:.4f}, Deviazione Standard: {:.4f}".format(math.mean(), math.std()))
    print(f"Statistica: {stat:.4f}, p-value: {p_val:.4f}")
    
    if p_val < 0.05:
        print("✅ Ci sono differenze significative tra token geo e token math (p <= 0.05)")
    else:
        print("❌ Non ci sono differenze significative tra token geo e token math (p > 0.05)")

# salva su excel
import openpyxl
from openpyxl.styles import Alignment

with pd.ExcelWriter('results.xlsx', engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:  
    final_results.to_excel(writer, sheet_name='statistic_tests', index=False)

# Aggiusta la larghezza e centra il testo
wb = openpyxl.load_workbook("results.xlsx")
centered = Alignment(horizontal="center", vertical="center", wrap_text=True)

ws = wb['statistic_tests']
for col in ws.columns:
    max_len = max(len(str(cell.value or '')) for cell in col)
    col_letter = openpyxl.utils.get_column_letter(col[0].column)
    ws.column_dimensions[col_letter].width = max(max_len + 3, 12)
    for cell in col:
        cell.alignment = centered

wb.save("results.xlsx")