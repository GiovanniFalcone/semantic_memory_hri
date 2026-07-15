import pandas as pd 
import seaborn as sns
import matplotlib.pyplot as plt 
from pathlib import Path

def create_boxplot_by_condition(df, y_col, title, y_label, output_filename):
    sns.boxplot(
        x='experiment_condition', 
        y=y_col, 
        hue='experiment_condition', 
        palette="pastel", 
        legend=False,              
        data=df
    )

    plt.title(title) 
    plt.suptitle("")
    plt.ylabel(y_label)
    plt.xlabel("Experimental condition") 
    plt.tight_layout()
    
    output_dir = Path("plot")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = output_dir / output_filename
    plt.savefig(file_path, dpi=300, bbox_inches="tight")
    plt.close()

df = pd.read_excel("results.xlsx")
# tempo per condizione
create_boxplot_by_condition(df, "time to finish_sec", "Time to finish by experimental condition", "Time (seconds)", "1_boxplot_time_to_finish.png")
# turni per condizione
create_boxplot_by_condition(df, "turns", "Turns by experimental condition", "Number of turns", "2_boxplot_turns.png")
# numero di volte che è stato cliccato il bottone geo
create_boxplot_by_condition(df, "token geo", "Token geo by experimental condition", "Number of times the geo token was used", "3_boxplot_token_geo.png")
# numero di volte che è stato cliccato il bottone math
create_boxplot_by_condition(df, "token math", "Token math by experimental condition", "Number of times the math token was used", "4_boxplot_token_math.png")
# numero di volte in cui si è risettato il tabellone
create_boxplot_by_condition(df, "board changed times", "Board resets by experimental condition", "Number of times the board was reset", "6_boxplot_reset.png")
# numero di volte in cui il robot di geografia ha risolto delle coppie (qualsiasi: random e non)
create_boxplot_by_condition(df, "pairs resolved from geo robot", "Geo pairs resolved by experimental condition", "Number of geo pairs resolved", "7_boxplot_geo_pairs_resolved.png")
# idem con matematica
create_boxplot_by_condition(df, "pairs resolved from math robot", "Math pairs resolved by experimental condition", "Number of math pairs resolved", "8_boxplot_math_pairs_resolved.png")

# numero di volte totali in cui gli utenti hanno cliccato i bottoni
df_total = df.copy()
df_total["total_clicks"] = df_total["token geo"] + df_total["token math"]
create_boxplot_by_condition(df_total, "total_clicks", "Total clicks by experimental condition", "Total number of clicks", "5_boxplot_total_clicks.png")