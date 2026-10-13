"""
EDA de asignacion_cartera.csv y gestiones_proveedor.csv.
Revisa calidad de datos y hallazgos que afectan el SQL y la liquidación.

Uso:  python eda.py        (genera también eda_reporte.txt)
"""
import sys
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent
RUTA_DATOS = BASE.parent / "data"
RUTA_ASIGNACION = RUTA_DATOS / "asignacion_cartera.csv"
RUTA_GESTIONES = RUTA_DATOS / "gestiones_proveedor.csv"
RUTA_REPORTE = BASE / "eda_reporte.txt"

pd.options.display.float_format = "{:,.2f}".format
pd.options.display.width = 140


def titulo(txt):
    print(f"\n{'=' * 70}\n{txt}\n{'=' * 70}")


def eda_tabla(df, nombre):
    titulo(f"{nombre}: estructura")
    print(f"Filas: {len(df):,} | Columnas: {df.shape[1]}")
    print(df.dtypes.to_string())
    print("\nNulos por columna:")
    print(df.isna().sum().to_string())
    print(f"\nFilas totalmente duplicadas: {df.duplicated().sum()}")
    print("\nMuestra:")
    print(df.head(5).to_string(index=False))


def main():
    a = pd.read_csv(RUTA_ASIGNACION)
    g = pd.read_csv(RUTA_GESTIONES)

    eda_tabla(a, "asignacion_cartera")
    eda_tabla(g, "gestiones_proveedor")

   
    resumen = base.groupby("proveedor").agg(
        obligaciones=("id_obligacion", "count"),
        cobertura_pct=("n_gestiones", lambda s: (s > 0).mean() * 100),
        contactabilidad_pct=("contacto", lambda s: (s == 1).mean() * 100),
        gestiones_prom_por_obl=("n_gestiones", "mean"),
        recaudo_total=("recaudo_mes", "sum"),
    )



class Tee:
    """Imprime en consola y guarda el reporte en archivo."""
    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for s in self.streams:
            s.write(data)

    def flush(self):
        for s in self.streams:
            s.flush()


if __name__ == "__main__":
    with open(RUTA_REPORTE, "w", encoding="utf-8") as f:
        sys.stdout = Tee(sys.__stdout__, f)
        main()
        sys.stdout = sys.__stdout__
    print(f"\nReporte guardado en: {RUTA_REPORTE}")
