"""
Paso 2: Liquidación de comisiones por recaudo efectivo.

Reglas del banco:
  - Recaudo GESTIONADO : recaudo_mes > 0 y al menos un contacto_efectivo = 1.
  - Recaudo ESPONTÁNEO : recaudo_mes > 0 y ningún contacto efectivo (0% comisión).
  - Comisión escalonada sobre el recaudo gestionado, según dias_mora:
        < 30 días        -> 5%
        30 a 60 días     -> 8%   (30 y 60 incluidos en este tramo)
        > 60 días        -> 12%

Uso:  python main.py
Salida: liquidacion_proveedores.csv (junto a este script)
"""
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
RUTA_ASIGNACION = BASE / "data" / "asignacion_cartera.csv"
RUTA_GESTIONES = BASE / "data" / "gestiones_proveedor.csv"
RUTA_SALIDA = BASE / "liquidacion_proveedores.csv"

TASA_MORA_BAJA = 0.05   # < 30 días
TASA_MORA_MEDIA = 0.08  # 30 a 60 días
TASA_MORA_ALTA = 0.12   # > 60 días


def cargar_datos():
    asignacion = pd.read_csv(RUTA_ASIGNACION)
    gestiones = pd.read_csv(RUTA_GESTIONES)
    # Normaliza texto para evitar cruces fallidos por espacios
    asignacion["proveedor"] = asignacion["proveedor"].str.strip()
    gestiones["proveedor"] = gestiones["proveedor"].str.strip()
    return asignacion, gestiones


def contacto_por_obligacion(gestiones: pd.DataFrame) -> pd.DataFrame:
    """Una fila por obligación: evita duplicar recaudos al hacer el merge."""
    return (
        gestiones.groupby("id_obligacion", as_index=False)
        .agg(tuvo_contacto=("contacto_efectivo", "max"))
    )


def clasificar_recaudo(asignacion: pd.DataFrame, contactos: pd.DataFrame) -> pd.DataFrame:
    df = asignacion.merge(contactos, on="id_obligacion", how="left")
    df["tuvo_contacto"] = df["tuvo_contacto"].fillna(0).astype(int)  # sin gestiones = sin contacto

    pago = df["recaudo_mes"] > 0
    df["recaudo_gestionado"] = np.where(pago & (df["tuvo_contacto"] == 1), df["recaudo_mes"], 0.0)
    df["recaudo_espontaneo"] = np.where(pago & (df["tuvo_contacto"] == 0), df["recaudo_mes"], 0.0)
    return df


def calcular_comision(df: pd.DataFrame) -> pd.DataFrame:
    condiciones = [df["dias_mora"] < 30, df["dias_mora"] <= 60]
    df["tasa_comision"] = np.select(condiciones, [TASA_MORA_BAJA, TASA_MORA_MEDIA], default=TASA_MORA_ALTA)
    df["comision"] = df["recaudo_gestionado"] * df["tasa_comision"]
    return df


def liquidar(df: pd.DataFrame) -> pd.DataFrame:
    liq = (
        df.groupby("proveedor", as_index=False)
        .agg(
            recaudo_total=("recaudo_mes", "sum"),
            recaudo_gestionado=("recaudo_gestionado", "sum"),
            recaudo_espontaneo=("recaudo_espontaneo", "sum"),
            comision_a_pagar=("comision", "sum"),
        )
        .round(2)
    )
    # Validación de consistencia: total = gestionado + espontáneo
    assert np.allclose(
        liq["recaudo_total"], liq["recaudo_gestionado"] + liq["recaudo_espontaneo"], atol=0.05
    ), "recaudo_total no cuadra con gestionado + espontáneo"
    return liq


def main():
    asignacion, gestiones = cargar_datos()
    df = clasificar_recaudo(asignacion, contacto_por_obligacion(gestiones))
    df = calcular_comision(df)
    liq = liquidar(df)

    # Control: el recaudo total liquidado debe igualar el del archivo fuente
    assert abs(liq["recaudo_total"].sum() - asignacion["recaudo_mes"].sum()) < 1, "Recaudo total no cuadra con la fuente"

    liq.to_csv(RUTA_SALIDA, index=False)
    pd.options.display.float_format = "{:,.2f}".format
    print(liq.to_string(index=False))
    print(f"\nArchivo generado: {RUTA_SALIDA}")


if __name__ == "__main__":
    main()
