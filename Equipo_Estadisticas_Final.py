# -*- coding: utf-8 -*-
import pandas as pd

INFILE = "normalized_estadisticas_equipos_with_id.csv"   # Input real
TEAMS  = "equipos_final_ids.csv"                         # Catálogo real
OUT    = "TEAM_STATS_FINAL.CSV"                          # Output final

print("🔵 Generando TEAM_STATS_FINAL...")

# Cargar stats por partido
df = pd.read_csv(INFILE)

# Cargar catálogo equipo -> team_id
teams = pd.read_csv(TEAMS)[["equipo", "team_id"]]

# Unir team_id para local
df = df.merge(
    teams.rename(columns={"equipo": "home_team"}),
    on="home_team",
    how="left"
)
df = df.rename(columns={"team_id": "home_team_id"})

# Unir team_id para visitante
df = df.merge(
    teams.rename(columns={"equipo": "away_team"}),
    on="away_team",
    how="left"
)
df = df.rename(columns={"team_id": "away_team_id"})

# Reordenar columnas
cols_front = ["id", "home_team_id", "away_team_id"]
other_cols = [c for c in df.columns if c not in cols_front 
              and c not in ["home_team", "away_team"]]

df = df[cols_front + other_cols]

# Guardar archivo FINAL
df.to_csv(OUT, index=False, encoding="utf-8-sig")

print("✔ Archivo generado:", OUT)
print(df.head())