import pdfplumber
import re
from typing import Dict, Optional

# -------------------------- PARSING FUNKSİYONLARI --------------------------

def extract_text_from_pdf(pdf_path: str) -> Optional[str]:
    """PDF dosyasından pdfplumber kullanarak ham metni çıkarır."""
    try:
        # pdfplumber, CV formatları için önerilen araçlardan biridir[cite: 49].
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n\n"
            return full_text
    except Exception as e:
        print(f"Hata: PDF okunamadı {pdf_path}. Hata: {e}")
        return None

def preprocess_text(text: str) -> str:
    """Çıkarılan metni temizler (Fazla boşluk, satır sonları vb. düzenler)."""
    if not text:
        return ""
    text = re.sub(r'[\r\n]+', ' ', text)
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()

def extract_sections_simple(text: str) -> Dict[str, str]:
    """Basit kural tabanlı bölüm tespiti (regex + layout cues) yapar[cite: 23]."""
    # Proje planındaki ortak alanları içeren yaygın başlıklar[cite: 3].
    section_titles = [
        "EĞİTİM", "Egitim", "DENEYİM", "Deneyim", "YETENEKLER", "Yetenekler",
        "TEKNİK BECERİLER", "TEKNIK BECERILER", "TEKNİK", "TECHNICAL SKILLS",
        "YABANCI DİL", "YABANCI DİLLER", "LANGUAGES", "DİL", "DIL",
        "KURSLAR", "KURS", "COURSES",
        "SERTİFİKALAR", "CERTIFICATIONS",
        "KİŞİSEL BECERİLER", "KISISEL BECERILER", "PERSONAL SKILLS",
        "REFERANSLAR", "REFERANS", "REFERENCES",
        "SKILLS", "EXPERIENCE", "EDUCATION", "SUMMARY", "ÖZET", "CONTACT", "İLETİŞİM", "PROJELER"
    ]
    
    # Başlıkları yakalamak için regex paterni
    pattern = r'(?:^|\n)\s*(' + '|'.join(section_titles) + r')\s*\n'
    
    parts = replit_with_content(pattern, text)
    
    sections = {}
    current_title = "GENERAL"
    
    for part in parts:
        if part.strip().upper() in [t.upper() for t in section_titles]:
            current_title = part.strip().upper()
            sections[current_title] = ""
        elif current_title in sections:
            sections[current_title] += part.strip() + " "
        else:
            sections["GENERAL"] = sections.get("GENERAL", "") + part.strip() + " "

    return {k: v.strip() for k, v in sections.items() if v.strip()}

def replit_with_content(pattern: str, text: str) -> list:
    """re.split'in yakalanan grupları dahil etme versiyonu."""
    parts = re.split(pattern, text, flags=re.IGNORECASE)
    result = []
    # Çift indekslerde başlık, tek indekslerde içerik bulunur
    for i in range(len(parts)):
        if i % 2 == 0:
            result.append(parts[i])
        elif i % 2 == 1:
            result.append(parts[i])
    return [p for p in result if p]

def parse_cv(pdf_path: str) -> Dict[str, str]:
    """Tüm parsing akışını yönetir."""
    raw_text = extract_text_from_pdf(pdf_path)
    if not raw_text:
        return {}
    # Keep original newlines for reliable section heading detection
    sections = extract_sections_simple(raw_text)
    
    return sections