import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from langdetect import detect, DetectorFactory
import os

def scrape_verkkokauppa_reviews(product_url, max_pages=5):
    """
    Kerää arvosteluja Verkkokaupan tuotteista.
    """
    reviews_list = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

    for page in range(1, max_pages + 1):
        # Muodostetaan URL sivunumeron kanssa
        url_with_page = f"{product_url}?page={page}"
        print(f"Kerätään dataa sivulta: {url_with_page}")

        try:
            response = requests.get(url_with_page, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            review_containers = soup.find_all('article', class_='review-content')

            if not review_containers:
                print("Ei löytynyt enempää arvosteluja, lopetetaan.")
                break
            DetectorFactory.seed = 0  # tekee tuloksista toistettavia

            for review in review_containers:
                # Otsikko
                title_element = review.find('h2', class_='review-title__title')
                title = title_element.get_text(strip=True) if title_element else 'N/A'

                # Teksti
                text_element = review.find('div', class_='sc-hgRRfv bMWdIZ')
                text = text_element.get_text(strip=True) if text_element else 'N/A'

                lang = 'unknown'
                try:
                    if text and text != 'N/A':
                        lang = detect(text)
                except Exception:
                    lang = 'unknown'

                # Skippaa jos ei suomea
                if lang != 'fi':
                    continue

                # Tähtiarvio
                rating_element = review.find('div', attrs={'percentage': True})
                stars = None
                if rating_element:
                    perc = rating_element.get('percentage')
                    if perc:
                        try:
                            stars = int(round(float(perc) / 20))  # skaalaa 0–100% → 0–5
                        except ValueError:
                            stars = None

                if stars is None:
                    continue

                # Otetaan vain arvostelut joilla 3 tähteä tai alle
                if stars <= 3:
                    tunne = 'negatiivinen' if stars < 3 else 'neutraali'
                    reviews_list.append({
                        'otsikko': title,
                        'teksti': text,
                        'tahdet': stars,
                        'url': url_with_page,
                        'kieli': lang,
                        'tunne': tunne
                    })

        except requests.exceptions.RequestException as e:
            print(f"Virhe sivun noutamisessa: {e}")
            break

        time.sleep(2)  # KOHTELIAS VIIVE

    return pd.DataFrame(reviews_list)

# --- KÄYTTÖESIMERKKI ---
target_product_url = "https://www.verkkokauppa.com/fi/product/814390/JBL-Reflect-Aero-TWS-vastamelunappikuulokkeet-valkoinen/reviews" 

scraped_df = scrape_verkkokauppa_reviews(target_product_url, max_pages=50)

csv_file = "keratyt_arvostelut.csv"

if not scraped_df.empty:
    if os.path.exists(csv_file):
        # Lue olemassa oleva ja yhdistä
        old_df = pd.read_csv(csv_file, encoding="utf-8-sig")
        combined = pd.concat([old_df, scraped_df], ignore_index=True)
        # Poista duplikaatit tekstin perusteella
        combined.drop_duplicates(subset=["teksti"], inplace=True)
        combined.to_csv(csv_file, index=False, encoding="utf-8-sig")
        print(f"\nYhdistetty ja tallennettu {len(combined)} uniikkia arvostelua tiedostoon {csv_file}")
    else:
        scraped_df.drop_duplicates(subset=["teksti"], inplace=True)
        scraped_df.to_csv(csv_file, index=False, encoding="utf-8-sig")
        print(f"\nTallennettu {len(scraped_df)} uniikkia arvostelua tiedostoon {csv_file}")
