import os
import time
import pandas as pd
from langdetect import detect, DetectorFactory

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def _accept_cookies(driver, wait):
    """Hyväksyy/sulkee evästemodaalin, jos se on näkyvissä."""
    try:
        # Jos consent-elementtiä ei tule, palataan heti
        wait.until(EC.presence_of_element_located((By.ID, "consent_block")))
    except Exception:
        return

    selectors_in_order = [
        "button[widget-attachpoint='agree'][rel-widget-id='consent_block']",     # Hyväksy kaikki
        "span[widget-attachpoint='basicAgree'][rel-widget-id='consent_block']",  # Jatka ilman hyväksyntää
        "a.c-modal__close[rel-widget-id='generalModal']",                        # Ruksi
    ]

    for css in selectors_in_order:
        try:
            el = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css)))
            driver.execute_script("arguments[0].click();", el)
            break
        except Exception:
            pass

    # Yritä odottaa, että consent häviää näkyvistä (ei haittaa jos jää DOM:iin)
    try:
        wait.until(EC.invisibility_of_element_located((By.ID, "consent_block")))
    except Exception:
        pass
    time.sleep(0.3)


def scrape_hobbyhall_reviews(
    product_url: str,
    output_csv: str = "hobbyhall_reviews.csv",
    only_finnish: bool = True,
    headless: bool = False,
):
    # --- selainasetukset ---
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--window-size=1280,900")
    chrome_options.add_argument("--lang=fi-FI")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
    )
    if headless:
        chrome_options.add_argument("--headless=new")

    driver = webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()),
        options=chrome_options
    )
    wait = WebDriverWait(driver, 15)

    DetectorFactory.seed = 0  # deterministisempi langdetect

    try:
        driver.get(product_url)

        # 1) evästeet
        _accept_cookies(driver, wait)

        # 2) varmista, että arvostelut ovat DOM:ssa
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.c-review")))
        time.sleep(0.3)

        # 3) jos sivulla on "Näytä lisää" -tyyppinen nappi, klikkaa niin kauan kuin löytyy
        while True:
            try:
                more_btn = driver.find_element(
                    By.XPATH, "//button[contains(., 'Näytä') or contains(., 'lisää')]"
                )
                driver.execute_script("arguments[0].click();", more_btn)
                time.sleep(1.0)
            except Exception:
                break

        # 4) kaiva arvostelut
        reviews = driver.find_elements(By.CSS_SELECTOR, "div.c-review")
        rows = []
        for rv in reviews:
            try:
                author = rv.find_element(By.CSS_SELECTOR, "div.c-review__author").get_text().strip()
            except Exception:
                try:
                    author = rv.find_element(By.CSS_SELECTOR, "div.c-review__author").text.strip()
                except Exception:
                    author = "N/A"

            try:
                date = rv.find_element(By.CSS_SELECTOR, "div.c-review__date").text.strip()
            except Exception:
                date = "N/A"

            try:
                content = rv.find_element(By.CSS_SELECTOR, "div.c-review__content").text.strip()
            except Exception:
                content = "N/A"

            try:
                rating = len(rv.find_elements(By.CSS_SELECTOR, "i.c-icon--star-full.s-is-active"))
            except Exception:
                rating = "N/A"

            lang = "unknown"
            if content not in ("", "N/A"):
                try:
                    lang = detect(content)
                except Exception:
                    lang = "unknown"

            if only_finnish and lang != "fi":
                continue

            rows.append({
                "otsikko" : 'N/A',
                "teksti": content,
                "tahdet": rating,
                "url": product_url,
                "kieli": lang
            })

        df = pd.DataFrame(rows)
        if df.empty:
            print("Ei löytynyt arvosteluja.")
            return df

        # 5) tallenna (append jos tiedosto on jo olemassa)
        if os.path.exists(output_csv):
            df.to_csv(output_csv, mode="a", header=False, index=False, encoding="utf-8-sig")
            print(f"Lisätty {len(df)} arvostelua tiedostoon {output_csv}")
        else:
            df.to_csv(output_csv, index=False, encoding="utf-8-sig")
            print(f"Tallennettu {len(df)} arvostelua tiedostoon {output_csv}")

        return df

    except Exception as e:
        # Selkeä virheilmoitus debugia varten
        print(f"Virhe haussa: {e}")
        return pd.DataFrame()

    finally:
        driver.quit()


# --- KÄYTTÖESIMERKKI ---
if __name__ == "__main__":
    target_url = "https://hobbyhall.fi/fi/review/2981373/3612223#review-10"
    scrape_hobbyhall_reviews(
        product_url=target_url,
        output_csv="hobbyhall_reviews.csv",
        only_finnish=True,
        headless=False
    )
