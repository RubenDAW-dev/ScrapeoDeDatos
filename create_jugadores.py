# -*- coding: utf-8 -*-
import time
from io import StringIO
import pandas as pd
from bs4 import BeautifulSoup, Comment
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

LIGA_PLAYERS_URL = "https://fbref.com/en/comps/12/stats/La-Liga-Stats"
OUT_CSV = "jugadores_laliga.csv"

def flatten_columns(cols):
    """Aplana MultiIndex de pandas.read_html."""
    flat = []
    for c in cols:
        if isinstance(c, tuple):
            c = next((x for x in c[::-1] if x and "Unnamed" not in str(x)), c[-1])
        flat.append(str(c))
    return flat

def find_standard_player_table(html: str):
    """
    Busca la tabla 'Player Standard Stats' (#stats_standard) tanto en DOM
    como dentro de comentarios <!-- ... -->. Devuelve DataFrame o None.
    """
    soup = BeautifulSoup(html, "lxml")
    candidate_html_tables = []

    # 1) Tablas visibles en el DOM
    for table in soup.select("table#stats_standard"):
        candidate_html_tables.append(table.decode())

    # 2) Tablas en comentarios (FBref suele meterlas aquí)
    for c in soup.find_all(string=lambda t: isinstance(t, Comment)):
        txt = str(c)
        # Cubrimos ambos formatos: real y escapado
        if (("<table" in txt and "</table>" in txt) or
            ("&lt;table" in txt and "&lt;/table&gt;" in txt)) and "stats_standard" in txt:
            sub = BeautifulSoup(txt, "lxml")
            for table in sub.select("table#stats_standard"):
                candidate_html_tables.append(table.decode())

    # 3) Convertimos a DataFrame y limpiamos
    for html_tbl in candidate_html_tables:
        try:
            df = pd.read_html(StringIO(html_tbl))[0]
        except ValueError:
            continue
        df.columns = flatten_columns(df.columns)
        if "Player" in df.columns:
            # Quitar cabeceras repetidas que vienen como filas
            df = df[df["Player"].notna()]
            df = df[df["Player"] != "Player"]
        return df

    return None

def clean_player_df(df: pd.DataFrame) -> pd.DataFrame:
    """Limpieza básica/normalización."""
    for col in ["Rk", "Rank", "Ranking"]:
        if col in df.columns:
            df = df.drop(columns=[col])
    rename_map = {
        "Team": "Squad",
        "Equipo": "Squad",
        "Nación": "Nation",
        "País": "Nation",
        "Posición": "Pos",
        "Edad": "Age",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    return df.dropna(how="all").reset_index(drop=True)

def main():
    # 1) Conectar a tu Chrome abierto en 9222
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    driver = webdriver.Chrome(options=options)

    # 2) Navegar a la página de jugadores
    print(f"🌐 Abriendo: {LIGA_PLAYERS_URL}")
    driver.get(LIGA_PLAYERS_URL)

    # 3) Espera breve por si FBref termina de montar la página
    time.sleep(2.0)

    # 4) Capturar el HTML completo de la página renderizada
    html = driver.page_source

    # 5) Extraer la tabla 'Player Standard Stats'
    df = find_standard_player_table(html)
    if df is None or df.empty:
        with open("debug_players.html", "w", encoding="utf-8") as f:
            f.write(html)
        raise RuntimeError(
            "No se pudo localizar la tabla 'stats_standard'. "
            "Se guardó debug_players.html para inspección."
        )

    # 6) Limpiar y exportar
    df = clean_player_df(df)
    df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

    print(f"✅ Archivo creado: {OUT_CSV}")
    print(f"🧍 Total jugadores: {len(df)}")

    # Vistazo rápido
    show_cols = [c for c in ["Player", "Nation", "Pos", "Squad", "Age", "MP", "Min", "Gls", "Ast"] if c in df.columns]
    if show_cols:
        print("\nEjemplo (primeras 15 filas):")
        print(df[show_cols].head(15))

if __name__ == "__main__":
    main()