import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder

# Cargamos el archivo XLSX
archivo_xlsx = 'Catalogo1960_2023.xlsx'
df = pd.read_excel(archivo_xlsx)

# Titulo y las descrip
st.title("Catálogo Sísmico del Perú")
st.write("Este dashboard permite explorar el catálogo sísmico elaborado por el IGP con datos desde 1960.")

# Pestañas general
tab1, tab2, tab3, tab4 = st.tabs(["Vista General", "Distribuciones", "Mapa Interactivo", "Resumen"])

# Pestaña 1
with tab1:
    st.subheader("Vista general de los datos")

    st.write("Tabla interactiva de los sismos:")
    gd = GridOptionsBuilder.from_dataframe(df)
    gd.configure_pagination(paginationAutoPageSize=True)
    gd.configure_side_bar()
    grid_options = gd.build()
    AgGrid(df, gridOptions=grid_options, theme='balham')  # cambiamos el tema, alpine, balham, material


    # Botón de descarga de datos
    @st.cache_data
    def convertir_a_csv(datos):
        return datos.to_csv(index=False).encode('utf-8')
    csv = convertir_a_csv(df)
    st.download_button(
        label="Descargar catálogo completo",
        data=csv,
        file_name='Catalogo_Sismico_Peru.csv',
        mime='text/csv',
    )

# Pestaña 2
with tab2:
    #1
    st.subheader("Distribución de la Magnitud de los Sismos")
    fig_histograma = px.histogram(df, x='MAGNITUD', nbins=50, title="Histograma de Magnitud de Sismos")
    st.plotly_chart(fig_histograma)

    #2
    st.subheader("Magnitud vs. Profundidad de los Sismos")
    fig_dispersion = px.scatter(
        df, x='PROFUNDIDAD', y='MAGNITUD',
        labels={'PROFUNDIDAD': 'Profundidad (km)', 'MAGNITUD': 'Magnitud'},
        title="Relación entre Magnitud y Profundidad",
        color='MAGNITUD',
    )
    st.plotly_chart(fig_dispersion)

# Pestaña 3
with tab3:
    st.subheader("Mapa de Sismos en Perú (Magnitud > 7)")
    m = folium.Map(location=[-9.19, -75.0152], zoom_start=5)
    sismos_mayores_6 = df[df['MAGNITUD'] > 7]
    for _, row in sismos_mayores_6.iterrows():
        folium.CircleMarker(
            location=[row['LATITUD'], row['LONGITUD']],
            radius=5,
            popup=f"Magnitud: {row['MAGNITUD']}<br>Profundidad: {row['PROFUNDIDAD']} km",
            color="red",
            fill=True,
            fill_color="red"
        ).add_to(m)
    st_folium(m, width=700, height=500)

# Pestaña 4
with tab4:
    st.subheader("Resumen Estadístico de los Sismos")
    promedio_magnitud = df['MAGNITUD'].mean()
    std_magnitud = df['MAGNITUD'].std()
    max_magnitud = df['MAGNITUD'].max()
    min_magnitud = df['MAGNITUD'].min()
    promedio_profundidad = df['PROFUNDIDAD'].mean()
    std_profundidad = df['PROFUNDIDAD'].std()
    total_sismos = df.shape[0]

    st.write(f"**Total de sismos registrados**: {total_sismos}")
    st.write(f"**Promedio de Magnitud**: {promedio_magnitud:.2f}")
    st.write(f"**Desviación Estándar de la Magnitud**: {std_magnitud:.2f}")
    st.write(f"**Máxima Magnitud Registrada**: {max_magnitud:.2f}")
    st.write(f"**Mínima Magnitud Registrada**: {min_magnitud:.2f}")
    st.write(f"**Promedio de Profundidad**: {promedio_profundidad:.2f} km")
    st.write(f"**Desviación Estándar de la Profundidad**: {std_profundidad:.2f} km")



#hasta ahora se han usado : plotly, folium, aggrid, streamlit