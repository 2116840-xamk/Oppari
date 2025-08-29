import pandas as pd

# Tiedostojen lataus 
df_model = pd.read_csv('mallin_luomat_tunnearvot3.csv')
df_stars = pd.read_csv('tahtiarvot3.csv')

print(f"Mallin ennusteet -tiedostossa on rivejä: {len(df_model)}")
print(f"Tähtien arvot -tiedostossa on rivejä: {len(df_stars)}")
print("\n--- Verkkokauppa2 ennusteet jakauma ---")
print(df_model['mallin_ennuste'].value_counts())

print("\n--- Tähtien perusteella luotujen arvojen jakauma ---")
print(df_stars['tunne'].value_counts())
