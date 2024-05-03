import pandas as pd 
import numpy as np 
from scipy.stats import f_oneway, pearsonr
from statsmodels.stats.multicomp import pairwise_tukeyhsd

df = pd.read_csv("UserData/game_play_data.csv")
df = df.replace(-1,np.NaN)
df["percent_incorrect"] = df["num_incorrect"] / (df["num_correct"] + df["num_incorrect"])
df["percent_incomplete"] = (48 - df["num_correct"]) / 48


def calculate_pvalues(df):
    dfcols = pd.DataFrame(columns=df.columns)
    pvalues = dfcols.transpose().join(dfcols, how='outer')
    for r in df.columns:
        for c in df.columns:
            tmp = df[df[r].notnull() & df[c].notnull()]
            pvalues.loc[c,r] = round(pearsonr(tmp[r], tmp[c])[1], 4)
    return pvalues

print(df[["loops", "attempts", "total_time", "percent_incorrect", "percent_incomplete", "is_correct",  "challenge_scale"]].corr())
print("\n\n pvalues:")
print(calculate_pvalues(df[["loops", "attempts", "total_time", "percent_incorrect", "percent_incomplete", "is_correct",  "challenge_scale"]]))


df = df.dropna()

print("\n\n Enjoyment Anova test")
loop0 = df[df['loops'] == 0]['enjoyment_scale']
loop1 = df[df['loops'] == 1]['enjoyment_scale']
loop3 = df[df['loops'] == 3]['enjoyment_scale']
loop5 = df[df['loops'] == 5]['enjoyment_scale']


f, p = f_oneway(loop0, loop1, loop3, loop5) 

print(p)

tukey = pairwise_tukeyhsd(endog=df['enjoyment_scale'],
                          groups=df['loops'],
                        alpha=0.05)

print("\n\n Tukey test")
print(tukey)