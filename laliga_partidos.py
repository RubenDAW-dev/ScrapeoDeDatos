# -*- coding: utf-8 -*-
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# =====================================================
#     CONECTAR A CHROME YA ABIERTO (9222)
# =====================================================

options = Options()
options.debugger_address = "127.0.0.1:9222"

driver = webdriver.Chrome(options=options)

print("Conectado al Chrome real.")
print("Cuando veas la tabla de LaLiga en FBref, pulsa ENTER…")
input()

# =====================================================
#     OBTENER LA TABLA PRINCIPAL DE FIXTURES
# =====================================================

table = driver.find_element(By.CSS_SELECTOR, 'table[id^="sched_"]')
html = table.get_attribute("outerHTML")

df = pd.read_html(html)[0]

print("✔ Tabla encontrada. Procesando datos...")

# =====================================================
#     LIMPIEZA Y NORMALIZADO
# =====================================================

# Asegurar columnas estándar
if "Score" not in df.columns:
    df["Score"] = None

# Extraer goles si Score viene así: "2–1"
def parse_score(score):
    if isinstance(score, str) and "–" in score:
        try:
            h, a = score.split("–")
            return int(h), int(a)
        except:
            return None, None
    return None, None

df["HomeGoals"], df["AwayGoals"] = zip(*df["Score"].apply(parse_score))

# =====================================================
#     GUARDAR ARCHIVO FINAL
# =====================================================

df.to_csv("laliga_partidos.csv", index=False, encoding="utf-8-sig")

print("✔ Archivo actualizado: laliga_partidos.csv")
print(df.head())