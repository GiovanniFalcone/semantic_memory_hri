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
create_boxplot_by_condition(df, "time to finish_sec", "Time to finish by experimental condition", "Time (seconds)", "boxplot_time_to_finish.png")
# turni per condizione
create_boxplot_by_condition(df, "turns", "Turns by experimental condition", "Number of turns", "boxplot_turns.png")
# numero di volte che è stato cliccato il bottone geo
create_boxplot_by_condition(df, "token geo", "Token geo by experimental condition", "Number of times the geo token was used", "boxplot_token_geo.png")
# numero di volte che è stato cliccato il bottone math
create_boxplot_by_condition(df, "token math", "Token math by experimental condition", "Number of times the math token was used", "boxplot_token_math.png")