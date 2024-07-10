
import pandas as pd 
import numpy as np 
from scipy.stats import f_oneway, spearmanr
from statsmodels.stats.multicomp import pairwise_tukeyhsd
import scipy.stats 
import matplotlib.pyplot as plt
from sklearn.metrics import r2_score 
import statsmodels.api as sm 
from statsmodels.formula.api import ols  
from statsmodels.stats.multicomp import pairwise_tukeyhsd
import seaborn as sns 
COLOR1 = "#BFDBED"
COLOR2 = "#F89C3A"
COLOR3 = "#98A253"
COLOR4 = "#715B70"
COLOR5 = "#014550"

def quad_reg(df, column1, column2, title, column1_name, column2_name):
    model = np.poly1d(np.polyfit(df[column1], 
                             df[column2], 2)) 
    
    # r square metric 
    print("r score:" , r2_score(df[column2],  
               model(df[column1]))) 
    
    formula = "{} ~ model({})".format(column2, column1)
    results = ols(formula=formula, data=df).fit()
    #print(results.summary())
    #print("p-value", results.pvalues[1])
  
    # polynomial line visualization 
    polyline = np.linspace(1, 7, 100) 
    plt.ylim(1,7.2)
    plt.title(title) 
    plt.ylabel(column2_name)
    plt.xlabel(column1_name) 
    plt.scatter(df[column1], df[column2]) 
    plt.plot(polyline, model(polyline)) 
    plt.show() 
    
def plot_correlation(df, col1, col2, title, co1_name, col2_name):
    sns.stripplot(x=col2, y=col1, data=df, jitter=True)
    sns.despine()
    #bp.get_figure().gca().set_title("")
    plt.suptitle("")
    plt.title(title)
    plt.ylabel(co1_name)
    plt.xlabel(col2_name)
    plt.show()

def plot_violin(df, col1, title, co1_name, col2_name):
    sns.violinplot(x = 'loops', y = col1, data=df, color = COLOR4, cut = 0, inner=None)

    plt.suptitle("")
    plt.title(title)
    plt.ylabel(co1_name)
    plt.xlabel(col2_name)
    #plt.ylim(0, 1)

    plt.show()





df = pd.read_csv("UserData/game_play_data_full.csv")
df = df[df["user"] != "Tvx6ixeKw4hH3EzPyMpteMW1krr1"]
df = df.replace(-1,np.NaN)
print("total puzzle instances:", len(df))
df["loops"] = df["loops"] + 1
df2 = df.dropna()

df["percent_incorrect"] = df["num_incorrect"] / (df["num_correct"] + df["num_incorrect"])
df["percent_correct"] = df["num_incorrect"] / (df["num_correct"] + df["num_incorrect"])
df["total_time_seconds"]  = df["total_time"] / 1000 
df["total_time_minutes"]  = df["total_time_seconds"] / 60
df_small = df[df["total_time_minutes"] <60]
print("puzzles under an hour:", len(df_small))

df["percent_incomplete"] = (48 - df["num_correct"]) / 48 
print(df["total_time_minutes"].mean())
print(df["total_time_minutes"].std())
print(df["total_time_minutes"].median())

print("Loop Correlation")
#print(df[["loops", "attempts", "total_time", "percent_incorrect", "percent_incomplete", "is_correct",  "challenge_scale"]].corr(method = "spearman"))
behaviors = ["attempts", "total_time", "percent_incorrect", "percent_correct", "num_correct", "percent_incomplete", "is_correct"]
for i in behaviors:
    results = scipy.stats.spearmanr(df["loops"], df[i])
    print("\tBehavior:{}, corr:{}, p:{}".format(i , results.correlation, results.pvalue))



results = scipy.stats.spearmanr(df2["loops"], df2["challenge_scale"])
print("\tSubjective:{}, corr:{}, p:{}".format("subjective difficulty" , results.correlation, results.pvalue))


plot_violin(df2, "challenge_scale", "Subjective difficulty by solver loops", "Subjective Difficulty", "Solver Loops")
plot_violin(df, "is_correct", "Correctness by solver loops", "Correctness (0 or 1)", "Solver Loops")
print("Sub diff mean:{}, std:{}, median;{}".format(df[ "challenge_scale"].mean(), df[ "challenge_scale"].std(), df["challenge_scale"].median()))
print("Correct mean:{}, std:{}, median:{}".format(df["is_correct"].mean(), df["is_correct"].std(), df["is_correct"].median()))


for i in [1,2,4,6]:
    sub_df = df[df["loops"] == i]
    print("{}:".format(i))
    print("\t Sub diff mean:{}, std:{}, median;{}".format(sub_df[ "challenge_scale"].mean(), sub_df[ "challenge_scale"].std(), sub_df["challenge_scale"].median()))
    print("\t Correct mean:{}, std:{}, median:{}".format(sub_df["is_correct"].mean(), sub_df["is_correct"].std(), sub_df["is_correct"].median()))


# quad regression subjective enjoyment and subjective difficulty 
print("Inverted U tests")

quad_reg(df2, "challenge_scale", 'enjoyment_scale', "Subjective difficulty by Enjoyment", "Subjective Difficulty", "Enjoyment")

novice = df2[df2["user_category"] == "novice"]
general =  df2[df2["user_category"] == "intermediate"]
specific = df2[df2["user_category"] == "expert"]


quad_reg(novice, "challenge_scale", 'enjoyment_scale', "Novice Users", "Subjective Difficulty", "Enjoyment")

quad_reg(general, "challenge_scale", 'enjoyment_scale', "Users with general puzzle experience", "Subjective Difficulty", "Enjoyment")
quad_reg(specific, "challenge_scale", 'enjoyment_scale', "Users with specific puzzle experience", "Subjective Difficulty", "Enjoyment")


print("User category anova")
cw_lm=ols('challenge_scale ~ C(user_category) + C(loops) + C(user_category):C(loops)', data=df2).fit() #Specify C for Categorical
print(sm.stats.anova_lm(cw_lm, typ=2))

tukey = pairwise_tukeyhsd(endog=df2["challenge_scale"],
                          groups=df2["user_category"],
                          alpha=0.05)
print(tukey)

tukey = pairwise_tukeyhsd(endog=df2["challenge_scale"],
                          groups=df2["loops"],
                          alpha=0.05)
print(tukey)

tukey = pairwise_tukeyhsd(endog=df2["challenge_scale"],
                          groups=df2["user_by_loops"],
                          alpha=0.05)
print(tukey)