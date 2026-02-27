import pandas as pd

# Cargar el archivo Excel
archivo ="D:\\Catamarca\\Resumen Banco Fleteros.xlsx"   # reemplazá con el nombre real
df = pd.read_excel(archivo)

# Mostrar las primeras filas
print("Primeras filas del archivo:")
print(df.head())

# Mostrar columnas
print("\nColumnas disponibles:")
print(df.columns)