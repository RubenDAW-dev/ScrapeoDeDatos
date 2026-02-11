# -*- coding: utf-8 -*-
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

options = Options()
options.debugger_address = "127.0.0.1:9222"

driver = webdriver.Chrome(options=options)

print("Conectado al Chrome real.")
print("Cuando hayas pasado Cloudflare y se vea la tabla de Fixtures, pulsa ENTER…")
input()

# Seleccionar la tabla correcta de Fixtures
table = driver.find_element(By.CSS_SELECTOR, 'table[id^="sched_"]')

html = table.get_attribute("outerHTML")

df = pd.read_html(html)[0]
df.to_csv("laliga_fixtures.csv", index=False, encoding="utf-8")

print("✔ Archivo generado: laliga_fixtures.csv")