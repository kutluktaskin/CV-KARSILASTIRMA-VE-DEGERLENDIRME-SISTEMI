import spacy
from typing import Dict, List, Any
from collections import defaultdict
import re

# SpaCy modelini yükleyin
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("SpaCy modeli yüklenemedi. Kurulumu kontrol edin.")
    nlp = None

# -------------------------- ÇIKARIM FONKSİYONLARI --------------------------

def extract_skills(text: str) -> List[str]:
    """Yetenekler bölümünden anahtar kelimeleri çıkarır."""
    if not text:
        return []
        
    skills = [s.strip() for s in re.split(r'[,;•\n]', text) if len(s.strip()) > 2]
    return list(set(skills))

def extract_experience_details(experience_text: str) -> List[Dict[str, str]]:
    """Deneyim metninden NLP/Regex ile detaylı verileri (tarih, kurum, pozisyon) çıkarır."""
    if not nlp or not experience_text:
        return []

    doc = nlp(experience_text)
    experiences = []
    
    # Basit Heuristik: SpaCy'nin hazır NER etiketlerini kullan
    current_exp = defaultdict(str)
    
    for ent in doc.ents:
        if ent.label_ == "DATE":
            current_exp["Tarih"] += ent.text + " "
        elif ent.label_ == "ORG" or ent.label_ == "GPE":
             if not current_exp["Kurum"]:
                 current_exp["Kurum"] = ent.text
    
    # Gerçek projede custom NER ile daha isabetli pozisyon ve kurum çıkarımı yapılmalıdır.
    sentences = [sent.text.strip() for sent in doc.sents]
    if sentences:
        current_exp["Pozisyon"] = sentences[0].split('|')[1].strip() if '|' in sentences[0] else sentences[0]
        current_exp["Açıklama"] = " ".join(sentences[1:])
    
    if current_exp.get("Kurum") or current_exp.get("Pozisyon"):
        experiences.append(dict(current_exp))
    
    return experiences

# -------------------------- ANA ÇIKARIM FONKSİYONU --------------------------

def extract_structured_data(sections: Dict[str, str]) -> Dict[str, Any]:
    """Tüm CV bölümlerinden yapılandırılmış veriyi çıkarır."""
    structured_data = {
        "DENEYİM": [],
        "EĞİTİM": [],
        "YETENEKLER": [],
        "ÖZET": sections.get("ÖZET", sections.get("SUMMARY", ""))
    }
    
    experience_text = sections.get("DENEYİM", sections.get("EXPERIENCE", ""))
    if experience_text:
        structured_data["DENEYİM"] = extract_experience_details(experience_text)
        
    skills_text = sections.get("YETENEKLER", sections.get("SKILLS", ""))
    if skills_text:
        structured_data["YETENEKLER"] = extract_skills(skills_text)

    # Eğitim ve diğer alanlar da benzer şekilde işlenmelidir.
    education_text = sections.get("EĞİTİM", sections.get("EDUCATION", ""))
    if education_text:
         structured_data["EĞİTİM"].append({"Kurum/Derece": education_text.split('|')[0].strip()})

    return structured_data