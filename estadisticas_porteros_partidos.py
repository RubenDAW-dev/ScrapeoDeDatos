# -*- coding: utf-8 -*-
"""
Scraper SOLO de PORTEROS (FBref — LaLiga)
- Extrae keeper_stats_<hash>
- Extrae keeper_adv_stats_<hash>
- Descomenta HTML
- Hace merge por Player + team + match_url
- Guarda incrementalmente en goalkeeper_raw.csv
"""

import os
import time
import re
import pandas as pd
from io import StringIO

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# =========================
# CONFIG
# =========================
FIXTURES_URL = "https://fbref.com/en/comps/12/schedule/La-Liga-Scores-and-Fixtures"
GK_FILE = "goalkeeper_raw.csv"

WAIT_FIXTURES_SEC = 25
WAIT_PARTIDO_SEC = 20


# =========================
# UTILIDADES
# =========================

def flatten(df):
    """Aplana MultiIndex en columnas simples."""
    if isinstance(df.columns, pd.MultiIndex):
        cols = []
        for col in df.columns:
            parts = [str(x) for x in col if not (pd.isna(x) or "Unnamed" in str(x))]
            cols.append("_".join(parts) if parts else col[-1])
        df.columns = cols
    else:
        df.columns = [str(c) for c in df.columns]
    return df


def uncomment(html: str) -> str:
    """Elimina comentarios HTML para dejar las tablas visibles a read_html."""
    return re.sub(r"<!--|-->", "", html)


def save_gk(df):
    """Guardar incremental en goalkeeper_raw.csv"""
    exists = os.path.exists(GK_FILE) and os.path.getsize(GK_FILE) > 0

    df.to_csv(
        GK_FILE,
        mode="a" if exists else "w",
        index=False,
        header=not exists,
        encoding="utf-8"
    )
    print(f"   💾 Guardadas {len(df)} filas en {GK_FILE}")


# =========================
# EXTRACCIÓN DE PORTEROS
# =========================

def extract_gk_tables(page_source: str):
    """
    Devuelve dict:
      - basic → keeper_stats_<hash>
      - adv   → keeper_adv_stats_<hash>
    """
    html = uncomment(page_source)

    # ---- TABLAS BÁSICAS (keeper_stats_<hash>) ----
    basic = []
    for m in re.finditer(r'(<table[^>]+id="keeper_stats_([^"]+)"[^>]*>.*?</table>)',
                         html, re.DOTALL):

        table_html = m.group(1)
        team_hash = m.group(2)

        try:
            df = pd.read_html(StringIO(table_html))[0]
            df = flatten(df)

            if "Player" not in df.columns:
                continue

            df = df[df["Player"].notna()]
            df = df[~df["Player"].isin(["", "Player", "Starting XI", "Bench"])]

            if df.empty:
                continue

            df["team"] = team_hash
            basic.append(df)

        except Exception as e:
            print(f"   ⚠️ Error tabla básica {team_hash}: {e}")

    df_basic = pd.concat(basic, ignore_index=True) if basic else None

    # ---- TABLAS AVANZADAS (keeper_adv_stats_<hash>) ----
    adv = []
    for m in re.finditer(r'(<table[^>]+id="keeper_adv_stats_([^"]+)"[^>]*>.*?</table>)',
                         html, re.DOTALL):

        table_html = m.group(1)
        team_hash = m.group(2)

        try:
            df = pd.read_html(StringIO(table_html))[0]
            df = flatten(df)

            if "Player" not in df.columns:
                continue

            df = df[df["Player"].notna()]
            df = df[~df["Player"].isin(["", "Player", "Starting XI", "Bench"])]

            if df.empty:
                continue

            df["team"] = team_hash
            adv.append(df)

        except Exception as e:
            print(f"   ⚠️ Error tabla avanzada {team_hash}: {e}")

    df_adv = pd.concat(adv, ignore_index=True) if adv else None

    return {"basic": df_basic, "adv": df_adv}


def merge_gk(df_basic, df_adv, match_url):
    """Une basic + adv por Player + team + match_url."""
    if df_basic is None or df_basic.empty:
        return None

    df_basic = df_basic.copy()
    df_basic["match_url"] = match_url

    if df_adv is None or df_adv.empty:
        return df_basic

    df_adv = df_adv.copy()
    df_adv["match_url"] = match_url

    # prefijo para columnas avanzadas
    rename_map = {c: f"adv_{c}" for c in df_adv.columns
                  if c not in ["Player", "team", "match_url"]}
    df_adv = df_adv.rename(columns=rename_map)

    merged = pd.merge(
        df_basic,
        df_adv,
        on=["Player", "team", "match_url"],
        how="left"
    )

    return merged


# =========================
# PROCESO PRINCIPAL
# =========================

def main():

    print("🚀 Scraper SOLO porteros iniciado...")

    # Chrome debugger mode (9222)
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    from selenium.webdriver.chrome.service import Service

    service = Service()
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(FIXTURES_URL)

    WebDriverWait(driver, WAIT_FIXTURES_SEC).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "table[id^='sched_']"))
    )

    rows = driver.find_elements(By.CSS_SELECTOR, "table[id^='sched_'] tbody tr")

    match_urls = []
    for r in rows:
        try:
            a = r.find_element(By.CSS_SELECTOR, 'td[data-stat="match_report"] a')
            match_urls.append(a.get_attribute("href"))
        except:
            pass

    match_urls = list(dict.fromkeys(match_urls))
    print(f"📌 Partidos detectados: {len(match_urls)}")

    total = 0

    for i, url in enumerate(match_urls, 1):
        print(f"\n({i}/{len(match_urls)}) {url}")

        driver.get(url)
        time.sleep(1.2)

        # asegurar carga mínima
        try:
            WebDriverWait(driver, WAIT_PARTIDO_SEC).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".scorebox"))
            )
        except:
            print("   ⚠️ Scorebox no cargó; continuar...")
            continue

        html = driver.page_source

        gk = extract_gk_tables(html)
        df_basic = gk["basic"]
        df_adv = gk["adv"]

        if df_basic is None:
            print("   ❌ No se encontró tabla keeper_stats_*")
            continue

        df = merge_gk(df_basic, df_adv, url)

        save_gk(df)
        total += len(df)

    print(f"\n🎉 Finalizado. Total porteros extraídos: {total}")


if __name__ == "__main__":
    main()