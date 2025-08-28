import pandas as pd

# Lataa tiedosto, jossa on verkkokauppa2 ennusteet
df_model = pd.read_csv('verkkokauppa_arvostelut2.csv')

# Lataa tiedosto, jossa on tähtien perusteella luodut arvot
df_stars = pd.read_csv('tahtiarvot.csv')

print(f"Verkkokauppa2 ennusteet -tiedostossa on rivejä: {len(df_model)}")
print(f"Tähtien arvot -tiedostossa on rivejä: {len(df_stars)}")
print("\n--- Verkkokauppa2 ennusteet jakauma ---")
print(df_model['tunne'].value_counts())

print("\n--- Tähtien perusteella luotujen arvojen jakauma ---")
print(df_stars['tahtien_tunne'].value_counts())
