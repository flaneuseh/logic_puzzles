import matplotlib.pyplot as plt  
import pickle 
from statistics import stdev, mean 
from colorPalette import COLOR5 
from DataVisualization import set_font_sizes 


def format_fits(fits, indexes):
    re_formated = []
    for i in indexes:
        re_formated.append([])
    
    for fit in fits:
        for i in indexes:
            re_formated[i-1] += fit[i -1]
    return re_formated 



def avg_std(ratios, indexes):

    re_formated = []
    for i in indexes:
        re_formated.append([])

    for r in ratios:
        for i in indexes:
            re_formated[i - 1].append(r[i- 1])
    
    avgs = [mean(li) for li in re_formated]
    stds = [stdev(li) for li in re_formated]
    return avgs, stds 



set_font_sizes(14,16,18)
ratios = pickle.load( open("MutationData/ratios.p", "rb" ) )
fits = pickle.load( open("MutationData/fits.p", "rb" ) )

mutations = list(range(1, 6))
avgs, stds = avg_std(ratios, mutations)

print(avgs)
print(stds)


plt.bar(mutations, avgs, color = COLOR5, yerr = stds, capsize=4)
plt.title("Amount of feasible indivuals after mutations")
plt.ylabel("Ratio of feasible indivuals")
plt.xlabel("Number of mutations")
plt.ylim(0,1)
plt.show()

formated_fits = format_fits(fits, mutations)

avg_fits = [mean(li) for li in formated_fits]
print(avg_fits)

max_fits = [max(li) for li in formated_fits]
print(max_fits)

min_fits = [min(li) for li in formated_fits]
print(min_fits)

figure, axis = plt.subplots(nrows=5, ncols=1, sharex=True, sharey=True)
figure.suptitle("Histograms of Infeasible Fitness After Mutation")
#figure.ylabel("Number of indivuals")
plt.xlim(0,1)

axis[0].hist(formated_fits[0], bins=20) 
axis[0].set_ylabel("1 Mutation")


axis[1].hist(formated_fits[1], bins=20) 
axis[1].set_ylabel("2 Mutations")

axis[2].hist(formated_fits[2], bins=20) 
axis[2].set_ylabel("3 Mutations")

axis[3].hist(formated_fits[3], bins=20) 
axis[3].set_ylabel("4 Mutations")

axis[4].hist(formated_fits[4], bins=20) 
axis[4].set_ylabel("5 Mutations")
axis[4].set_xlabel("Infeasible Fitness")


plt.show()

