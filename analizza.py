import pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns

sns.set_theme()

enti = pd.read_csv("enti.csv")
d = pd.read_csv("entiRes.csv", header=None)
d.columns = ("Codice_IPA", "score")

d1 = d[d["score"] > 0]
