import pandas as pd

df = pd.read_csv("TEAM_STATS_FINAL.CSV")

# Eliminar filas donde NO hay equipos
df = df[~(df["home_team_id"].isna() & df["away_team_id"].isna())]

df.to_csv("TEAM_STATS_FINAL.CSV", index=False)
print("✔ TEAM_STATS_FINAL limpiado")