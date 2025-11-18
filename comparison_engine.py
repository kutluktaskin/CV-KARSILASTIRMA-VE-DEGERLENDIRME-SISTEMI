from typing import Dict, Any, Tuple, List
import json
import numpy as np
# YENİ KÜTÜPHANELER: Semantik Benzerlik ve Matris İşlemleri için
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity 

# --- SEMANTİK MODEL YÜKLEME ---
# Modelin bir kez yüklenmesini sağlayın. 'all-MiniLM-L6-v2', hızlı ve iyi performanslı bir modeldir.
# Projenin çalışması için bu kütüphanenin kurulmuş olması gerekir.
try:
    # Modelin bir kez yüklenmesi gerektiğinden, global bir değişken olarak tanımlanır.
    SEMANTIC_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
    print("SBERT modeli başarıyla yüklendi.")
except Exception as e:
    print(f"HATA: Sentence Transformer yuklenemedi. Lutfen 'pip install sentence-transformers' komutunu calistirin. Hata: {e}")
    SEMANTIC_MODEL = None

# -------------------------- BENZERLİK VE PUANLAMA --------------------------

def calculate_semantic_similarity(text1: str, text2: str) -> float:
    """
    Sentence-Transformers (SBERT) kullanarak iki metin arasındaki Kosinüs Benzerliğini hesaplar.
    Bu, metinlerin anlamsal olarak ne kadar benzediğini ölçer.
    """
    # Eğer model yüklenemediyse veya metin yoksa, 0.0 döndürülür
    if SEMANTIC_MODEL is None or not text1 or not text2:
        return 0.0
    
    # 1. Metinleri vektörlere (embeddings) dönüştür
    embeddings = SEMANTIC_MODEL.encode([text1, text2])
    
    # 2. Kosinüs Benzerliğini hesapla (Skor -1 ile 1 arasındadır)
    # Bu metot Kosinüs Benzerliği (Cosine Similarity) matrisini üretir.
    score_matrix = cosine_similarity([embeddings[0]], [embeddings[1]])
    
    # Matrisin ilk elemanı, yani iki cümle arasındaki benzerlik skoru döndürülür
    score = score_matrix[0][0]
    
    # Skorlar -1 (tamamen zıt) ile 1 (tamamen aynı) arasında olabileceğinden,
    # genellikle pozitif bir aralıkta kalması beklendiği için 0 ile 1 arasına sıkıştırılır.
    return float(max(0.0, score)) # Negatif skorları 0'a sabitler

def compare_cv_data(data_a: Dict[str, Any], data_b: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
    """
    İki CV'nin yapılandırılmış verilerini karşılaştırır ve puanlama stratejisine göre skor verir.
    """
    # Proje Planı Ağırlıklandırması [cite: Plan_CV_Karsilastirma_ve_Degerlendirme_Sistemi.docx, source 33]
    WEIGHTS = {
        "DENEYİM": 0.40,  # En yüksek ağırlık
        "YETENEKLER": 0.30,
        "EĞİTİM": 0.15,
        "ÖZET": 0.15      # Genel Semantik Uyum
    }
    
    section_scores = {}
    total_score = 0.0

    # 1. Yetenekler Karşılaştırması (Kesişim bazlı - Hızlı tarama için geçici olarak bırakılabilir)
    # İleride her yeteneği SBERT ile karşılaştırmak daha doğru olur.
    skills_a = set(data_a.get("YETENEKLER", []))
    skills_b = set(data_b.get("YETENEKLER", []))
    union_len = len(skills_a.union(skills_b))
    skill_score = len(skills_a.intersection(skills_b)) / union_len if union_len > 0 else 0.0
    section_scores["YETENEKLER"] = skill_score

    # 2. Deneyim, Eğitim ve Özet Karşılaştırması (SEMANTİK)
    
    # Deneyim: Yapılandırılmış veriyi metne çevirip anlamsal benzerlik hesaplar.
    exp_score = calculate_semantic_similarity(
        json.dumps(data_a.get("DENEYİM", [])), 
        json.dumps(data_b.get("DENEYİM", []))
    )
    section_scores["DENEYİM"] = exp_score
    
    # Eğitim: Eğitim verilerinin anlamsal benzerlik skoru
    edu_score = calculate_semantic_similarity(
        json.dumps(data_a.get("EĞİTİM", [])),
        json.dumps(data_b.get("EĞİTİM", []))
    )
    section_scores["EĞİTİM"] = edu_score
    
    # Genel Uyum (Özet): Global semantik benzerlik skoru [cite: Plan_CV_Karsilastirma_ve_Degerlendirme_Sistemi.docx, source 32]
    summary_score = calculate_semantic_similarity(data_a.get("ÖZET", ""), data_b.get("ÖZET", ""))
    section_scores["ÖZET"] = summary_score
            
    # 3. Ağırlıklı Toplam Skoru Hesaplama
    for section, weight in WEIGHTS.items():
        if section in section_scores:
            total_score += section_scores[section] * weight
            
    return round(total_score, 3), section_scores

# -------------------------- RAPORLAMA --------------------------

def generate_report(data_a: Dict[str, Any], data_b: Dict[str, Any], total_score: float, section_scores: Dict[str, float]) -> List[str]:
    """
    İnsan kaynaklarına avantaj/dezavantaj raporu özeti oluşturur [cite: Plan_CV_Karsilastirma_ve_Degerlendirme_Sistemi.docx, source 5, 34].
    """
    report = [f"--- Karşılaştırma Raporu (Genel Skor: {total_score * 100:.1f}%) ---"]
    
    # Yorumlama
    if total_score > 0.75:
        report.append("-> Özet: Adaylar Yüksek Uyumlu. Semantik benzerlik, rollerin mükemmel örtüştüğünü gösteriyor.")
    elif total_score > 0.5:
        report.append("-> Özet: Adaylar Orta Uyumlu. Temel bilgi ve deneyim alanları örtüşüyor, ancak uzmanlıklar farklı.")
    else:
        report.append("-> Özet: Adaylar Düşük Uyumlu. Rol beklentisi netleştirilmeli veya uzmanlık alanları tamamen farklı.")

    # Avantaj/Dezavantaj Tespiti [cite: Plan_CV_Karsilastirma_ve_Degerlendirme_Sistemi.docx, source 34]
    
    # Deneyim
    exp_score = section_scores.get('DENEYİM', 0.0)
    report.append(f"-> DENEYİM UYUMU: {exp_score:.2f} (Semantik Örtüşme {exp_score * 100:.1f}%).")
    
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