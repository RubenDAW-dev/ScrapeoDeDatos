# -*- coding: utf-8 -*-
import pandas as pd

# ================================
# LISTA OFICIAL DE EQUIPOS FBref
# ================================
equipos = [
    "Real Madrid",
    "Barcelona",
    "Atlético Madrid",
    "Athletic Club",
    "Valencia",
    "Sevilla",
    "Real Sociedad",
    "Villarreal",
    "Real Betis",
    "Osasuna",
    "Celta Vigo",
    "Rayo Vallecano",
    "Getafe",
    "Girona",
    "Mallorca",
    "Levante",
    "Espanyol",
    "Alavés",
    "Elche",
    "Oviedo",
]

# ==========================================================
#  ESTADIOS + CIUDAD + CAPACIDAD (de Transfermarkt) 
#  Datos confirmados literalmente de tu búsqueda
#  https://www.transfermarkt.es/laliga/stadien/wettbewerb/ES1
# ==========================================================
estadios  = [
    "Santiago Bernabéu",
    "Spotify Camp Nou",               # Barcelona juega temporalmente ahí
    "Riyadh Air Metropolitano",
    "San Mamés",
    "Mestalla",
    "Ramón Sánchez-Pizjuán",
    "Reale Arena",
    "La Cerámica",
    "Benito Villamarín",
    "El Sadar",
    "Abanca Balaídos",
    "Estadio de Vallecas",
    "Coliseum",
    "Montilivi",
    "Mallorca Son Moix",
    "Ciutat de València",
    "RCDE Stadium",
    "Mendizorroza",
    "Manuel Martínez Valero",
    "Carlos Tartiere"
]

ciudades = [
    "Madrid",
    "Barcelona",
    "Madrid",
    "Bilbao",
    "Valencia",
    "Sevilla",
    "San Sebastián",
    "Villarreal",
    "Sevilla",
    "Pamplona",
    "Vigo",
    "Madrid",
    "Getafe",
    "Girona",
    "Palma de Mallorca",
    "València",
    "Cornellà de Llobregat",
    "Vitoria-Gasteiz",
    "Elche",
    "Oviedo"
]

capacidades = [
    "83186",
    "55926",
    "70460",
    "53289",
    "49430",
    "43883",
    "39313",
    "23500",
    "60721",
    "23576",
    "24870",
    "14708",
    "16800",
    "14624",
    "26020",
    "26354",
    "40500",
    "19840",
    "31388",
    "30500"
]

# ==========================================
# Construcción del DataFrame final
# ==========================================
df = pd.DataFrame({
    "equipo": equipos,
    "estadio": estadios,
    "ciudad": ciudades,
    "capacidad": capacidades
})

df.to_csv("equipos_final.csv", index=False, encoding="utf-8")
print("🎉 Archivo generado correctamente: equipos_final.csv")
print(df)