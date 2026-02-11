# -*- coding: utf-8 -*-
import os
import time
from io import StringIO
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

FIXTURES_URL = "https://fbref.com/en/comps/12/schedule/La-Liga-Scores-and-Fixtures"
RAW_FILE = "team_raw.csv"

# ============================
# 1) Cargar partidos ya procesados
# ============================
processed_urls = set()
try:
    prev = pd.read_csv(RAW_FILE)
    if "match_url" in prev.columns:
        processed_urls = set(prev["match_url"].unique())
        print(f"✔ Partidos ya procesados: {len(processed_urls)}")
    else:
        print("⚠ team_raw.csv existe pero sin columna 'match_url'. Ignorando filtrado.")
except FileNotFoundError:
    print("ℹ Primera ejecución: no existe team_raw.csv")

# ============================
# 2) Conectar a Chrome
# ============================
options = Options()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
driver = webdriver.Chrome(options=options)

# ============================
# 3) Cargar fixtures
# ============================
driver.get(FIXTURES_URL)

try:
    fixtures_table = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'table[id^="sched_"]'))
    )
except:
    print("❌ No apareció la tabla de fixtures.")
    print("URL actual:", driver.current_url)
    print("Título:", driver.title)
    raise

# ============================
# 4) Extraer URLs de Match Report
# ============================
rows = fixtures_table.find_elements(By.CSS_SELECTOR, "tbody tr")
match_urls = []
for row in rows:
    try:
        a = row.find_element(By.CSS_SELECTOR, 'td[data-stat="match_report"] a[href*="/matches/"]')
        href = a.get_attribute("href")
        if href:
            match_urls.append(href)
    except:
        pass

match_urls = list(dict.fromkeys(match_urls))
print(f"➡ Partidos con Match Report: {len(match_urls)}")

new_matches = [u for u in match_urls if u not in processed_urls]
print(f"🟦 Partidos nuevos: {len(new_matches)}")
print("-" * 60)

# ============================
# 5) Lector de team_stats + team_stats_extra
# ============================
def extract_table_from_block(block_html: str):
    """Extrae tabla visible o comentada."""
    if "<!--" in block_html:
        block_html = block_html.replace("<!--", "").replace("-->", "")
    try:
        return pd.read_html(StringIO(block_html))[0]
    except:
        return None

def read_combined_team_stats(driver):
    """
    Devuelve un DF combinando:
    - div#team_stats
    - div#team_stats_extra
    """
    df_list = []
    block_ids = ["team_stats", "team_stats_extra"]

    for block in block_ids:
        try:
            container = driver.find_element(By.CSS_SELECTOR, f"div#{block}")
            inner = container.get_attribute("innerHTML")
            df = extract_table_from_block(inner)
            if df is not None:
                df_list.append(df)
        except:
            continue

    if not df_list:
        return None

    return pd.concat(df_list, ignore_index=True)

# ============================
# 6) Guardado incremental (append)
# ============================
def append_to_csv(df):
    exists = os.path.isfile(RAW_FILE)
    df.to_csv(
        RAW_FILE,
        mode="a",
        index=False,
        header=not exists,
        encoding="utf-8"
    )

# ============================
# 7) Scraper principal (GUARDADO POR PARTIDO)
# ============================
for idx, url in enumerate(new_matches, 1):
    print(f"({idx}/{len(new_matches)}) {url}")

    # 1) cargar partido
    try:
        driver.get(url)
    except Exception as e:
        print(f"   ❌ Error cargando: {e}")
        continue

    time.sleep(1.5)

    # 2) extraer stats
    df = read_combined_team_stats(driver)
    if df is None or df.empty:
        print("   ❌ No se pudo leer 'team_stats' ni 'team_stats_extra'. Se salta.")
        continue

    # 3) metadata
    try:
        home_team = driver.find_element(By.CSS_SELECTOR, ".scorebox .team:nth-child(1) strong a").text
        away_team = driver.find_element(By.CSS_SELECTOR, ".scorebox .team:nth-child(2) strong a").text
        score_text = driver.find_element(By.CSS_SELECTOR, ".scorebox .scores").text
        date_text  = driver.find_element(By.CSS_SELECTOR, ".scorebox_meta div").text
    except:
        home_team = away_team = score_text = date_text = None

    df["match_url"] = url
    df["home_team"] = home_team
    df["away_team"] = away_team
    df["score"] = score_text
    df["date"] = date_text

    # 4) GUARDAR YA MISMO
    append_to_csv(df)
    print("   ✔ Guardado en CSV (append)")

    # 5) marcar como procesado
    processed_urls.add(url)

print("\n✅ Terminado.")