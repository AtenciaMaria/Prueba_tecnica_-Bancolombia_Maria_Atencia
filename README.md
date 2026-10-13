# Prueba Técnica: Practicante de Analítica, Gerencia Canales de Cobranza

**Maria Fernanda Atencia Oliva, Ingeniería de Sistemas**

Auditoría de la gestión de proveedores externos de cobranza (Deskonecta, Telepromesa y A-ETXA), medición de sus indicadores operativos y liquidación de comisiones sobre el recaudo atribuible a su gestión.

---

## 1. Descripción de lo que se hizo

1. **Exploración de datos (EDA):** se revisó la calidad de los dos CSV (nulos, duplicados, llaves, consistencia entre tablas, tramos de mora) antes de calcular cualquier indicador.
2. **Paso 1, KPIs de gestión (SQL):** una consulta que cruza la asignación con las gestiones y calcula, por proveedor, el número de obligaciones, el saldo asignado, la tasa de cobertura y la tasa de contactabilidad.
3. **Paso 2, liquidación de comisiones (Python):** un script que clasifica el recaudo en *gestionado* o *espontáneo*, aplica la comisión escalonada según los días de mora y exporta la liquidación por proveedor.
4. **Paso 3, conclusiones:** análisis de costo-eficiencia y propuesta de indicadores para el tablero de seguimiento (sección 5).

## 2. Estructura del repositorio

```
Prueba_tecnica_-Bancolombia_Maria_Atencia/
├── data/
│   ├── asignacion_cartera.csv
│   └── gestiones_proveedor.csv
├── Sql/
│   ├── eda.py                         # Exploración y calidad de datos
│   ├── eda_reporte.txt                # Salida del EDA
│   └── paso1_kpis_proveedores.sql     # Paso 1
├── main.py                            # Paso 2
├── liquidacion_proveedores.csv        # Resultado del Paso 2
├── requirements.txt
└── README.md                       # Documentación y conclusiones (Paso 3)
```

## 3. Cómo ejecutar

```bash
pip install -r requirements.txt
python eda.py     # imprime el análisis y genera eda_reporte.txt
python main.py    # genera liquidacion_proveedores.csv
```

La consulta SQL (`sql/paso1_kpis_proveedores.sql`) usa SQL estándar y corre en PostgreSQL, SQLite o Impala. Las tablas deben llamarse `asignacion_cartera` y `gestiones_proveedor`. Los resultados de la consulta se validaron contra el cálculo en Python y coinciden.

## 4. Metodología, supuestos y resultados

### Decisiones de diseño
- **Una fila por obligación antes del cruce.** Cada obligación puede tener varias gestiones. Si se hiciera el JOIN directo, los saldos y recaudos se duplicarían. Por eso las gestiones se agregan primero (número de gestiones y `MAX(contacto_efectivo)`) y luego se cruzan con un `LEFT JOIN` desde la asignación.
- **Las obligaciones sin gestión se conservan.** Cuentan en el denominador de cobertura y contactabilidad, y se tratan como sin contacto efectivo.
- **Los porcentajes se calculan sobre obligaciones asignadas**, no sobre el número de gestiones.
- **Comisión por obligación.** Cada obligación usa la tasa de su propio tramo de mora y luego se suma por proveedor.
- **Validaciones en el código:** `recaudo_total = recaudo_gestionado + recaudo_espontaneo`, y el recaudo total liquidado es igual al del archivo fuente.

### Reglas de liquidación aplicadas

| Concepto | Regla |
|---|---|
| Recaudo gestionado | `recaudo_mes > 0` y al menos un `contacto_efectivo = 1` |
| Recaudo espontáneo | `recaudo_mes > 0` sin ningún contacto efectivo (0% de comisión) |
| Mora < 30 días | 5% sobre el recaudo gestionado |
| Mora de 30 a 60 días | 8% sobre el recaudo gestionado |
| Mora > 60 días | 12% sobre el recaudo gestionado |

### Resultados

**KPIs de gestión (Paso 1)**

| Proveedor | Obligaciones | Saldo asignado | Cobertura | Contactabilidad |
|---|---|---|---|---|
| A-ETXA | 400 | 6.872,4 M | 80,00% | 36,50% |
| Deskonecta | 374 | 6.905,4 M | 78,61% | 43,32% |
| Telepromesa | 426 | 7.665,7 M | 77,23% | 48,59% |

**Liquidación (Paso 2)**

| Proveedor | Recaudo total | Recaudo gestionado | Recaudo espontáneo | Comisión a pagar |
|---|---|---|---|---|
| A-ETXA | 679.893.187,39 | 300.532.304,39 | 379.360.883,00 | 17.146.951,83 |
| Deskonecta | 653.225.095,49 | 306.423.804,22 | 346.801.291,27 | 19.323.273,41 |
| Telepromesa | 843.617.377,82 | 400.570.176,89 | 443.047.200,93 | 26.513.414,74 |

Indicadores derivados:

| Proveedor | Recaudo gestionado / comisión | % recaudo espontáneo | Comisión / recaudo gestionado |
|---|---|---|---|
| A-ETXA | 17,53 | 55,80% | 5,71% |
| Deskonecta | 15,86 | 53,09% | 6,31% |
| Telepromesa | 15,11 | 52,52% | 6,62% |

## 5. Conclusiones y visión de negocio

**Eficiencia de proveedores.** A-ETXA fue el proveedor más costo-eficiente: generó 17,5 pesos de recaudo gestionado por cada peso de comisión, frente a 15,9 de Deskonecta y 15,1 de Telepromesa. Parte de esa ventaja viene de su cartera, ya que el 76,7% de su recaudo gestionado está en mora menor a 30 días, el tramo que paga la tasa más baja (5%). A-ETXA también es el proveedor con mayor dependencia de recaudo espontáneo: 55,8% de su recaudo total (53,1% en Deskonecta y 52,5% en Telepromesa). Esto es coherente con su contactabilidad, la más baja de los tres (36,5%), pese a tener la mayor cobertura (80%): gestiona más cuentas, pero logra hablar con menos titulares. En los tres casos más de la mitad del recaudo es espontáneo y no genera comisión.

**Tablero de control.** En la cabecera del reporte mensual pondría tres indicadores comparados por proveedor: (1) **recaudo gestionado sobre saldo asignado**, que mide el resultado atribuible a la gestión; (2) **tasa de contactabilidad**, con la cobertura como apoyo, que mide la calidad de la gestión; y (3) **costo de cobranza** (comisión sobre recaudo gestionado), que mide la eficiencia del gasto. En el cuerpo del reporte agregaría el porcentaje de recaudo espontáneo y filtros por mes, tramo de mora y canal.


## 6. Uso de Inteligencia Artificial

Utilicé **Claude** (Anthropic) como apoyo en el proceso, principalmente para la **gestión y corrección de errores** del código y para la **documentación de los archivos** (comentarios del código y este README). La lógica de negocio, la interpretación de los resultados y las conclusiones fueron revisadas y validadas por mí.
