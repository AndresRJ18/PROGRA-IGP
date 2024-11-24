import streamlit as st
import pandas as pd
import plotly.express as px
import geopandas as gpd
import folium
from streamlit_folium import st_folium
from st_aggrid import AgGrid
from streamlit_option_menu import option_menu
from st_aggrid.grid_options_builder import GridOptionsBuilder

#descargar el archivo
file_path = "Catalogo1960_2023.xlsx"
data = pd.read_excel(file_path)
shapefile_path = "DEPARTAMENTOS.shp"
departments = gpd.read_file(shapefile_path)

if not departments.crs:
    departments = departments.set_crs("EPSG:4326")
else:
    # Transformar al CRS requerido por Folium
    departments = departments.to_crs("EPSG:4326")
    
#Para trabajar los años
data['FECHA_UTC'] = pd.to_datetime(data['FECHA_UTC'], format='%Y%m%d', errors='coerce')
data['AÑO'] = data['FECHA_UTC'].dt.year

geometry = gpd.points_from_xy(data['LONGITUD'], data['LATITUD'])
geo_df = gpd.GeoDataFrame(data, geometry=geometry)
geo_df = geo_df.set_crs("EPSG:4326")

geo_df = geo_df.set_crs(departments.crs)
result = gpd.sjoin(geo_df, departments, how="left", predicate="within")
#print(result.columns)
data['DEPARTAMENTO'] = result['DEPARTAMEN'].str.strip().str.upper()

data['DEPARTAMENTO'] = result['DEPARTAMEN'].fillna("DESCONOCIDO")

#print(result[['IDDPTO', 'DEPARTAMEN']].head())

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
                "background-color": "#007bff",  # Azul
                "color": "white",
            },
        },
    )

    # Submenú de Graficas (interactiva y datos)
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

    if selected == "Mapa Interactivo":
        map_selected = option_menu(
            "Mapas Interactivos",
            ["Mapa por Rangos de Magnitud", "Mapa por Departamento"],
            icons=["map", "pin-map"],
            menu_icon="geo-alt",
            default_index=0,
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
        map_selected = None
#La seleccion para los submenus
if selected == "Inicio":

    st.title("Análisis de Sismos en el Perú (1960-2023)")

    # Breve descripción del proyecto
    st.markdown("""
    ### Bienvenidos 👋
    Este proyecto presenta un análisis interactivo de los sismos ocurridos en el Perú entre 1960 y 2023, utilizando herramientas de visualización avanzadas como gráficos dinámicos y mapas interactivos. 
    El objetivo principal es facilitar la exploración de datos sísmicos para comprender patrones, tendencias y regiones más afectadas.

    #### ¿Qué encontrarás en este dashboard?
    - **Vista General:** Un resumen con los datos principales organizados en una tabla.
    - **Gráficas:** Visualizaciones interactivas para analizar sismos por departamento, rango de magnitud y más.
    - **Mapa Interactivo:** Localización geográfica de los sismos en el territorio peruano.

    ---
    """)

    # Sección de integrantes
    st.subheader("Integrantes del Equipo")
    st.markdown("""
    - **Andres Rodas**
    - **Jhan Mocaico**
    - **Juan Aquino**
    - **Dario Huerta**
    - **Anthony Zuñiga**
    """)

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

        # selección de año y departamento
        años_disponibles = sorted(data['AÑO'].dropna().unique(), reverse=True)  # Orden descendente
        año_seleccionado = st.selectbox("Selecciona el año:", años_disponibles)

        # Obtener los departamentos disponibles y ordenarlos
        departamentos_disponibles = sorted(
            [depto for depto in data['DEPARTAMENTO'].unique() if depto != "DESCONOCIDO"])
        departamentos_disponibles.append("DESCONOCIDO")
        depto_seleccionado = st.selectbox("Selecciona el departamento:", departamentos_disponibles) #el box para seleccionar

        datos_filtrados = data[(data['AÑO'] == año_seleccionado) &
                               (data['DEPARTAMENTO'] == depto_seleccionado)]

        # Comprobar si hay datos filtrados
        if not datos_filtrados.empty:
            total_sismos = len(datos_filtrados)
            sismo_mas_fuerte = datos_filtrados.loc[datos_filtrados['MAGNITUD'].idxmax()]

            st.write(
                f"### Resumen de Sismos en {depto_seleccionado} durante {año_seleccionado}:")
            st.metric(label="Número Total de Sismos", value=total_sismos)
            st.metric(
                label="Sismo Más Fuerte",
                value=f"{sismo_mas_fuerte['MAGNITUD']} Mw",
                help=(
                    f"Fecha: {sismo_mas_fuerte['FECHA_UTC']}\n"
                    f"Profundidad: {sismo_mas_fuerte['PROFUNDIDAD']} km"
                )
            )
            # Explicación sobre Mw
            st.caption("**Mw**: Magnitud Momento, una medida de la energía liberada por el sismo.")

            # Gráfico de barras apiladas para Rango de Magnitud
            bins = [0, 3, 4, 5, 6, 7, 10] #rangos
            labels = ["<3", "3-4", "4-5", "5-6", "6-7", ">7"]
            datos_filtrados['RANGO_MAGNITUD'] = pd.cut(datos_filtrados['MAGNITUD'], bins=bins, labels=labels)

            magnitud_counts = datos_filtrados['RANGO_MAGNITUD'].value_counts().sort_index()
            fig_magnitud = px.bar(
                x=magnitud_counts.index,
                y=magnitud_counts.values,
                title=f"MAGNITUD DE LOS SISMOS ",
                labels={"x": "Rango de Magnitud", "y": "Número de Sismos"},
                color=magnitud_counts.index,
            )
            st.plotly_chart(fig_magnitud)
            st.write(
                f"""
                        El gráfico de barras apiladas muestra la cantidad de sismos registrados en el departamento 
                        **{depto_seleccionado}** durante el año **{año_seleccionado}**, clasificados según rangos de magnitud. 
                        Esto permite identificar si predominan sismos de menor magnitud o si hay un número significativo 
                        de eventos más intensos.
                        """
            )
            # Histograma para distribución de Profundidad
            fig_profundidad = px.box(
                datos_filtrados,
                y="PROFUNDIDAD",
                title=f"PROFUNDIDAD DE LOS SISMOS",
                labels={"PROFUNDIDAD": "Profundidad (km)"},
                points="all"  # Mostrar valores atípicos
            )
            fig_profundidad.update_traces(
                marker_color="green",  # Color de los puntos (valores atípicos)
                boxmean=True,  # Mostrar media en el gráfico (opcional)
                line_color="green",  # Color de los bordes de la caja y los bigotes
                fillcolor="lightgreen" )

            st.plotly_chart(fig_profundidad) #grafo
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
        st.subheader("Tendencia Anual de Sismos")

        sismos_por_año = data.groupby('AÑO').size()
        fig_tendencia = px.line(
            x=sismos_por_año.index,
            y=sismos_por_año.values,
            title="A) Número de Sismos por Año",
            labels={"x": "Año", "y": "Número de Sismos"},
        )
        st.plotly_chart(fig_tendencia) #grafo
        st.write(
            """
            - Este gráfico muestra cómo ha variado la cantidad de sismos registrados en cada año.
            - Es útil para identificar tendencias temporales, como períodos de mayor o menor actividad sísmica,
            y permite analizar la evolución de los eventos sísmicos a lo largo del tiempo.
            """
        )
        #  gráfico de barras apiladas
        bins = [0, 3, 4, 5, 6, 7, 10] #rangos
        labels = ["<3", "3-4", "4-5", "5-6", "6-7", ">7"]
        data['RANGO_MAGNITUD'] = pd.cut(data['MAGNITUD'], bins=bins, labels=labels)

        sismos_departamento = data.groupby(['DEPARTAMENTO', 'RANGO_MAGNITUD']).size().reset_index(name='CUENTA')

        fig_barras_apiladas = px.bar(
            sismos_departamento,
            x='DEPARTAMENTO',
            y='CUENTA',
            color='RANGO_MAGNITUD',
            title="B) Sismos Acumulados por Departamento y Rango de Magnitud",
            labels={"DEPARTAMENTO": "Departamento", "CUENTA": "Número de Sismos",
                    "RANGO_MAGNITUD": "Rango de Magnitud"},
            text_auto=True,  # Mostrar los valores directamente en las barras
        )

        # Ajustar diseño del gráfico
        fig_barras_apiladas.update_layout(
            xaxis=dict(title="Departamento", tickangle=45),  # Inclinación de etiquetas para mejor legibilidad
            yaxis=dict(
                title="Número de Sismos",
                tickformat=",",  # Formato para miles
            ),
            legend_title="Rango de Magnitud",
            barmode="stack",  # Barras apiladas
            margin=dict(t=50, b=150)  # Margen para evitar cortes en las etiquetas
        )
        st.plotly_chart(fig_barras_apiladas)
        st.write(
            """
            - Este gráfico representa el número total de sismos en cada departamento, desglosado por rangos de magnitud.
            - Los departamentos con mayor actividad sísmica son fácilmente identificables, y el desglose por magnitud permite
            entender la proporción de sismos de diferentes intensidades en cada región.
            """
        )
if selected == "Mapa Interactivo":
    if map_selected == "Mapa por Rangos de Magnitud":
        st.title("Mapa Interactivo: Rangos de Magnitud")

        col1, col2 = st.columns([1, 2])  # Dividir en dos columnas
        with col1:
            st.header("Filtros")
            magnitud_min, magnitud_max = st.slider(
                "Selecciona el rango de magnitud:",
                min_value=float(data['MAGNITUD'].min()),
                max_value=float(data['MAGNITUD'].max()),
                value=(6.0, 7.0),  # Valores iniciales
                step=0.1,
            )

            datos_filtrados = data[(data['MAGNITUD'] >= magnitud_min) & (data['MAGNITUD'] <= magnitud_max)]

        with col2:
            st.header("Mapa de Sismos")
            # Crear mapa
            mapa_rangos = folium.Map(location=[-9.19, -75.0152], zoom_start=6)  # Centrado en Perú
            for _, row in datos_filtrados.iterrows():
                folium.CircleMarker(
                    location=[row['LATITUD'], row['LONGITUD']],
                    radius=5,
                    color='red',
                    fill=True,
                    fill_color='red',
                    popup=f"Magnitud: {row['MAGNITUD']}<br>Fecha: {row['FECHA_UTC']}",
                ).add_to(mapa_rangos)
            st_folium(mapa_rangos, width=700, height=500)

    elif map_selected == "Mapa por Departamento":
        st.title("Mapa por Departamento")
        # Dividir en dos columnas
        col1, col2 = st.columns([2, 1])  # Ajusta las proporciones de las columnas (2:1)
        with col1:

            mapa_departamento = folium.Map(location=[-9.19, -75.0152], zoom_start=6)
            # Función para procesar la selección de departamentos
            def estilo_departamento(feature):
                return {"fillColor": "blue", "color": "black", "weight": 1, "fillOpacity": 0.5}
            # Añadir interactividad al mapa
            folium.GeoJson(
                departments,
                name="Departamentos",
                tooltip=folium.GeoJsonTooltip(fields=["DEPARTAMEN"], aliases=["Departamento"]),
                style_function=estilo_departamento,
            ).add_to(mapa_departamento)

            # Mostrar el mapa en Streamlit
            output = st_folium(mapa_departamento, width=700, height=500)
        with col2:
            st.subheader("Características del Departamento")
            # Procesar clic en un departamento
            if output and output.get("last_active_drawing"):
                # Obtener el nombre del departamento seleccionado
                departamento_seleccionado = output["last_active_drawing"]["properties"]["DEPARTAMEN"]
                st.write(f"**Departamento Seleccionado:** {departamento_seleccionado}")
                # Filtrar los datos del departamento
                datos_departamento = data[data["DEPARTAMENTO"] == departamento_seleccionado]

                if not datos_departamento.empty:
                    # Calcular características
                    total_sismos = int(len(datos_departamento))  # Convertir a entero
                    promedio_magnitud = round(datos_departamento["MAGNITUD"].mean(), 2)  # Redondear a 2 decimales
                    sismo_mas_fuerte = datos_departamento.loc[datos_departamento["MAGNITUD"].idxmax()]
                    magnitud_fuerte = round(sismo_mas_fuerte["MAGNITUD"], 1)  # Redondear a 1 decimal
                    año_fuerte = int(sismo_mas_fuerte["AÑO"])  # Convertir a entero

                    # Crear un DataFrame con los valores calculados
                    tabla = pd.DataFrame({
                        "Características": [
                            "Total de Sismos",
                            "Promedio de Magnitud",
                            "Sismo Más Fuerte",
                            "Año del Sismo Más Fuerte",
                        ],
                        "Valores": [
                            int(total_sismos),
                            promedio_magnitud,
                            magnitud_fuerte,
                            int(año_fuerte),
                        ],
                    })

                    tabla["Valores"] = tabla["Valores"].apply(
                        lambda x: f"{x:.2f}" if isinstance(x, float) else f"{x}"
                        # Solo redondear los flotantes a 2 decimales
                    )

                    # Mostrar la tabla
                    st.table(tabla)
                else:
                    st.write("No hay datos disponibles para este departamento.")
            else:
                st.write("Selecciona un departamento en el mapa para ver sus características.")
