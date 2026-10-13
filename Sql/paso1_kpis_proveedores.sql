-- =============================================================================
-- Paso 1: Auditoría y KPIs de gestión por proveedor
-- Compatible con: PostgreSQL, SQLite e Impala (SQL estándar)
-- Tablas: asignacion_cartera, gestiones_proveedor
--
-- Lógica:
--   1) Las gestiones son N por obligación. Se agregan primero a UNA fila por
--      obligación para que el JOIN no duplique saldos (error típico).
--   2) LEFT JOIN desde asignación: las obligaciones sin gestiones se conservan
--      (cuentan en el denominador de cobertura y contactabilidad).
--   3) Los porcentajes se calculan sobre obligaciones asignadas, no sobre gestiones.
-- =============================================================================

WITH gestion_por_obligacion AS (
    SELECT
        id_obligacion,
        COUNT(*) AS n_gestiones,
        MAX(contacto_efectivo) AS tuvo_contacto_efectivo   -- 1 si hubo al menos un contacto
    FROM gestiones_proveedor
    GROUP BY id_obligacion
)
SELECT
    a.proveedor,
    COUNT(*) AS total_obligaciones,
    SUM(a.saldo_asignado) AS saldo_total_asignado,
    -- Tasa de Cobertura (%): obligaciones con >= 1 gestión / obligaciones asignadas
    ROUND(100.0 * SUM(CASE WHEN g.n_gestiones > 0 THEN 1 ELSE 0 END)
                / COUNT(*), 2) AS tasa_cobertura_pct,
    -- Tasa de Contactabilidad (%): obligaciones con >= 1 contacto efectivo / asignadas
    ROUND(100.0 * SUM(CASE WHEN g.tuvo_contacto_efectivo = 1 THEN 1 ELSE 0 END)
                / COUNT(*), 2)                              AS tasa_contactabilidad_pct
FROM asignacion_cartera a
LEFT JOIN gestion_por_obligacion g
       ON a.id_obligacion = g.id_obligacion
GROUP BY a.proveedor
ORDER BY a.proveedor;
