import streamlit as st
import os
from cv_parser import parse_cv
from data_extractor import extract_structured_data
from comparison_engine import compare_cv_data, generate_report
from typing import Dict, Any, List

# --- Çözüm Kodu: data klasörünü otomatik oluştur ---
if not os.path.exists("data"):
    os.makedirs("data")
# ---------------------------------------------------

# --- Konfigürasyon ---
st.set_page_config(layout="wide", page_title="Akıllı CV Karşılaştırma Sistemi")

# --- Yardımcı Fonksiyon ---
def run_full_analysis(cv_file, name: str) -> Dict[str, Any]:
    """Yüklenen dosyayı işler ve yapılandırılmış veriyi döndürür."""
    # Yüklenen dosyayı geçici olarak kaydet
    temp_path = os.path.join("data", f"{name}_{cv_file.name}")
    with open(temp_path, "wb") as f:
        f.write(cv_file.getbuffer())

    # Parsing ve Çıkarım
    sections = parse_cv(temp_path)
    if not sections:
        st.error(f"{name} dosyası okunamadı veya bölüm çıkarılamadı. PDF formatını kontrol edin.")
        return None
    
    structured_data = extract_structured_data(sections)
    return structured_data

# --- Ana Streamlit Uygulaması ---

st.title("👨‍💻 CV Karşılaştırma ve Değerlendirme Sistemi")
st.subheader("İki adayın teknik yeterliliklerini analiz edin.")

# 1. Dosya Yükleme Alanı
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Aday A (Hedef CV)")
    uploaded_file_a = st.file_uploader("CV A Dosyasını Yükleyin (PDF)", type=["pdf"])

with col2:
    st.markdown("#### Aday B (Karşılaştırılacak CV)")
    uploaded_file_b = st.file_uploader("CV B Dosyasını Yükleyin (PDF)", type=["pdf"])

# 2. Analizi Başlatma
if uploaded_file_a and uploaded_file_b:
    st.success("İki dosya da yüklendi. Analiz için Başlat'a tıklayın.")
    
    if st.button("🚀 Karşılaştırmayı Başlat", type="primary"):
        st.spinner("CV'ler parse ediliyor ve NLP ile analiz ediliyor...")
        
        # Analizleri Çalıştır
        data_a = run_full_analysis(uploaded_file_a, "A")
        data_b = run_full_analysis(uploaded_file_b, "B")
        
        if data_a and data_b:
            # 3. Puanlama
            total_score, section_scores = compare_cv_data(data_a, data_b)
            
            # 4. Raporlama
            report_lines: List[str] = generate_report(data_a, data_b, total_score, section_scores)

            st.balloons()
            
            # Sonuçları Gösterme
            st.header("✅ Analiz Tamamlandı")

            # Genel Puan
            st.metric(label="GENEL BENZERLİK SKORU", value=f"% {total_score * 100:.1f}")

            st.markdown("---")
            
            # Rapor ve Skor Detayları
            col_report, col_scores = st.columns(2)
            
            with col_report:
                st.subheader("İK Uzmanı Rapor Özeti")
                for line in report_lines:
                    st.write(line)

            with col_scores:
                st.subheader("Alan Bazlı Benzerlik Skorları")
                scores_df = {'Alan': [], 'Benzerlik Skoru': []}
                for section, score in section_scores.items():
                    scores_df['Alan'].append(section)
                    scores_df['Benzerlik Skoru'].append(f"% {score * 100:.1f}")
                
                st.table(scores_df)

            st.markdown("---")
            
            # Yapılandırılmış Veri Karşılaştırması
            st.subheader("🔍 Çıkarılan Detayların Karşılaştırması")
            
            st.markdown("**Yetenekler Kesişimi:**")
            skills_a = set(data_a.get("YETENEKLER", []))
            skills_b = set(data_b.get("YETENEKLER", []))
            common_skills = skills_a.intersection(skills_b)
            st.write(f"Ortak Yetenekler ({len(common_skills)} adet): {', '.join(list(common_skills))}")