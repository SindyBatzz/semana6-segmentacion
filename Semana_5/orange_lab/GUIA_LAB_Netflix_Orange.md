# Lab de Orange (aprox. 60 min): ¿qué palanca del CLV vale más en Netflix?

**Qué van a hacer:** abrir los datos, arrastrar widgets y responder preguntas del negocio. Casi no hay código: solo escribir fórmulas cortas.

## Antes de empezar

**Datos: reales y simulados**
| Archivo | Qué es |
|---|---|
| `suscriptores_orange.csv` | 12,000 suscriptores **simulados** de Netflix (un suscriptor por fila) |
| `gasto_marketing_muestra.csv` | Gasto de marketing por canal y mes, **simulado** |
| `peliculas_cola_larga.csv` | **Real:** cuántas calificaciones tiene cada una de 10,506 películas (MovieTweetings, licencia MIT). No son datos de Netflix |
| `canales_resumen.csv`, `ab_resumen.csv` | Resúmenes ya calculados, por si un widget les falla |

**Fórmula del curso:** `CLV = margen × (1 − churn) / (churn + 0.008)`
**Churn mensual** = bajas ÷ meses observados. **CAC** = gasto ÷ altas.

**Columnas de suscriptores que van a usar**
| Columna | Qué significa |
|---|---|
| `se_fue` | 1 si el cliente canceló, 0 si no |
| `meses_observados` | cuántos meses se le observó |
| `activo_12m` | 1 si seguía suscrito a los 12 meses, 0 si no |
| `margen_mensual_usd` | cuánto margen deja por mes |
| `home_experimento` | qué pantalla de inicio vio: personalizada o popular |
| `canal` | por dónde llegó |

### Cómo nombra Orange las columnas de **Group By**
Group By escribe cada resultado como **`columna - Agregación`**. Por ejemplo, si le piden **Sum** a `se_fue`, la columna nueva se llama **`se_fue - Sum`**. Siempre revisen los nombres reales en un **Data Table** después del Group By.

| Concepto del negocio | Cómo lo piden en Group By | Nombre de la columna nueva (se ve en el Data Table) | **Cómo se escribe en Formula** | En los archivos resumen se llama |
|---|---|---|---|---|
| **bajas** (clientes que se fueron) | `se_fue` → **Sum** | `se_fue - Sum` | `se_fue___Sum` | `bajas` |
| **meses observados** | `meses_observados` → **Sum** | `meses_observados - Sum` | `meses_observados___Sum` | `meses_observados` |
| **margen medio** | `margen_mensual_usd` → **Mean** | `margen_mensual_usd - Mean` | `margen_mensual_usd___Mean` | `margen_medio` |
| **altas** (número de clientes) | `subscriber_id` → **Count** | `subscriber_id - Count` | `subscriber_id___Count` | `altas` |
| **retención a 12 meses** | `activo_12m` → **Mean** | `activo_12m - Mean` | `activo_12m___Mean` | `retencion_12m` |
| **gasto total** (en el otro archivo) | `gasto_usd` → **Sum** | `gasto_usd - Sum` | `gasto_usd___Sum` | `gasto_total` |

**Importante:** el widget **Formula** no acepta espacios ni guiones en los nombres. Los cambia por guion bajo: `se_fue - Sum` (tres caracteres: espacio, guion, espacio) se escribe **`se_fue___Sum`** (tres guiones bajos). Si lo escriben con el guion, Orange lo lee como una **resta** y da error o un resultado sin sentido. Lo más seguro es **elegir la columna en el menú desplegable** del widget Formula, que la escribe ya con el nombre correcto.

Ojo: la **retención a 12 meses** (Mean de `activo_12m`) y las **bajas** (Sum de `se_fue`) son cosas distintas. La retención no entra en la fórmula del churn.

### Reglas de los widgets
- **Formula:** cada Formula crea **una** variable. Para varias, **encadenen** un Formula tras otro (primero `churn`, luego `clv`, etc.). Los nombres de Group By se escriben en Formula con guiones bajos (`se_fue - Sum` → `se_fue___Sum`): usen el menú desplegable del widget para que no haya error. Las variables que ustedes creen (`churn`, `clv`, `cac`) se escriben tal cual en el siguiente Formula.
- Si `se_fue` o `activo_12m` aparecen como categóricas y Group By no deja calcular Mean o Sum, pongan un **Edit Domain** después de File y cámbienlas a **numeric**.
- Si un widget les falla, usen el archivo de resumen y sigan. No pierdan más de 3 minutos en un widget.

---

## Parte 1 · ¿La pantalla personalizada retiene más? (≈10 min)
A la mitad de los suscriptores (al azar) se les mostró una pantalla de inicio **personalizada** y a la otra mitad una de títulos **populares**.

1. **File** → `suscriptores_orange.csv`. Abran **Data Table** para mirar: ¿qué significan `se_fue`, `meses_observados` y `activo_12m`?
2. Conecten **Group By** al File. En *Group by* escojan `home_experimento`. En *Aggregations* pidan:
   - `se_fue` → **Sum**  (queda `se_fue - Sum` = bajas)
   - `meses_observados` → **Sum**  (queda `meses_observados - Sum`)
   - `margen_mensual_usd` → **Mean**  (queda `margen_mensual_usd - Mean`)
   - `activo_12m` → **Mean**  (queda `activo_12m - Mean` = retención a 12 meses)
3. Conecten un **Data Table** al Group By. Anoten la retención de cada grupo.
4. Conecten un **Formula** al Group By y creen:
   - `churn = se_fue___Sum / meses_observados___Sum`  (bajas ÷ meses)
5. Conecten otro **Formula** (después del anterior, para que `churn` ya exista) y creen:
   - `clv = margen_mensual_usd___Mean * (1 - churn) / (churn + 0.008)`
6. Anoten retención, churn y CLV de cada grupo, y la diferencia.

*(Atajo: con `ab_resumen.csv` las fórmulas son `churn = bajas / meses_observados` y `clv = margen_medio * (1 - churn) / (churn + 0.008)`.)*

**Preguntas:** ¿cuántos puntos más retiene la personalizada? ¿Cuánto vale esa diferencia por cliente (ΔCLV)? ¿Por qué podemos decir que *causó* la diferencia?

## Parte 2 · ¿Qué canal vale la pena? (≈12 min)
1. En el mismo **File**, conecten un segundo **Group By**. Agrupen por `canal` y pidan:
   - `subscriber_id` → **Count**  (queda `subscriber_id - Count` = altas)
   - `se_fue` → **Sum**  (`se_fue - Sum` = bajas)
   - `meses_observados` → **Sum**  (`meses_observados - Sum`)
   - `margen_mensual_usd` → **Mean**  (`margen_mensual_usd - Mean`)
2. Abran `gasto_marketing_muestra.csv` con otro **File** → **Group By**. Agrupen por `canal` y pidan `gasto_usd` → **Sum**  (`gasto_usd - Sum` = gasto total).
3. **Merge Data**: unan ambas tablas por `canal` (en los dos lados elijan `canal`).
   *(Atajo: `canales_resumen.csv` ya trae todo junto con estos nombres: `altas`, `gasto_total`, `bajas`, `meses_observados`, `margen_medio`.)*
4. Conecten cuatro **Formula** en cadena, una por variable:
   - `cac = gasto_usd___Sum / subscriber_id___Count`  (gasto ÷ altas)
   - `churn = se_fue___Sum / meses_observados___Sum`  (bajas ÷ meses)
   - `clv = margen_mensual_usd___Mean * (1 - churn) / (churn + 0.008)`
   - `clv_cac = clv / cac`
   *(Con el atajo: `cac = gasto_total / altas`, `churn = bajas / meses_observados`, `clv = margen_medio * (1 - churn) / (churn + 0.008)`, `clv_cac = clv / cac`.)*
5. **Bar Plot** de `clv_cac` por canal. La regla común es que un canal sano pasa de 3.

**Preguntas:** ¿qué canal tiene la mejor razón? ¿Cuál es el más caro de adquirir? ¿Hay un canal barato con mucho churn?

## Parte 3 · ¿Qué predice que un suscriptor se quede? (≈12 min)
1. Del **File** (`suscriptores_orange.csv`) conecten un **Select Columns** y verifiquen los roles: el **objetivo** (target) es `se_quedo`; `se_fue`, `meses_observados`, `activo_12m` y `subscriber_id` van como **meta** (fuera de los modelos, porque revelan la respuesta).
2. **Rank** conectado al File: ¿qué variables dicen más sobre quién se queda? Anoten las tres primeras.
3. Conecten el File a **Test and Score** y agreguen cuatro modelos: **Constant** (siempre responde la mayoría), **Logistic Regression**, **Tree** y **Random Forest**.
4. En Test and Score: *Cross validation*, 5 folds, y miren **AUC** y **CA**. Escojan `no` en *Evaluation results for target*.
5. **Experimento de parámetros:** en **Tree**, pónganle "Limit the maximal tree depth" en 4 y luego quítenlo. Comparen AUC y CA.

**Preguntas:** ¿el modelo más complejo le gana a "siempre responde la mayoría" en **CA**? ¿Y en **AUC**? ¿Por qué el árbol sin límite sale peor? ¿Las variables del Rank (títulos vistos, horas) las podemos mover nosotros para que el cliente se quede, o solo son señales?

## Parte 4 · Datos reales: la cola larga (≈5 min)
1. **File** → `peliculas_cola_larga.csv`. Conecten **Distributions** y escojan `n_calificaciones`. ¿Cómo se ve?
2. **Data Table** → ordenen por `n_calificaciones` (clic en el encabezado). ¿Cuáles son las 10 más calificadas?
3. **Select Rows**: `n_calificaciones` *is below* `5`. En la parte de abajo del widget (o en el Data Table conectado) dice "x de 10,506". ¿Qué porcentaje es?
4. Un dato extra: con estos mismos datos, recomendar las 10 películas más populares acertó **14.5%** de las veces, y un recomendador personalizado acertó **15.4%**.

**Pregunta:** si casi todo está concentrado en pocas películas, ¿qué tanto ayuda personalizar?

## Parte 5 · Ahora conecten con la verdad oculta (≈6 min)
Ahora usen `verdad_oculta_resumen.csv`: el porcentaje de clientes de cada canal que **habría llegado igual** sin el marketing (columna `pct_habria_llegado_igual`).
1. **File** → `verdad_oculta_resumen.csv` → **Merge Data** con la tabla final de la Parte 2 (la que ya tiene `cac`, `churn`, `clv`, `clv_cac`), por `canal`.
2. Dos **Formula** en cadena:
   - `cac_real = cac / (1 - pct_habria_llegado_igual)`
   - `clv_cac_real = clv / cac_real`
3. Hagan **dos Bar Plot**: uno con `clv_cac` (el contable) y otro con `clv_cac_real`, ambos agrupados por `canal`. Comparen las dos gráficas.

**Preguntas:**
- ¿Por qué bajó `clv_cac_real` en todos los canales? (Pista: el CLV es el mismo en las dos columnas. ¿Qué número cambió?)
- Miren las barras: ¿qué canal se veía mejor de lo que era? ¿Cuál cambió de lugar respecto a los demás? Fíjense en el **orden** de las barras y no solo en la altura. La barra de referidos es tan alta que tapa los cambios de los demás canales.
- ¿Cómo medirían en la vida real cuántos habrían llegado igual? (Pista: grupo de control.)

---

## Para entregar (anótenlo en el Word, punto 5 (anexo))
Las tablas de las partes 1, 2, 3 y 5, y una conclusión de 5 líneas: **¿en qué palanca pondría Netflix el próximo dólar?** Digan qué números son reales, cuáles son supuestos y cuáles son simulados.
