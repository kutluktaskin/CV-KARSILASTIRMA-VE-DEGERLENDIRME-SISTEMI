from typing import Dict, Any, Tuple, List
import json
import numpy as np

# -------------------------- BENZERLİK VE PUANLAMA --------------------------

def calculate_semantic_similarity(text1: str, text2: str) -> float:
    """
    Geçici: İki metin arasındaki basit Jaccard (Kelime Kesişim) benzerlik skoru.
    Gerçek projede SBERT/USE (Semantik embeddingler) kullanılacaktır[cite: 51].
    """
    if not text1 or not text2:
        return 0.0
        
    set1 = set(text1.lower().split())
    set2 = set(text2.lower().split())
    
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    
    return intersection / union if union > 0 else 0.0

def compare_cv_data(data_a: Dict[str, Any], data_b: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
    """
    İki CV'nin yapılandırılmış verilerini karşılaştırır ve puanlama stratejisine göre skor verir.
    """
    # Proje Planı Ağırlıklandırması [cite: 33]
    WEIGHTS = {
        "DENEYİM": 0.40,  # En yüksek ağırlık
        "YETENEKLER": 0.30,
        "EĞİTİM": 0.15,
        "ÖZET": 0.15      # Genel Semantik Uyum
    }
    
    section_scores = {}
    total_score = 0.0

    # 1. Yetenekler Karşılaştırması (Kesişim bazlı)
    skills_a = set(data_a.get("YETENEKLER", []))
    skills_b = set(data_b.get("YETENEKLER", []))
    union_len = len(skills_a.union(skills_b))
    skill_score = len(skills_a.intersection(skills_b)) / union_len if union_len > 0 else 0.0
    section_scores["YETENEKLER"] = skill_score

    # 2. Deneyim ve Eğitim Karşılaştırması (Semantik Benzerlik)
    # Yapılandırılmış veriyi metne çevirip benzerlik hesaplar.
    exp_score = calculate_semantic_similarity(
        json.dumps(data_a.get("DENEYİM", [])), 
        json.dumps(data_b.get("DENEYİM", []))
    )
    section_scores["DENEYİM"] = exp_score
    
    edu_score = calculate_semantic_similarity(
        json.dumps(data_a.get("EĞİTİM", [])),
        json.dumps(data_b.get("EĞİTİM", []))
    )
    section_scores["EĞİTİM"] = edu_score
    
    # 3. Genel Uyum (Özet) Karşılaştırması (Global semantik benzerlik yerine geçer) [cite: 32]
    summary_score = calculate_semantic_similarity(data_a.get("ÖZET", ""), data_b.get("ÖZET", ""))
    section_scores["ÖZET"] = summary_score
            
    # 4. Ağırlıklı Toplam Skoru Hesaplama
    for section, weight in WEIGHTS.items():
        if section in section_scores:
            total_score += section_scores[section] * weight
            
    return round(total_score, 3), section_scores

# -------------------------- RAPORLAMA --------------------------

def generate_report(data_a: Dict[str, Any], data_b: Dict[str, Any], total_score: float, section_scores: Dict[str, float]) -> List[str]:
    """
    İnsan kaynaklarına avantaj/dezavantaj raporu özeti oluşturur[cite: 5].
    """
    report = [f"--- Karşılaştırma Raporu (Genel Skor: {total_score * 100:.1f}%) ---"]
    
    # Yorumlama
    if total_score > 0.65:
        report.append("-> Özet: Adaylar Yüksek Uyumlu. Uzmanlık alanları ve deneyim süreleri yakın.")
    elif total_score > 0.4:
        report.append("-> Özet: Adaylar Orta Uyumlu. Farklı teknik yığınlarda (tech-stack) güçlüler.")
    else:
        report.append("-> Özet: Adaylar Düşük Uyumlu. Rol beklentisi netleştirilmelidir.")

    # Avantaj/Dezavantaj Tespiti [cite: 34]
    
    # Deneyim
    exp_score = section_scores.get('DENEYİM', 0.0)
    report.append(f"-> DENEYİM UYUMU: {exp_score:.2f} (Örtüşme {exp_score * 100:.1f}%).")
    
    # Yetenekler Farkı
    skills_a = set(data_a.get("YETENEKLER", []))
    skills_b = set(data_b.get("YETENEKLER", []))
    
    unique_to_a = skills_a - skills_b
    unique_to_b = skills_b - skills_a
    
    if unique_to_a:
        report.append(f"-> AVANTAJ Aday A (Benzersiz Yetenek): {', '.join(list(unique_to_a)[:2])} ve fazlası.")
    if unique_to_b:
        report.append(f"-> AVANTAJ Aday B (Benzersiz Yetenek): {', '.join(list(unique_to_b)[:2])} ve fazlası.")
        
    return report