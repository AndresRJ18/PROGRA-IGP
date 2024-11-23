import streamlit as st
import pandas as pd
import plotly.express as px
import geopandas as gpd
import folium
from shapely.geometry import Point, Polygon
from streamlit_folium import st_folium
from st_aggrid import AgGrid
from streamlit_option_menu import option_menu
from st_aggrid.grid_options_builder import GridOptionsBuilder
# Cargar el archivo Excel
file_path = "Catalogo1960_2023.xlsx"
data = pd.read_excel(file_path)

data['FECHA_UTC'] = pd.to_datetime(data['FECHA_UTC'], format='%Y%m%d', errors='coerce')

data['AÑO'] = data['FECHA_UTC'].dt.year

# Crear un GeoDataFrame desde el DataFrame usando latitud y longitud
geometry = gpd.points_from_xy(data['LONGITUD'], data['LATITUD'])
geo_df = gpd.GeoDataFrame(data, geometry=geometry)

# Cargar el shapefile de los departamentos
shapefile_path = "DEPARTAMENTOS.shp"
departments = gpd.read_file(shapefile_path)

# Asegurar que ambos GeoDataFrames tengan el mismo sistema de coordenadas (CRS)
geo_df = geo_df.set_crs(departments.crs)

# Realizar un spatial join para asignar departamentos a las coordenadas
result = gpd.sjoin(geo_df, departments, how="left", predicate="within")

# Usar la columna correcta que contiene los nombres de los departamentos
data['DEPARTAMENTO'] = result['NOMBDEP']

data['DEPARTAMENTO'] = result['NOMBDEP'].fillna("DESCONOCIDO")

# Configurar el diseño del sidebar con colores personalizados y submenús
with st.sidebar:
    selected = option_menu(
        "Menú Principal",  # Título del menú
        ["Inicio", "Vista General", "Gráficas", "Mapa Interactivo"],  # Opciones principales
        icons=["house", "table", "bar-chart", "geo-alt"],  # Íconos
        menu_icon="cast",  # Ícono del menú
        default_index=0,  # Selección inicial
        styles={
            "container": {"padding": "5px", "background-color": "#1a1a1a"},  # Fondo oscuro
            "nav-link": {
                "font-size": "16px",
                "text-align": "left",
                "margin": "5px",
                "color": "#cfcfcf",  # Color de texto claro
                "border-radius": "5px",
            },
            "nav-link-selected": {
                "background-color": "#007bff",  # Azul para el seleccionado
                "color": "white",
            },
        },
    )

    # Submenú para "Gráficas" si está seleccionada
    if selected == "Gráficas":
        sub_selected = option_menu(
            "Gráficas",  # Título del submenú
            ["Gráfica Interactiva", "Gráfico de Datos"],  # Opciones del submenú
            icons=["bar-chart", "graph-up"],  # Íconos
            menu_icon="bar-chart",  # Ícono del submenú
            default_index=0,  # Selección inicial
            styles={
                "container": {"padding": "5px"},
                "nav-link": {
                    "font-size": "14px",
                    "color": "#cfcfcf",
                    "margin": "2px",
                },
                "nav-link-selected": {
                    "background-color": "#0056b3",
                    "color": "white",
                },
            },
        )
    else:
        sub_selected = None

# Lógica para cada sección
if selected == "Inicio":
    st.title("Inicio")
    st.write("Bienvenido a la aplicación interactiva.")
elif selected == "Vista General":
    st.title("Vista General")
    st.write("Tabla extraída del archivo Excel:")
    gd = GridOptionsBuilder.from_dataframe(data)
    gd.configure_pagination(paginationAutoPageSize=True)
    gd.configure_side_bar()
    grid_options = gd.build()
    AgGrid(data, gridOptions=grid_options, theme='balham')


    # Botón de descarga
    @st.cache_data
    def convertir_a_csv(datos):
        return datos.to_csv(index=False).encode('utf-8')


    csv = convertir_a_csv(data)
    st.download_button(
        label="Descargar catálogo completo",
        data=csv,
        file_name='Catalogo_Sismico_Peru.csv',
        mime='text/csv',
    )

elif selected == "Gráficas":
    if sub_selected == "Gráfica Interactiva":
        st.title("Gráfica Interactiva")

        # Interactividad: selección de año y departamento
        años_disponibles = sorted(data['AÑO'].dropna().unique(), reverse=True)  # Orden descendente
        año_seleccionado = st.selectbox("Selecciona el año:", años_disponibles)

        # Obtener los departamentos disponibles y ordenarlos
        departamentos_disponibles = sorted(
            [depto for depto in data['DEPARTAMENTO'].unique() if depto != "DESCONOCIDO"]
        )
        # Agregar "Desconocido" al final
        departamentos_disponibles.append("DESCONOCIDO")

        # Mostrar el selector con los departamentos ordenados
        depto_seleccionado = st.selectbox("Selecciona el departamento:", departamentos_disponibles)

        # Filtrar datos según selección
        datos_filtrados = data[(data['AÑO'] == año_seleccionado) &
                               (data['DEPARTAMENTO'] == depto_seleccionado)]

        # Comprobar si hay datos filtrados
        if not datos_filtrados.empty:
            # Clasificar magnitudes en rangos
            bins = [0, 3, 4, 5, 6, 7, 10]
            labels = ["<3", "3-4", "4-5", "5-6", "6-7", ">7"]
            datos_filtrados['RANGO_MAGNITUD'] = pd.cut(datos_filtrados['MAGNITUD'], bins=bins, labels=labels)

            # Gráfico de barras apiladas para Rango de Magnitud
            magnitud_counts = datos_filtrados['RANGO_MAGNITUD'].value_counts().sort_index()
            fig_magnitud = px.bar(
                x=magnitud_counts.index,
                y=magnitud_counts.values,
                title=f"MAGNITUD ({depto_seleccionado}, {año_seleccionado})",
                labels={"x": "Rango de Magnitud", "y": "Número de Sismos"},
                color=magnitud_counts.index,
            )
            st.plotly_chart(fig_magnitud)

            # Histograma para distribución de Profundidad
            fig_profundidad = px.box(
                datos_filtrados,
                y="PROFUNDIDAD",
                title=f"PROFUNDIDAD ({depto_seleccionado}, {año_seleccionado})",
                labels={"PROFUNDIDAD": "Profundidad (km)"},
                points="all"  # Mostrar valores atípicos
            )
            fig_profundidad.update_traces(
                marker_color="green",  # Color de los puntos (valores atípicos)
                boxmean=True,  # Mostrar media en el gráfico (opcional)
                line_color="green",  # Color de los bordes de la caja y los bigotes
                fillcolor="lightgreen" )


            st.plotly_chart(fig_profundidad)
            st.write(
                """
                **Gráfico de Cajas y Bigotes: Profundidad de los Sismos**

                Este gráfico muestra cómo varían las profundidades de los sismos:
                - **Caja**: Rango típico donde ocurren la mayoría de los sismos.
                - **Línea dentro de la caja**: Profundidad mediana.
                - **Puntos fuera de los bigotes**: Sismos inusualmente profundos o poco profundos.
                """
            )
        else:
            st.write("No hay datos para la selección realizada.")

    elif sub_selected == "Gráfico de Datos":
        st.title("Gráfico de Datos")
        st.write("Sección en desarrollo.")
elif selected == "Mapa Interactivo":
    st.title("Mapa Interactivo")
    st.write("Sección en desarrollo.")
