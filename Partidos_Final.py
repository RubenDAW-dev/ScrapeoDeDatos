# -*- coding: utf-8 -*-
import pandas as pd

INFILE = "laliga_partidos_with_id.csv"     # ← input real
TEAMS  = "equipos_final_ids.csv"           # ← catálogo equipos REAL
OUT    = "PARTIDOS_FINAL.CSV"              # ← output final en MAYÚSCULA

print("🔵 Generando PARTIDOS_FINAL...")

# Cargar partidos
df = pd.read_csv(INFILE)

# Cargar catálogo maestro
teams = pd.read_csv(TEAMS)[["equipo", "team_id"]]

# Merge HOME
df = df.merge(
    teams.rename(columns={"equipo": "Home"}),
    on="Home",
    how="left"
)
df = df.rename(columns={"team_id": "home_team_id"})

# Merge AWAY
df = df.merge(
    teams.rename(columns={"equipo": "Away"}),
    on="Away",
    how="left"
)
df = df.rename(columns={"team_id": "away_team_id"})

# Reordenar
cols_front = ["id", "home_team_id", "away_team_id"]
other_cols = [c for c in df.columns if c not in cols_front and c not in ["Home", "Away"]]
df = df[cols_front + other_cols]

# Guardar archivo final
df.to_csv(OUT, index=False, encoding="utf-8-sig")

print("✔ Archivo generado:", OUT)
print(df.head())