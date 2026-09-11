import pandas as pd
import scipy.stats as stats
import pingouin as pg
import openpyxl
from openpyxl.styles import Alignment

def save_dataframes_to_excel(dataframe_A, dataframe_B, sheet_name):
    if dataframe_B is not None:
        # Creiamo una riga vuota con le stesse colonne per fare da separatore
        empty_row = pd.DataFrame([{col: None for col in dataframe_A.columns}])
        # Concatenazione dei DataFrame con la riga vuota in mezzo
        df_final = pd.concat([pd.DataFrame(dataframe_A), empty_row, pd.DataFrame(dataframe_B)], ignore_index=True)
    else:
        df_final = pd.DataFrame(dataframe_A)
        
    # Salviamo in un nuovo foglio mantenendo quelli vecchi
    with pd.ExcelWriter('Questionnaire_results.xlsx', engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:  
        df_final.to_excel(writer, sheet_name=sheet_name, index=False)

    # Formattazione per rendere le celle leggibili
    wb = openpyxl.load_workbook("Questionnaire_results.xlsx")
    centered = Alignment(horizontal="center", vertical="center", wrap_text=True)

    ws = wb[sheet_name]
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)
        for cell in col:
            cell.alignment = centered

    wb.save("Questionnaire_results.xlsx")

def compare_single_robot_between_conditions(df, conditions, columns, questionnaire_name):
    # ==========================================
    # CONFRONTO TRA CONDIZIONI 
    # (Il robot viene percepito diversamente nei vari gruppi?)
    # ==========================================

    print(f"\n--- AVVIO ANALISI TRA CONDIZIONI - {questionnaire_name} ---")
    results_A = []
    posthoc_results = []

    for col in columns:
        df_clean = df[['robot_type', col]].dropna()
        groups = [df_clean[df_clean['robot_type'] == cond][col].values for cond in conditions]
        groups = [g for g in groups if len(g) > 0]

        # Test Normalità (Shapiro)
        is_normal = True
        for group in groups:
            if len(group) >= 3:
                _, p_shapiro = stats.shapiro(group)
                if p_shapiro <= 0.05:
                    is_normal = False
                    break
            else:
                is_normal = False

        # Scelta del test
        if is_normal:
            _, p_levene = stats.levene(*groups)
            if p_levene > 0.05:
                stat, p_val = stats.f_oneway(*groups)
                test_used = 'ANOVA'
            else:
                welch = pg.welch_anova(dv=col, between='robot_type', data=df_clean)
                stat = welch['F'].iloc[0]
                p_val = welch['p-unc'].iloc[0]
                test_used = 'Welch ANOVA'
        else:
            stat, p_val = stats.kruskal(*groups)
            test_used = 'Kruskal-Wallis'

        is_significant = p_val < 0.05
        results_A.append({
            'Analisi': 'Tra Condizioni',
            'Variabile/Condizione': col,
            'Test Utilizzato': test_used,
            'Statistica': stat,
            'p-value': p_val,
            'Significativo (p<0.05)': is_significant
        })

        # ==========================================
        # TEST POST-HOC
        # ==========================================
        if is_significant:
            print(f"Trovata significatività per {col}! Eseguo i test Post-Hoc...")
            posthoc_test_used = ''
            
            if test_used == 'ANOVA':
                ph = pg.pairwise_tukey(data=df_clean, dv=col, between='robot_type')
                ph.rename(columns={'p_tukey': 'p-value_corretto'}, inplace=True)
                posthoc_test_used = 'Tukey'
                
            elif test_used == 'Welch ANOVA':
                ph = pg.pairwise_gameshowell(data=df_clean, dv=col, between='robot_type')
                ph.rename(columns={'pval': 'p-value_corretto'}, inplace=True)
                posthoc_test_used = 'Games-Howell'
                
            else:
                # Per Kruskal-Wallis usiamo confronti a coppie con correzione di Holm
                ph = pg.pairwise_tests(data=df_clean, dv=col, between='robot_type', parametric=False, padjust='holm')
                ph.rename(columns={'p_unc': 'p-value_corretto'}, inplace=True)
                posthoc_test_used = 'Holm'

            # output dei risultati post-hoc
            ph = ph[['A', 'B', 'p-value_corretto']].copy()
            ph['Variabile'] = col
            ph['Significativo'] = ph['p-value_corretto'] < 0.05
            ph['Test Post-Hoc'] = posthoc_test_used
            posthoc_results.append(ph)

    # Creazione del DataFrame dei risultati finali
    final_results = pd.DataFrame(results_A)
    print("\n" + "="*50)
    print("RISULTATI FINALI:")
    print("="*50)
    print(final_results.to_string(index=False))

    if len(posthoc_results) > 0:
        final_posthoc = pd.concat(posthoc_results)
        print("\n" + "="*50)
        print("RISULTATI POST-HOC (Confronti a coppie):")
        print("="*50)
        print(final_posthoc.to_string(index=False))
    else:
        final_posthoc = pd.DataFrame()
        print("\nNessun test post-hoc necessario in quanto non sono state rilevate differenze significative tra le condizioni.")

    return final_results, final_posthoc

def compare_robots_in_condition(df, metrics, questionnaire_name):
    # ==========================================
    # CONFRONTO GEO VS MATH 
    # (Nella stessa condizione, Geo è valutato diversamente da Math?)
    # ==========================================
    print(f"\n--- AVVIO ANALISI GEO VS MATH - {questionnaire_name} ---")
    results_B = []
    posthoc_results = []

    for cond in conditions:
        df_cond = df[df['robot_type'] == cond].dropna()

        for metric in metrics:
            col_D = f"{metric}_D"
            col_M = f"{metric}_M"
            
            # estrae i valori delle due colonne per la condizione corrente
            geo_scores = df_cond[col_D].values
            math_scores = df_cond[col_M].values

            # Calcolo delle differenze tra le due serie di punteggi
            diffs = geo_scores - math_scores
            
            # controllo se tutte le differenze sono uguali (valori identici)
            if len(set(diffs)) == 1:
                stat, p_val = 0.0, 1.0
                test_used = 'Valori identici (Nessun test)'
            else:
                # verifica la normalità della distribuzione delle differenze (Shapiro-Wilk)
                _, p_shapiro = stats.shapiro(diffs)
                
                if p_shapiro > 0.05:
                    # Distribuzione normale -> T-test
                    stat, p_val = stats.ttest_rel(geo_scores, math_scores)
                    test_used = 'T-test'
                else:
                    # Distribuzione non normale -> Test di Wilcoxon
                    stat, p_val = stats.wilcoxon(geo_scores, math_scores)
                    test_used = 'Wilcoxon'

            is_significant = p_val < 0.05
            results_B.append({
                'Analisi': 'Geo vs Math',
                'Variabile/Condizione': f"{metric} in {cond}",
                'Test Utilizzato': test_used,
                'Statistica': stat,
                'p-value': p_val,
                'Significativo (p<0.05)': is_significant
            })

        # aggiungo una riga vuota per separare i risultati delle diverse condizioni
        results_B.append({
            'Analisi': None,
            'Variabile/Condizione': None,
            'Test Utilizzato': None,
            'Statistica': None,
            'p-value': None,
            'Significativo (p<0.05)': None
        })

    # Creazione del DataFrame dei risultati finali
    final_results = pd.DataFrame(results_B)
    print("\n" + "="*50)
    print("RISULTATI FINALI:")
    print("="*50)
    print(final_results.dropna(how='all').to_string(index=False))

    return final_results, None

df = pd.read_excel("Questionnaire_results.xlsx", decimal=',') 

conditions = ['CC', 'CS0', 'CS1', 'CI', 'II']
# PSI
psi_col = ['SOC_D', 'SOC_M', 'HLP_D', 'HLP_M', 'TRU_D', 'TRU_M']
psi_scales = ['SOC', 'HLP', 'TRU']
# Trust
trust_col = ['PR_D', 'PR_M', 'PTC_D', 'PTC_M', 'PU_D', 'PU_M', 'F_D', 'F_M']
trust_scales = ['PR', 'PTC', 'PU', 'F']

psi_results_compare_single_robot_between_conditions, psi_post_hoc = compare_single_robot_between_conditions(df, conditions, psi_col, "PSI")
psi_results_compare_robots_in_condition, _ = compare_robots_in_condition(df, psi_scales, "PSI")
save_dataframes_to_excel(psi_results_compare_single_robot_between_conditions, psi_results_compare_robots_in_condition, "PSI_Results")
save_dataframes_to_excel(psi_post_hoc, None, "PSI_PostHoc")
print("Dataframe PSI salvato in 'Questionnaire_results.xlsx' nel foglio 'PSI_Results'.")

print("\n" + "="*50)
print("ANALISI SUL QUESTIONARIO TRUST")
print("="*50)

trust_results_compare_single_robot_between_conditions, _ = compare_single_robot_between_conditions(df, conditions, trust_col, "Trust")
trust_results_compare_robots_in_condition, _ = compare_robots_in_condition(df, trust_scales, "Trust")
save_dataframes_to_excel(trust_results_compare_single_robot_between_conditions, trust_results_compare_robots_in_condition, "Trust_Results")
print("Dataframe Trust salvato in 'Questionnaire_results.xlsx' nel foglio 'Trust_Results'.")