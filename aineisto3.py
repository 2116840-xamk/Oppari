import csv
import re
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException
from langdetect import detect, DetectorFactory
import os

DetectorFactory.seed = 0
# ---------- apufunktiot ----------

def click_safely(driver, elem):
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", elem)
    time.sleep(0.2)
    try:
        elem.click()
    except Exception:
        driver.execute_script("arguments[0].click();", elem)

def try_handle_cookies(driver):
    # Yritä kuitata Usercentrics (hyväksy tai vain välttämättömät)
    for sel in [
        "button[data-testid='uc-accept-all-button']",
        "button[data-testid='uc-deny-all-button']",
        "//button[normalize-space()='Hyväksy kaikki']",
        "//button[normalize-space()='Vain välttämättömät']",
    ]:
        try:
            if sel.startswith("//"):
                btn = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.XPATH, sel)))
            else:
                btn = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
            click_safely(driver, btn)
            print("Evästeet kuitattu.")
            time.sleep(0.5)
            return
        except TimeoutException:
            continue
    print("Eväste-popup ei tullut näkyviin.")

def find_with_scrolling(driver, by, value, total_timeout=25, step_px=600, settle=0.25):
    """
    Scrollaa porrastetusti alas kunnes elementti löytyy tai aikakatkaisu tulee.
    Palauttaa WebElementin tai nostaa TimeoutException.
    """
    end_time = time.time() + total_timeout
    last_y = -1
    while time.time() < end_time:
        elems = driver.find_elements(by, value)
        visible = [e for e in elems if e.is_displayed()]
        if visible:
            return visible[0]
        # scrollaa alaspäin
        driver.execute_script(f"window.scrollBy(0, {step_px});")
        time.sleep(settle)
        # jos ei enää liiku, kokeile vielä iso hyppy alas ja ylös
        y = driver.execute_script("return window.scrollY;")
        if y == last_y:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.4)
            driver.execute_script("window.scrollBy(0, -300);")
            time.sleep(0.3)
        last_y = y
    raise TimeoutException(f"Elementtiä ei löytynyt: {by}={value}")

def open_reviews_dialog(driver):
    # Etsi "Katso lisää arvioita" ID:llä, muuten tekstillä; scrollaa tarvittaessa
    try:
        btn = find_with_scrolling(driver, By.ID, "reviews-see-more", total_timeout=30)
    except TimeoutException:
        btn = find_with_scrolling(
            driver, By.XPATH, "//button[contains(normalize-space(),'Katso lisää arvioita')]", total_timeout=30
        )
    click_safely(driver, btn)
    print("Avattiin arvosteluikkuna.")
    # Odota että dialogi ja ensimmäiset li:t ilmestyvät
    WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located(
            (By.XPATH, "//div[@role='dialog' and not(starts-with(@id,'uc-'))]//li[@data-index]")
        )
    )

def load_all_reviews_in_dialog(driver, max_clicks=200):
    # Klikkaa "Näytä lisää" kunnes määrä ei enää kasva tai nappi katoaa
    def count_reviews():
        return len(driver.find_elements(By.XPATH, "//div[@role='dialog' and not(starts-with(@id,'uc-'))]//li[@data-index]"))

    last = count_reviews()
    stagnant = 0
    for _ in range(max_clicks):
        try:
            show_more = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//div[@role='dialog' and not(starts-with(@id,'uc-'))]//button[normalize-space()='Näytä lisää' and @aria-disabled='false']")
                )
            )
        except TimeoutException:
            break
        try:
            click_safely(driver, show_more)
        except (ElementClickInterceptedException, StaleElementReferenceException):
            time.sleep(0.6)
            driver.execute_script("arguments[0].click();", show_more)
        time.sleep(1.0)
        try:
            WebDriverWait(driver, 6).until(lambda d: count_reviews() > last)
            last = count_reviews()
            stagnant = 0
            print(f"Ladattu {last} arviota...")
        except TimeoutException:
            stagnant += 1
            if stagnant >= 2:
                break

def extract_reviews(driver, product_url):
    lis = driver.find_elements(By.XPATH, "//div[@role='dialog' and not(starts-with(@id,'uc-'))]//li[@data-index]")
    out = []
    seen = set()
    for li in lis:
        # Varsinainen tekstikappale: li:n SUORA lapsi-p
        text = ""
        try:
            p = li.find_element(By.XPATH, "./p[contains(@class,'text-body-small-regular')]")
            text = re.sub(r"\s+", " ", p.text.strip())
        except NoSuchElementException:
            pass
        if not text:
            continue
        try:
            lang = detect(text)
            if lang != "fi":
                continue
        except Exception:
            continue
        rating = ""
        try:
            val = li.find_element(By.XPATH, ".//p[contains(@class,'values-container')]").text
            m = re.search(r"(\d+)", val)
            if m:
                rating = m.group(1)
        except NoSuchElementException:
            pass

        key = (text, rating)
        if key in seen:
            continue
        seen.add(key)
        out.append({"otsikko": 'N/A', "teksti": text, "arvosana": rating, "url": product_url, "kieli": lang})
    return out

# ---------- pääfunktio ----------

def scrape_prisma_reviews(product_url, output_csv="prisma_reviews.csv"):
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    # Halutessasi: options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(options=options)

    try:
        driver.get(product_url)
        time.sleep(0.8)

        try_handle_cookies(driver)

        # Varmista että sisältöä on ladattu: perusscroll
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
        time.sleep(0.4)

        open_reviews_dialog(driver)

        load_all_reviews_in_dialog(driver)

        reviews = extract_reviews(driver, product_url)
        if os.path.exists(output_csv):
            with open(output_csv, "a", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=["otsikko", "teksti", "arvosana", "url", "kieli"])
                writer.writerows(reviews)
                print(f"Tallennettu {len(reviews)} arvostelua tiedostoon {output_csv}")
        else: 
            with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=["otsikko", "teksti", "arvosana", "url", "kieli"])
                writer.writeheader()
                writer.writerows(reviews)
                print(f"Lisätty {len(reviews)} arvostelua tiedostoon {output_csv}")
    finally:
        driver.quit()

if __name__ == "__main__":
    url = "https://www.prisma.fi/tuotteet/100088384/biolan-pikakompostori-220eco-tummanharmaa-100088384"
    scrape_prisma_reviews(url, "prisma_reviews.csv")
