"""
App de segmentación de clientes · Semana 6
Dos partes:
  1. Visor de grupos: sube un CSV con una columna de grupos (Orange o notebook)
     y muestra el perfil de cada grupo.
  2. Comparador de técnicas: ajusta k-means, jerárquico, DBSCAN, GMM y
     k-prototypes con las mismas variables y las compara.

Ejecutar:  streamlit run app.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from kmodes.kprototypes import KPrototypes
from sklearn.cluster import DBSCAN, AgglomerativeClustering, KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler

AQUI = Path(__file__).parent

# Mismas variables que en Orange y en el notebook
NUMERICAS = ["ingreso_anual", "gasto_total", "compras_tienda", "compras_web",
             "compras_catalogo", "visitas_web_mes", "recencia_dias",
             "hijos_pequenos", "edad"]
CATEGORICAS = ["educacion", "estado_civil"]

st.set_page_config(page_title="Segmentación de clientes", layout="wide")


# ---------------------------------------------------------------------------
# Lectura de datos
# ---------------------------------------------------------------------------
def leer_csv(archivo) -> pd.DataFrame:
    """Lee un CSV de Orange o del notebook y deja nombres de columna limpios.

    Orange puede escribir el tipo en el encabezado ("m#id_cliente", "D#educacion")
    o en dos filas extra debajo del encabezado ("continuous", "discrete"...).
    """
    df = pd.read_csv(archivo)
    # 1) Quitar prefijos de tipo: "mD#respondio_ultima_campana" -> "respondio_ultima_campana"
    df.columns = [str(c).split("#")[-1].strip() for c in df.columns]
    # 2) Quitar las dos filas de tipos del formato de 3 encabezados de Orange
    tipos = {"continuous", "discrete", "string", "time", "c", "d", "s", "meta", "class", ""}
    while len(df) and df.iloc[0].fillna("").astype(str).str.strip().str.lower().isin(tipos).all():
        df = df.iloc[1:].reset_index(drop=True)
    # 3) Convertir a número todo lo que sea numérico
    for c in df.columns:
        convertida = pd.to_numeric(df[c], errors="coerce")
        if convertida.notna().mean() > 0.95:
            df[c] = convertida
    return df


@st.cache_data
def leer_base_local(nombre: str):
    ruta = AQUI / nombre
    return leer_csv(ruta) if ruta.exists() else None


def perfil_por_grupo(df: pd.DataFrame, col_grupo: str, col_valor: str) -> pd.DataFrame:
    """Tabla de perfil: clientes, % de clientes, gasto promedio y % del gasto."""
    g = df.groupby(col_grupo)
    tabla = pd.DataFrame({
        "Clientes": g.size(),
        "% de clientes": g.size() / len(df) * 100,
        "Gasto promedio (US$)": g[col_valor].mean(),
        "% del gasto": g[col_valor].sum() / df[col_valor].sum() * 100,
    })
    if "respondio_ultima_campana" in df.columns or "respondio" in df.columns:
        col_resp = "respondio_ultima_campana" if "respondio_ultima_campana" in df.columns else "respondio"
        tabla["% respondió última campaña"] = g[col_resp].mean() * 100
    return tabla.sort_values("Gasto promedio (US$)", ascending=False)


# ---------------------------------------------------------------------------
# Técnicas de segmentación (con caché para no recalcular en cada clic)
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Ajustando las cinco técnicas…")
def ajustar_tecnicas(df: pd.DataFrame, k: int, eps: float, min_vecinos: int) -> pd.DataFrame:
    """Devuelve una columna de etiquetas por técnica. -1 = ruido (solo DBSCAN)."""
    # Estandarizar: si no, el ingreso (decenas de miles) aplasta a las visitas (unidades)
    Z = StandardScaler().fit_transform(df[NUMERICAS])
    etiquetas = pd.DataFrame(index=df.index)

    etiquetas["k-means"] = KMeans(k, n_init=10, random_state=0).fit_predict(Z)
    etiquetas["Jerárquico (Ward)"] = AgglomerativeClustering(n_clusters=k, linkage="ward").fit_predict(Z)
    etiquetas["DBSCAN"] = DBSCAN(eps=eps, min_samples=min_vecinos).fit_predict(Z)
    etiquetas["Mezcla gaussiana"] = GaussianMixture(k, random_state=0, n_init=5).fit_predict(Z)

    # k-prototypes: números estandarizados + categorías en un solo modelo
    cats = [c for c in CATEGORICAS if c in df.columns]
    if cats:
        X = np.column_stack([Z, df[cats].astype(str).values]).astype(object)
        idx_cat = list(range(len(NUMERICAS), len(NUMERICAS) + len(cats)))
        kp = KPrototypes(n_clusters=k, init="Cao", random_state=0, n_init=3)
        etiquetas["k-prototypes"] = kp.fit_predict(X, categorical=idx_cat)
    return etiquetas


def silueta(Z: np.ndarray, etiquetas: pd.Series):
    """Silueta sobre las variables numéricas estandarizadas, sin contar el ruido."""
    sin_ruido = etiquetas != -1
    if etiquetas[sin_ruido].nunique() < 2:
        return np.nan
    return silhouette_score(Z[sin_ruido.values], etiquetas[sin_ruido])


def nombre_grupo(valor) -> str:
    return "Ruido" if valor == -1 else f"Grupo {int(valor) + 1}"


# ---------------------------------------------------------------------------
# Interfaz
# ---------------------------------------------------------------------------
st.title("Segmentación de clientes")
st.caption("¿A qué grupos de clientes les hablamos distinto, y cuánto vale cada grupo?")

tab_visor, tab_comparador = st.tabs(["Visor de grupos", "Comparador de técnicas"])

# ---------------------------- 1. Visor de grupos ----------------------------
with tab_visor:
    st.subheader("Visor de grupos")
    st.write("Suba el CSV que guardó desde Orange (`clientes_con_cluster.csv`) "
             "o el del notebook (`segmentos_notebook.csv`).")
    archivo = st.file_uploader("CSV con una columna de grupos", type="csv", key="visor")

    if archivo is not None:
        datos = leer_csv(archivo)
    else:
        datos = leer_base_local("segmentos_notebook.csv")
        if datos is not None:
            st.info("Mostrando `segmentos_notebook.csv` de ejemplo. Suba su propio archivo para verlo.")

    if datos is None:
        st.warning("Suba un archivo para empezar.")
    else:
        # Columnas que pueden ser grupos: pocas categorías distintas
        candidatas = [c for c in datos.columns if 1 < datos[c].nunique() <= 15
                      and c not in NUMERICAS]
        if not candidatas:
            st.error("No encontré ninguna columna de grupos (por ejemplo, `Cluster`).")
        else:
            col_grupo = st.selectbox("Columna de grupos", candidatas,
                                     index=candidatas.index("Cluster") if "Cluster" in candidatas else 0)
            numericas = datos.select_dtypes("number").columns.tolist()
            c1, c2, c3 = st.columns(3)
            col_valor = c1.selectbox("Variable de valor", numericas,
                                     index=numericas.index("gasto_total") if "gasto_total" in numericas else 0)
            eje_x = c2.selectbox("Eje X", numericas,
                                 index=numericas.index("ingreso_anual") if "ingreso_anual" in numericas else 0)
            eje_y = c3.selectbox("Eje Y", numericas,
                                 index=numericas.index("gasto_total") if "gasto_total" in numericas else 0)

            datos[col_grupo] = datos[col_grupo].astype(str)
            tabla = perfil_por_grupo(datos, col_grupo, col_valor)

            m1, m2, m3 = st.columns(3)
            m1.metric("Clientes", f"{len(datos):,}")
            m2.metric("Grupos", datos[col_grupo].nunique())
            top = tabla.iloc[0]
            m3.metric(f"Grupo de más valor: {tabla.index[0]}",
                      f"{top['% del gasto']:.0f}% del gasto",
                      f"con {top['% de clientes']:.0f}% de los clientes", delta_color="off")

            izq, der = st.columns([3, 2])
            with izq:
                fig = px.scatter(datos, x=eje_x, y=eje_y, color=col_grupo, opacity=0.6,
                                 category_orders={col_grupo: sorted(datos[col_grupo].unique())},
                                 title=f"Clientes por grupo ({eje_x} vs {eje_y})")
                st.plotly_chart(fig, width="stretch")
            with der:
                barras = tabla[["% de clientes", "% del gasto"]].reset_index().melt(
                    id_vars=col_grupo, var_name="Medida", value_name="%")
                fig2 = px.bar(barras, x=col_grupo, y="%", color="Medida", barmode="group",
                              title="% de clientes vs. % del gasto")
                st.plotly_chart(fig2, width="stretch")

            st.markdown("**Perfil por grupo**")
            st.dataframe(tabla.style.format({
                "Clientes": "{:,.0f}", "% de clientes": "{:.1f}%",
                "Gasto promedio (US$)": "{:,.0f}", "% del gasto": "{:.1f}%",
                "% respondió última campaña": "{:.1f}%"}), width="stretch")

            disponibles = [c for c in NUMERICAS if c in datos.columns]
            if disponibles:
                with st.expander("Promedio de cada variable por grupo"):
                    st.dataframe(datos.groupby(col_grupo)[disponibles].mean().round(1),
                                 width="stretch")

# ------------------------- 2. Comparador de técnicas ------------------------
with tab_comparador:
    st.subheader("Comparador de técnicas")
    st.write("Ajusta las cinco técnicas con las mismas variables estandarizadas: "
             + ", ".join(f"`{v}`" for v in NUMERICAS)
             + ". k-prototypes además usa `educacion` y `estado_civil`.")

    archivo_base = st.file_uploader("Base de clientes (opcional, por defecto `clientes_retail.csv`)",
                                    type="csv", key="base")
    base = leer_csv(archivo_base) if archivo_base is not None else leer_base_local("clientes_retail.csv")

    if base is None:
        st.warning("Suba `clientes_retail.csv` para comparar técnicas.")
    elif not set(NUMERICAS).issubset(base.columns):
        st.error("Al archivo le faltan columnas: " + ", ".join(set(NUMERICAS) - set(base.columns)))
    else:
        base = base.dropna(subset=NUMERICAS).reset_index(drop=True)
        p1, p2, p3 = st.columns(3)
        k = p1.slider("Número de grupos (k)", 2, 6, 3,
                      help="Para k-means, jerárquico, mezcla gaussiana y k-prototypes")
        eps = p2.slider("DBSCAN · eps", 0.5, 3.0, 1.5, 0.1,
                        help="Radio del vecindario. Más grande = menos grupos y menos ruido")
        min_vecinos = p3.slider("DBSCAN · mínimo de vecinos", 3, 20, 5)

        etiquetas = ajustar_tecnicas(base, k, eps, min_vecinos)
        Z = StandardScaler().fit_transform(base[NUMERICAS])
        tecnicas = etiquetas.columns.tolist()

        # Resumen: grupos, tamaños, ruido y silueta
        filas = []
        for t in tecnicas:
            e = etiquetas[t]
            tam = e[e != -1].value_counts().sort_values(ascending=False)
            filas.append({
                "Técnica": t,
                "Nº de grupos": int(tam.size),
                "Tamaños": " / ".join(f"{n:,}" for n in tam.values),
                "Ruido": int((e == -1).sum()),
                "Silueta": silueta(Z, e),
            })
        resumen = pd.DataFrame(filas).set_index("Técnica")
        st.markdown("**Resumen por técnica**")
        st.dataframe(resumen.style.format({"Silueta": "{:.3f}"}, na_rep="n/a"),
                     width="stretch")
        st.caption("Silueta calculada con las variables numéricas estandarizadas y sin el ruido. "
                   "Va de −1 a 1: más alto = grupos más separados.")

        # Coincidencia entre técnicas (índice de Rand ajustado)
        ari = pd.DataFrame(
            [[adjusted_rand_score(etiquetas[a], etiquetas[b]) for b in tecnicas] for a in tecnicas],
            index=tecnicas, columns=tecnicas)
        izq, der = st.columns(2)
        with izq:
            fig = px.imshow(ari.round(2), text_auto=True, zmin=0, zmax=1,
                            color_continuous_scale="Blues",
                            title="¿Qué tanto coinciden? (1 = grupos idénticos)")
            st.plotly_chart(fig, width="stretch")
        with der:
            elegida = st.selectbox("Ver grupos de", tecnicas)
            vista = base.assign(Grupo=etiquetas[elegida].map(nombre_grupo))
            fig = px.scatter(vista, x="ingreso_anual", y="gasto_total", color="Grupo", opacity=0.6,
                             category_orders={"Grupo": sorted(vista["Grupo"].unique())},
                             title=f"{elegida}: ingreso vs. gasto")
            st.plotly_chart(fig, width="stretch")

        st.markdown(f"**Valor por grupo · {elegida}**")
        st.dataframe(perfil_por_grupo(vista, "Grupo", "gasto_total").style.format({
            "Clientes": "{:,.0f}", "% de clientes": "{:.1f}%",
            "Gasto promedio (US$)": "{:,.0f}", "% del gasto": "{:.1f}%",
            "% respondió última campaña": "{:.1f}%"}), width="stretch")

        with st.expander("Recomendación"):
            st.markdown(
                "- **Técnica:** k-means con k = 3 sobre variables de comportamiento estandarizadas.\n"
                "- **Por qué:** es la más fácil de explicar y recalcular, es estable, y k-prototypes "
                "llega prácticamente a los mismos grupos; DBSCAN no separa a estos clientes porque "
                "forman una nube continua.\n"
                "- **Acción:** retener al segmento premium (≈25% de los clientes y ≈59% del gasto) "
                "con un programa de lealtad, y crecer al segmento medio con venta cruzada por web.")
