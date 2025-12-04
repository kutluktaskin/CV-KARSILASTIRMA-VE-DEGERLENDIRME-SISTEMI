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
    # Redistributed weights to cover new fields. Sum == 1.0
    WEIGHTS = {
        "DENEYİM": 0.35,
        "YETENEKLER": 0.25,
        "TEKNİK_BECERİLER": 0.15,
        "EĞİTİM": 0.10,
        "ÖZET": 0.05,
        "YABANCI_DİL": 0.03,
        "KURSLAR": 0.03,
        "SERTİFİKALAR": 0.02,
        "KİŞİSEL_BECERİLER": 0.01,
        "REFERANSLAR": 0.01
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

    # Teknik Beceriler (kesişim bazlı)
    tech_a = set(data_a.get("TEKNİK_BECERİLER", []))
    tech_b = set(data_b.get("TEKNİK_BECERİLER", []))
    tech_union = len(tech_a.union(tech_b))
    tech_score = len(tech_a.intersection(tech_b)) / tech_union if tech_union > 0 else 0.0
    section_scores["TEKNİK_BECERİLER"] = tech_score

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
    
    # Yabancı dil: compare language names (if structured) or fallback to semantic
    langs_a = data_a.get("YABANCI_DİL", [])
    langs_b = data_b.get("YABANCI_DİL", [])
    try:
        names_a = set([l.get("dil", l).lower() if isinstance(l, dict) else str(l).lower() for l in langs_a])
        names_b = set([l.get("dil", l).lower() if isinstance(l, dict) else str(l).lower() for l in langs_b])
        lang_union = len(names_a.union(names_b))
        lang_score = len(names_a.intersection(names_b)) / lang_union if lang_union > 0 else 0.0
    except Exception:
        lang_score = calculate_semantic_similarity(json.dumps(langs_a), json.dumps(langs_b))
    section_scores["YABANCI_DİL"] = lang_score

    # Kurslar, Sertifikalar, Kişisel Beceriler, Projeler, Referanslar: semantic similarity on text
    cert_score = calculate_semantic_similarity(json.dumps(data_a.get("SERTİFİKALAR", [])), json.dumps(data_b.get("SERTİFİKALAR", [])))
    section_scores["SERTİFİKALAR"] = cert_score

    courses_score = calculate_semantic_similarity(json.dumps(data_a.get("KURSLAR", [])), json.dumps(data_b.get("KURSLAR", [])))
    section_scores["KURSLAR"] = courses_score

    personal_score = calculate_semantic_similarity(json.dumps(data_a.get("KİŞİSEL_BECERİLER", [])), json.dumps(data_b.get("KİŞİSEL_BECERİLER", [])))
    section_scores["KİŞİSEL_BECERİLER"] = personal_score

    projects_score = calculate_semantic_similarity(json.dumps(data_a.get("PROJELER", [])), json.dumps(data_b.get("PROJELER", [])))
    section_scores["PROJELER"] = projects_score

    refs_score = calculate_semantic_similarity(json.dumps(data_a.get("REFERANSLAR", [])), json.dumps(data_b.get("REFERANSLAR", [])))
    section_scores["REFERANSLAR"] = refs_score
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