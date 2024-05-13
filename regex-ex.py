import re
import os
import pandas as pd

RTDIR = os.path.dirname(__file__)
df = pd.read_csv(filepath_or_buffer=f'{RTDIR}\\valid_guesses.csv', names=["Words"])

pattern = "..ing"

mask = df["Words"].str.contains(pat=pattern, regex=True)
new_df = df[mask].reset_index(drop=True)

print(new_df)
