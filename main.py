from cv_parser import parse_cv
from data_extractor import extract_structured_data
from comparison_engine import compare_cv_data, generate_report
from typing import Dict, Any, Tuple
import os
import json

# --- Windows Dosya Yolları ---
# "data" klasöründeki dosyalarınızı çağırır
CV_A_PATH = os.path.join("data", "CV_A.pdf")
CV_B_PATH = os.path.join("data", "CV_B.pdf")

def run_analysis(cv_path: str, name: str) -> Tuple[Dict[str, str], Dict[str, Any]]:
    """Tek bir CV için Parsing ve Yapılandırılmış Veri Çıkarımını çalıştırır."""
    print(f"\n--- ANALİZ BAŞLADI: {name} ({cv_path}) ---")
    
    # 1. Parsing (Hafta 5-6)
    sections = parse_cv(cv_path)
    
    if not sections:
        print(f"HATA: {name} dosyası okunamadı veya bölüm çıkarılamadı.")
        return {}, {}

    print(f"  [PARSING BAŞARILI] Toplam {len(sections)} bölüm bulundu.")
    # 2. Yapılandırılmış Veri Çıkarımı (Hafta 7-9)
    structured_data = extract_structured_data(sections)
    
    print("  [ÇIKARIM SONUCU] Yapılandırılmış Veri:")
    print(json.dumps(structured_data, indent=2, ensure_ascii=False))

    return sections, structured_data

def main():
    print("=" * 60)
    print("AKILLI CV KARŞILAŞTIRMA SİSTEMİ - PROTOTİP AKIŞI BAŞLADI")
    print("=" * 60)
    
    # Adım 1 & 2: CV'leri Tek Tek İşle
    sections_a, data_a = run_analysis(CV_A_PATH, "Aday A")
    sections_b, data_b = run_analysis(CV_B_PATH, "Aday B")

    if not data_a or not data_b:
        print("\n!!! Karşılaştırma yapılamıyor: En az bir CV'den veri çıkarılamadı. !!!")
        return

    print("\n" + "=" * 60)
    print("3. KARŞILAŞTIRMA VE PUANLAMA (Hafta 10 Teslimatı)")
    print("=" * 60)

    # Adım 3: Karşılaştırma ve Puanlama
    total_score, section_scores = compare_cv_data(data_a, data_b)

    print(f"GENEL BENZERLİK SKORU: {total_score * 100:.1f} % (Ağırlıklı Toplam Skor)")
    print(f"BÖLÜM SKORLARI (Örn: Deneyim, Yetenekler): {section_scores}")
    
    # Adım 4: Raporlama
    report = generate_report(data_a, data_b, total_score, section_scores)

    print("\n--- 4. İK UZMANI RAPOR ÖZETİ (Hafta 11 Taslağı) ---")
    for line in report:
        print(line)
    
    print("=" * 60)

if __name__ == "__main__":
    main()