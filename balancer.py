import pandas as pd

# Lataa aineisto
df = pd.read_csv("yhdistetyt_reviews.csv")

# Varmistetaan että tähdet ovat numeroina
df["tahdet"] = pd.to_numeric(df["tahdet"], errors="coerce")

# Luo uusi sarake tunne-luokalle
def map_tunne(t):
    if pd.isna(t):
        return None
    if t in [1, 2]:
        return "negatiivinen"
    elif t == 3:
        return "neutraali"
    elif t in [4, 5]:
        return "positiivinen"
    return None

df["tunne"] = df["tahdet"].apply(map_tunne)

# Poistetaan rivit joilla ei ole validia luokkaa
df = df.dropna(subset=["tunne"])

# Selvitetään pienimmän luokan koko
min_count = df["tunne"].value_counts().min()
print("Luokkien jakauma ennen tasapainotusta:")
print(df["tunne"].value_counts())
print(f"Pienin luokka: {min_count}")

# Otetaan jokaisesta tunne-luokasta satunnaisesti min_count arvostelua
balanced = (
    df.groupby("tunne", group_keys=False)
      .apply(lambda x: x.sample(n=min_count, random_state=42))
)

# Sekoitetaan rivit satunnaisesti
balanced = balanced.sample(frac=1, random_state=42).reset_index(drop=True)

# Tallennus
balanced.to_csv("tasapainotetut_arvostelut.csv", index=False, encoding="utf-8-sig", quoting=1)

print(f"Tasapainotettu datasetti tallennettu ({len(balanced)} riviä).")
print("Luokkien jakauma tasapainotuksen jälkeen:")
print(balanced['tunne'].value_counts())
