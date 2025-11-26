import pandas as pd

xlsx_file = r"Datasets\\life_history_traits.xlsx"   # change this path
csv_file  = r"Datasets\\life_history_traits.csv"    # change this path

df = pd.read_excel(xlsx_file)
df.to_csv(csv_file, index=False)

print("Conversion complete!")
