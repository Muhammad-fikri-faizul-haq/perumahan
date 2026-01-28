import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster

# 1. KONFIGURASI HALAMAN
st.set_page_config(
    page_title="Dashboard Persebaran Perumahan",
    page_icon="🏠",
    layout="wide"
)

# 2. FUNGSI LOAD DATA
@st.cache_data
def load_data():
    try:
        # Membaca file yang dihasilkan oleh script scraping Anda
        df = pd.read_csv("data_perumahan_v2.csv")
        return df
    except FileNotFoundError:
        return None

# Load Data
df = load_data()

# 3. SIDEBAR (FILTER)
st.sidebar.title("🔍 Filter Data")

if df is not None:
    # A. FILTER KOTA
    st.sidebar.subheader("📍 Lokasi")
    
    # Ambil daftar unik kota & urutkan
    all_cities = sorted(df['pulau_kota'].unique().tolist())

    # FUNGSI CALLBACK UNTUK KOTA 
    def update_city_selection(status):
        """Fungsi ini dipanggil saat tombol ditekan"""
        for city in all_cities:
            # Update langsung key session state milik checkbox
            st.session_state[f"city_{city}"] = status

    with st.sidebar.expander("Pilih Kota", expanded=True):
        col_a, col_b = st.columns(2)
        
        # Memanggil fungsi update
        col_a.button("Select All", key="all_city_btn", on_click=update_city_selection, args=(True,))
        col_b.button("Clear All", key="none_city_btn", on_click=update_city_selection, args=(False,))
        
        selected_cities = []
        
        for city in all_cities:
            # Inisialisasi default state jika belum ada
            key_name = f"city_{city}"
            if key_name not in st.session_state:
                st.session_state[key_name] = True # Default True (Tercentang)

            # Checkbox langsung terhubung ke session_state via key
            is_checked = st.checkbox(city, key=key_name)
            
            if is_checked:
                selected_cities.append(city)

    # FILTER KATEGORI
    st.sidebar.subheader("🏷️ Kategori")
    all_categories = sorted(df['kategori'].unique().tolist())
    
    # FUNGSI CALLBACK UNTUK KATEGORI
    def update_cat_selection(status):
        for cat in all_categories:
            st.session_state[f"cat_{cat}"] = status

    with st.sidebar.expander("Pilih Jenis Perumahan", expanded=True):
        col_c, col_d = st.columns(2)
        col_c.button("Select All", key="all_cat_btn", on_click=update_cat_selection, args=(True,))
        col_d.button("Clear All", key="none_cat_btn", on_click=update_cat_selection, args=(False,))

        selected_categories = []

        for cat in all_categories:
            key_name = f"cat_{cat}"
            if key_name not in st.session_state:
                st.session_state[key_name] = True

            is_checked = st.checkbox(cat, key=key_name)
            
            if is_checked:
                selected_categories.append(cat)

    # TERAPKAN FILTER 
    if not selected_cities or not selected_categories:
        st.warning("⚠️ Mohon pilih setidaknya satu Kota dan Kategori.")
        filtered_df = pd.DataFrame(columns=df.columns)
    else:
        filtered_df = df[
            (df['pulau_kota'].isin(selected_cities)) & 
            (df['kategori'].isin(selected_categories))
        ]

    # RINGKASAN FILTER
    st.sidebar.divider()
    st.sidebar.caption("Filter Aktif:")
    
    if len(selected_cities) == len(all_cities):
        st.sidebar.info("Semua Kota Dipilih")
    elif len(selected_cities) == 0:
        st.sidebar.error("Tidak ada kota dipilih")
    else:
        st.sidebar.write(f"🏙️ **{len(selected_cities)} Kota:**")
        # Menampilkan max 5 kota agar sidebar tidak kepanjangan
        tampil_kota = selected_cities[:5]
        for c in tampil_kota:
            st.sidebar.markdown(f"- {c}")
        if len(selected_cities) > 5:
            st.sidebar.markdown(f"*(...dan {len(selected_cities)-5} lainnya)*")

else:
    st.error("⚠️ File 'data_perumahan_v2.csv' tidak ditemukan!")
    st.stop()

# 4. MAIN DASHBOARD
st.title("🏠 Housing Market Tracker")
st.markdown("data perumahan subsidi & elite.")

#
col1, col2, col3 = st.columns(3)
col1.metric("Total Data Perumahan", f"{len(filtered_df)} Unit")
col2.metric("Jumlah Kota Terpantau", f"{filtered_df['pulau_kota'].nunique()} Kota")
col3.metric("Kategori Terbanyak", filtered_df['kategori'].mode()[0] if not filtered_df.empty else "-")

st.divider()

# Tab untuk mengorganisir tampilan
tab1, tab2, tab3 = st.tabs(["📊 Visualisasi Grafik", "🗺️ Peta GIS", "📄 Data Tabel"])

# VISUALISASI MATPLOTLIB 
with tab1:
    st.subheader("Analisis Statistik")
    
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.write("**Distribusi Perumahan per Kota**")
        if not filtered_df.empty:
            fig, ax = plt.subplots(figsize=(8, 5))
            # Menggunakan Seaborn untuk styling yang lebih bagus
            sns.countplot(data=filtered_df, x='pulau_kota', hue='kategori', palette='viridis', ax=ax)
            ax.set_title("Jumlah Perumahan berdasarkan Kota & Kategori")
            ax.set_xlabel("Kota")
            ax.set_ylabel("Jumlah Data")
            plt.xticks(rotation=45)
            st.pyplot(fig)
        else:
            st.info("Data kosong setelah filter.")

    with col_chart2:
        st.write("**Perbandingan Persentase Kategori Perumahan**")
        if not filtered_df.empty:
            fig2, ax2 = plt.subplots(figsize=(6, 6))
            count_data = filtered_df['kategori'].value_counts()
            ax2.pie(count_data, labels=count_data.index, autopct='%1.1f%%', startangle=90, colors=['#66b3ff','#ff9999'])
            ax2.set_title("Persentase Subsidi dan Elite")
            st.pyplot(fig2)

# PETA GIS
with tab2:
    st.subheader("Peta Persebaran Lokasi")
    
    if not filtered_df.empty:
        # Tentukan titik tengah peta berdasarkan rata-rata koordinat data yang difilter
        center_lat = filtered_df['latitude'].mean()
        center_lon = filtered_df['longitude'].mean()
        
        m = folium.Map(location=[center_lat, center_lon], zoom_start=9, tiles="CartoDB positron")
        marker_cluster = MarkerCluster().add_to(m)

        for _, row in filtered_df.iterrows():
            color = 'green' if row['kategori'] == 'Subsidi' else 'red'
            
            popup_html = f"""
            <div style="font-family: Arial; width: 200px;">
                <b>{row['nama_perumahan']}</b><br>
                <span style="color: gray;">{row['pulau_kota']}</span><br>
                <span style="background-color: {color}; color: white; padding: 2px 5px; border-radius: 3px;">
                    {row['kategori']}
                </span><br>
                <a href="{row['link_gmaps']}" target="_blank">Buka di Google Maps</a>
            </div>
            """
            
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=6,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                popup=folium.Popup(popup_html, max_width=250)
            ).add_to(marker_cluster)

        # Render peta di Streamlit
        st_folium(m, width="100%", height=500)
    else:
        st.warning("Tidak ada data koordinat untuk ditampilkan.")

# TABEL DATA
with tab3:
    st.subheader("Data Perumahan Subsidi dan Elite")
    st.dataframe(
        filtered_df,
        use_container_width=True,
        column_config={
            "link_gmaps": st.column_config.LinkColumn("Link Gmaps")
        }
    )
    
    # Tombol Download CSV
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Data Terfilter (CSV)",
        data=csv,
        file_name='data_perumahan_filtered.csv',
        mime='text/csv',
    )