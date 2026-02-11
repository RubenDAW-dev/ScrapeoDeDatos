import pandas as pd

df = pd.read_csv("PLAYER_STATS_FINAL.CSV")

# Eliminar filas TOTAL (las que no tienen player_id)
df = df[df["player_id"].notna()]

df.to_csv("PLAYER_STATS_FINAL.CSV", index=False)
print("✔ PLAYER_STATS_FINAL limpiado")