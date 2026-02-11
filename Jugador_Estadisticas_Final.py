# -*- coding: utf-8 -*-
import pandas as pd

INFILE  = "jugadores_estadisticas_normalizado.csv"   # ← INPUT REAL
PLAYERS = "jugadores_laliga_ids.csv"                 # ← catálogo jugadores
OUT     = "PLAYER_STATS_FINAL.CSV"                   # ← OUTPUT FINAL

print("🟢 Generando PLAYER_STATS_FINAL...")

# 1) Cargar estadísticas normalizadas de jugadores (tu archivo REAL)
df = pd.read_csv(INFILE)

# 2) Cargar catálogo maestro de jugadores
players = pd.read_csv(PLAYERS)[["Player", "player_id"]]

# 3) Unir player_id por nombre
df = df.merge(players, on="Player", how="left")

# 4) Reordenar columnas (id + player_id + resto)
cols_front = ["id", "player_id"]
other_cols = [c for c in df.columns if c not in cols_front and c != "Player"]

df = df[cols_front + other_cols]

# 5) Guardar archivo FINAL en mayúsculas
df.to_csv(OUT, index=False, encoding="utf-8-sig")

print("✔ Archivo generado:", OUT)
print(df.head())