import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from langdetect import detect
import os

driver = webdriver.Chrome()
url = "https://fi.fazer.com/collections/all/products/karl-fazer-rouhea-keksi-suklaalevy-180-g-n"
driver.get(url)

wait = WebDriverWait(driver, 20)

# --- Evästeet ---
try:
    decline_btn = wait.until(EC.element_to_be_clickable((By.ID, "declineButton")))
    decline_btn.click()
    print("Eväste-popup suljettu (kielletty evästeet).")
except:
    try:
        accept_btn = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "coi-banner__accept")))
        accept_btn.click()
        print("Eväste-popup suljettu (hyväksytty evästeet).")
    except:
        print("Eväste-popupia ei löytynyt.")

# --- Arvosteluvälilehti ---
try:
    reviews_tab = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//div[@class='accordion-item']//a[contains(@href,'product-reviews')]"))
    )
    driver.execute_script("arguments[0].scrollIntoView(true);", reviews_tab)
    reviews_tab.click()
    print("Arvosteluvälilehti avattu.")
except:
    print("Arvosteluvälilehteä ei löytynyt.")

all_reviews = []

def scrape_page():
    time.sleep(2)
    reviews = driver.find_elements(By.CSS_SELECTOR, ".lipscore-review-box")
    for review in reviews:
        try:
            text_elem = review.find_element(By.CSS_SELECTOR, ".lipscore-review-text")
            text = text_elem.text.strip()
            if not text:
                continue

            # Kieli: vain suomi
            try:
                if detect(text) != "fi":
                    continue
            except:
                continue

            # --- Haetaan tähdet ---
            stars = len(review.find_elements(
                By.CSS_SELECTOR, ".lipscore-rating-star:not(.lipscore-rating-star-inactive)"
            ))

            # Fallback: etsi span-teksti muodossa "Arvostelun luokitus: 1.0 5:sta tähdestä"
            if stars == 0:
                try:
                    stars_text = review.find_element(
                        By.XPATH, ".//span[contains(text(),'Arvostelun luokitus')]"
                    ).text
                    # esim: "Arvostelun luokitus: 1.0 5:sta tähdestä"
                    stars = int(float(stars_text.split()[2]))
                except:
                    stars = None

            # Otetaan mukaan vain jos tähtiä 1–3
            if text and stars and 1 <= stars <= 3:
                all_reviews.append(["placeholder", text, stars, url, "fi"])

        except:
            continue


# --- Scrape loop ---
while True:
    scrape_page()

    # yritetään seuraavaa sivua
    try:
        paginator = driver.find_element(By.CSS_SELECTOR, ".lipscore-paginator")
        active = paginator.find_element(By.CSS_SELECTOR, "li.active")
        next_li = active.find_element(By.XPATH, "following-sibling::li[1]")

        # jos seuraava on » nappi
        if "next" in next_li.get_attribute("class"):
            next_li.find_element(By.TAG_NAME, "a").click()
        else:
            # klikkaa normaali sivunumero
            next_li.find_element(By.TAG_NAME, "a").click()

        time.sleep(2)
    except:
        break

driver.quit()

# --- CSV ---
if os.path.exists("fazer_reviews.csv"):
    with open("fazer_reviews.csv", "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerows(all_reviews)
        print(f"Lisätty {len(all_reviews)} arvostelua tiedostoon fazer_reviews.csv")
else:
    with open("fazer_reviews.csv", "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerow(["otsikko", "teksti", "tahdet", "url", "kieli"])
        writer.writerows(all_reviews)
        print(f"Luotu uusi CSV ja tallennettu {len(all_reviews)} arvostelua.")
