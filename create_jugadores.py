# -*- coding: utf-8 -*-
import time
from io import StringIO
import pandas as pd
from bs4 import BeautifulSoup, Comment
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# =======================================================
# CONFIG
# =======================================================
LIGA_PLAYERS_URL = "https://fbref.com/en/comps/12/stats/La-Liga-Stats"
OUT_CSV = "jugadores_laliga.csv"


# =======================================================
# HELPERS
# =======================================================

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
    Busca la tabla 'Player Standard Stats' (#stats_standard)
    tanto visible como dentro de comentarios.
    """
    soup = BeautifulSoup(html, "lxml")
    candidate_html_tables = []

    # 1) Tablas visibles
    for table in soup.select("table#stats_standard"):
        candidate_html_tables.append(table.decode())

    # 2) Tablas comentadas (FBref las oculta dentro de <!-- -->)
    for c in soup.find_all(string=lambda t: isinstance(t, Comment)):
        txt = str(c)

        if (
            ("<table" in txt and "</table>" in txt)
            or ("&lt;table" in txt and "&lt;/table&gt;" in txt)
        ) and "stats_standard" in txt:

            sub = BeautifulSoup(txt, "lxml")
            for table in sub.select("table#stats_standard"):
                candidate_html_tables.append(table.decode())

    # 3) Convertir a DataFrame
    for html_tbl in candidate_html_tables:
        try:
            df = pd.read_html(StringIO(html_tbl))[0]
        except Exception:
            continue

        df.columns = flatten_columns(df.columns)

        if "Player" in df.columns:
            df = df[df["Player"].notna()]
            df = df[df["Player"] != "Player"]

        return df

    return None


def clean_player_df(df: pd.DataFrame) -> pd.DataFrame:
    """Limpieza básica y renombrado."""
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


# =======================================================
# MAIN
# =======================================================

def main():
    # 1) Conectar con el Chrome REAL ya abierto
    options = Options()
    options.debugger_address = "127.0.0.1:9222"
    driver = webdriver.Chrome(options=options)

    print("💠 Conectado al Chrome real.")
    print("💠 Abre manualmente esta URL en ese Chrome:")
    print(f"   {LIGA_PLAYERS_URL}")
    print("💠 Cuando la página esté totalmente cargada, pulsa ENTER aquí...")
    input()

    # 2) Capturar HTML de esa página
    html = driver.page_source

    # 3) Buscar tabla de jugadores
    df = find_standard_player_table(html)
    if df is None or df.empty:
        with open("debug_players.html", "w", encoding="utf-8") as f:
            f.write(html)
        raise RuntimeError("No se encontró la tabla #stats_standard. HTML guardado en debug_players.html")

    # 4) Limpieza
    df = clean_player_df(df)

    # 5) Guardar
    df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

    print(f"✅ Archivo creado: {OUT_CSV}")
    print(f"🧍 Total jugadores: {len(df)}")

    # Mostrar columnas relevantes si existen
    show_cols = [c for c in ["Player", "Nation", "Pos", "Squad", "Age", "MP", "Min", "Gls", "Ast"] if c in df.columns]
    if show_cols:
        print("\nEjemplo (primeras 15 filas):")
        print(df[show_cols].head(15))


if __name__ == "__main__":
    main()