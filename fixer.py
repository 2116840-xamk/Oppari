import pandas as pd

keratyt = pd.read_csv("keratyt_arvostelut.csv")

# Jos siellä on tunne-sarake → poistetaan
if "tunne" in keratyt.columns:
    keratyt = keratyt.drop(columns=["tunne"])

# Varmistetaan että sarakkeet ovat samat kuin muissa
keratyt.columns = ["otsikko", "teksti", "tahdet", "url", "kieli"]

# Siistitään vielä rivinvaihdot
def clean_text(s):
    if pd.isna(s):
        return ""
    return str(s).replace("\n", " ").replace("\r", " ").strip()

for col in ["otsikko", "teksti"]:
    keratyt[col] = keratyt[col].apply(clean_text)
    
# Varmistetaan että tähdet on numeroina
keratyt["tahdet"] = pd.to_numeric(keratyt["tahdet"], errors="coerce")

# *** Suodatus: vain 1–3 tähden arviot ***
keratyt = keratyt[keratyt["tahdet"].between(1, 3, inclusive="both")]


fazer1 = pd.read_csv("fazer_reviews.csv")
fazer2 = pd.read_csv("fazer_reviews2.csv")
hobby  = pd.read_csv("hobbyhall_reviews.csv")
prisma = pd.read_csv("prisma_reviews.csv")
verkko2 = pd.read_csv("verkkokauppa_arvostelut2.csv")

# Poista tunne verkkokaupasta jos se on mukana
if "tunne" in verkko2.columns:
    verkko2 = verkko2.drop(columns=["tunne"])

# Yhdistä kaikki
frames = [fazer1, fazer2, hobby, prisma, verkko2, keratyt]
merged = pd.concat(frames, ignore_index=True)

# Tallennus
merged.to_csv("yhdistetyt_arvostelut.csv", index=False, encoding="utf-8-sig", quoting=1)
print(f"Yhdistetty {len(merged)} riviä tiedostoon yhdistetyt_arvostelut.csv")
