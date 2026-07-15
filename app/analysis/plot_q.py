import pandas as pd 
import seaborn as sns
import matplotlib.pyplot as plt 
from pathlib import Path

df = pd.read_excel("Questionnaire_results.xlsx")

pairs = [
    ("SOC", ["SOC_D", "SOC_M"]),
    ("HLP", ["HLP_D", "HLP_M"]),
    ("TRU", ["TRU_D", "TRU_M"]),
    ("Perceived_Reliability", ["PR_D", "PR_M"]),
    ("Perceived Technical Competence", ["PTC_D", "PTC_M"]),
    ("Perceived Understandability", ["PU_D", "PU_M"]),
    ("Faith", ["F_D", "F_M"]),
]

for pair_name, variables in pairs:
    pair_df = pd.melt(
        df[["robot_type"] + variables].copy(),
        id_vars=["robot_type"],
        value_vars=variables,
        var_name="measure",
        value_name="value",
    )

    sns.boxplot(
        x='robot_type', 
        y='value', 
        hue='measure', 
        palette="pastel",              
        data=pair_df
    )

    plt.title(pair_name + "_by_experimental_condition") 
    plt.suptitle("")
    plt.ylabel("Value")
    plt.xlabel("Experimental condition") 
    plt.tight_layout()
    
    output_dir = Path("plot")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_filename = f"{pair_name}_boxplot.png"
    file_path = output_dir / output_filename
    plt.savefig(file_path, dpi=300, bbox_inches="tight")
    plt.close()