# -*- coding: utf-8 -*-
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

options = Options()
options.debugger_address = "127.0.0.1:9222"
driver = webdriver.Chrome(options=options)

print("Conectado al Chrome real.")
print("Cuando veas la tabla de LaLiga en FBref, pulsa ENTER…")
input()

# Obtener HTML completo via page_source
html = driver.page_source
soup = BeautifulSoup(html, "html.parser")

table = soup.find("table", id="sched_2025-2026_12_1")

if table is None:
    print("❌ Tabla no encontrada")
else:
    print("✔ Tabla encontrada. Procesando...")
    df = pd.read_html(str(table))[0]

    # =====================================================
    #     LIMPIEZA
    # =====================================================

    if "Score" not in df.columns:
        df["Score"] = None

    def parse_score(score):
        if isinstance(score, str) and "–" in score:
            try:
                h, a = score.split("–")
                return int(h), int(a)
            except:
                return None, None
        return None, None

    df["HomeGoals"], df["AwayGoals"] = zip(*df["Score"].apply(parse_score))

    df.to_csv("laliga_partidos.csv", index=False, encoding="utf-8-sig")
    print("✔ Archivo guardado: laliga_partidos.csv")
    print(df.head())