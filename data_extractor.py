import spacy
from typing import Dict, List, Any
from collections import defaultdict
import re
# YENİ KÜTÜPHANELER: İleri NER (transformers) entegrasyonu için burada çağrılacaktır.

# --- MODEL YÜKLEME VE FALLBACK MANTIĞI ---

# Custom NER model yolunu veya Hugging Face model adını buraya girin (Gelecekteki geliştirme)
CUSTOM_NER_MODEL_NAME = "en_core_web_sm" # Şimdilik temel spaCy modelini kullanıyoruz.

try:
    # Eğitilmiş Custom NER modelini yüklemeyi dene
    nlp = spacy.load(CUSTOM_NER_MODEL_NAME)
    print(f"NLP: '{CUSTOM_NER_MODEL_NAME}' modeli başarıyla yüklendi.")
except OSError:
    print(f"HATA: '{CUSTOM_NER_MODEL_NAME}' modeli bulunamadi. Temel spaCy modeline geri donuluyor.")
    try:
        # Custom model yoksa temel modeli kullan
        nlp = spacy.load("en_core_web_sm")
        print("NLP: Temel 'en_core_web_sm' modeli yüklendi.")
    except Exception as e:
        print(f"KRİTİK HATA: Hiçbir spaCy modeli yüklenemedi. NLP islemleri yapilamayacak. Hata: {e}")
        nlp = None

# --- DETAYLI ALAN ÇIKARIMI FONKSİYONLARI ---

def extract_skills(text: str) -> List[str]:
    """Yetenekler bölümünden anahtar kelimeleri/teknolojileri çıkarır (Basit kural tabanlı)."""
    if not text:
        return []
        
    # Geliştirme: Yetenekleri daha temiz ayırmak için virgül, nokta, yeni satır vb. karakterleri kullan.
    skills = [s.strip() for s in re.split(r'[,;•\n\t]', text) if len(s.strip()) > 2 and s.strip().count(' ') < 4]
    
    # Fazla boşlukları, küçük harfe çevirmeleri ve tekrarları kaldır.
    return list(set([s.lower() for s in skills if s]))


def extract_languages(text: str) -> List[Dict[str, str]]:
    """Basitçe yabancı dil ve seviyesini çıkarır. Satır veya virgülle ayrılmış girdileri işler."""
    if not text:
        return []

    parts = [p.strip() for p in re.split(r'[;,\n\t•-]', text) if p.strip()]
    langs = []
    level_pattern = re.compile(r"(advanced|intermediate|basic|fluent|beginner|ileri|orta|başlangıç|başlangic|çok iyi|iyi)", re.I)
    for p in parts:
        match = level_pattern.search(p)
        if match:
            level = match.group(0)
            name = level_pattern.sub('', p).strip(' -,:;')
            langs.append({"dil": name, "seviyesi": level})
        else:
            # Eğer virgülden önce/proficiency yoksa sadece dil ismi kaydet
            langs.append({"dil": p, "seviyesi": ""})

    return langs


def extract_references(text: str) -> List[Dict[str, str]]:
    """Referans metninden e-posta ve telefon numarası arar ve temel alanları çıkarır."""
    if not text:
        return []

    entries = [e.strip() for e in re.split(r'\n\n|\n-\s|\n•|;|\n', text) if e.strip()]
    refs = []
    email_re = re.compile(r"[\w\.-]+@[\w\.-]+")
    phone_re = re.compile(r"\+?\d[\d\s\-\(\)]{6,}\d")

    for e in entries:
        ref = {"raw": e, "email": "", "phone": "", "name": ""}
        em = email_re.search(e)
        ph = phone_re.search(e)
        if em:
            ref['email'] = em.group(0)
        if ph:
            ref['phone'] = ph.group(0)

        # Basit isim tahmini: eğer virgül yoksa ilk kelimeler isim olabilir
        name = e.split('\n')[0]
        # temizle
        name = re.sub(r"\b(Email:|E-mail:|Tel:|Phone:|Telefon:)\b.*", '', name, flags=re.I).strip()
        ref['name'] = name
        refs.append(ref)

    return refs


def extract_experience_details(experience_text: str) -> List[Dict[str, str]]:
    """
    Deneyim metninden (Custom NER veya spaCy) pozisyon, kurum ve tarihleri çıkarır.
    
    AMAÇ: Her bir deneyim girdisini (örneğin 2020-2023 arası ABC Teknoloji) ayrı ayrı yapılandırmak.
    """
    if not nlp or not experience_text:
        return []

    doc = nlp(experience_text)
    experiences = []
    
    # Bu basit bir yer tutucudur. Gerçek Custom NER, doğru etiketleri (LABEL: COMPANY, LABEL: TITLE) sağlayacaktır.
    current_experience = defaultdict(str)
    
    # Heuristik: Paragraf sonlarını kullanarak deneyimleri ayırmaya çalış
    experience_entries = experience_text.split('\n\n')
    
    for entry in experience_entries:
        if not entry.strip():
            continue

        entry_doc = nlp(entry.strip())
        
        details = defaultdict(str)
        # SpaCy'nin hazır etiketlerini kullan (geçici NER)
        for ent in entry_doc.ents:
            if ent.label_ in ["DATE", "GPE"]: # GPE: Şehir, Ülke gibi yerler
                details["Tarih"] += ent.text + " "
            elif ent.label_ == "ORG": # ORG: Organizasyon (Kurum Adı olabilir)
                if not details["Kurum"]:
                    details["Kurum"] = ent.text
        
        # Heuristik: Entry'nin başlığını (genellikle ilk cümle) pozisyon/kurum olarak kullan
        first_line = entry.split('\n')[0].strip()
        details["Raw_Entry"] = first_line
        
        # Eğer bir Kurum veya Tarih çıkarıldıysa kaydet
        if details.get("Kurum") or details.get("Tarih"):
            experiences.append(dict(details))
            
    # Eğer deneyimler ayrılamadıysa, tüm metni tek bir girdi olarak döndür
    if not experiences and experience_text.strip():
         experiences.append({"Raw_Entry": experience_text.strip()})

    return experiences


def extract_education_details(education_text: str) -> List[Dict[str, str]]:
    """Eğitim metninden kurum, derece ve tarihleri çıkarır."""
    if not nlp or not education_text:
        return []

    # Eğitim verisi de Deneyim verisine benzer şekilde işlenebilir.
    education_entries = education_text.split('\n\n')
    education_list = []

    for entry in education_entries:
        if not entry.strip():
            continue
        
        details = defaultdict(str)
        entry_doc = nlp(entry.strip())
        
        for ent in entry_doc.ents:
             if ent.label_ in ["DATE"]:
                details["Tarih"] += ent.text + " "
             elif ent.label_ in ["ORG"]:
                details["Kurum"] = ent.text

        details["Raw_Entry"] = entry.strip()
        
        if details.get("Raw_Entry"):
            education_list.append(dict(details))

    return education_list


# --- ANA ÇIKARIM FONKSİYONU ---
def extract_structured_data(sections: Dict[str, str]) -> Dict[str, Any]:
    """
    Tüm bölümlerden yapılandırılmış veriyi çıkarır (Hafta 7-9 görevi).
    """
    structured_data = {
        "DENEYİM": [],
        "EĞİTİM": [],
        "YETENEKLER": [],
        "SERTİFİKALAR": [], # Yeni eklenecek alanlar
        "PROJELER": [],     # Yeni eklenecek alanlar
        "TEKNİK_BECERİLER": [],
        "YABANCI_DİL": [],
        "KURSLAR": [],
        "KİŞİSEL_BECERİLER": [],
        "REFERANSLAR": [],
        "ÖZET": sections.get("ÖZET", sections.get("SUMMARY", ""))
    }
    
    # 1. Deneyim Çıkarımı
    experience_text = sections.get("DENEYİM", sections.get("EXPERIENCE", ""))
    if experience_text:
        structured_data["DENEYİM"] = extract_experience_details(experience_text)
        
    # 2. Eğitim Çıkarımı
    education_text = sections.get("EĞİTİM", sections.get("EDUCATION", ""))
    if education_text:
        structured_data["EĞİTİM"] = extract_education_details(education_text)
        
    # 3. Yetenek Çıkarımı
    skills_text = sections.get("YETENEKLER", sections.get("SKILLS", ""))
    if skills_text:
        structured_data["YETENEKLER"] = extract_skills(skills_text)

    # 3b. Teknik Beceriler (ayrı bir bölüm varsa)
    tech_text = sections.get("TEKNİK BECERİLER", sections.get("TEKNIK BECERILER", ""))
    if tech_text:
        structured_data["TEKNİK_BECERİLER"] = extract_skills(tech_text)

    # 4. Sertifikalar Çıkarımı (Sadece metni al)
    # İleride NER ile Sertifika Adı ve Veriliş Tarihi gibi alt alanlar çıkarılmalıdır.
    certs_text = sections.get("SERTİFİKALAR", sections.get("CERTIFICATIONS", ""))
    if certs_text:
        structured_data["SERTİFİKALAR"].append({"Raw_Entry": certs_text.strip()})

    # 4b. Kurslar
    courses_text = sections.get("KURSLAR", sections.get("COURSES", ""))
    if courses_text:
        structured_data["KURSLAR"].append({"Raw_Entry": courses_text.strip()})

    # 5. Projeler Çıkarımı (Sadece metni al)

    # 5. Projeler Çıkarımı (Sadece metni al)
    projects_text = sections.get("PROJELER", "")
    if projects_text:
        structured_data["PROJELER"].append({"Raw_Entry": projects_text.strip()})

    # 6. Yabancı Dil
    languages_text = sections.get("YABANCI DİL", sections.get("YABANCI DİLLER", sections.get("LANGUAGES", "")))
    if languages_text:
        structured_data["YABANCI_DİL"] = extract_languages(languages_text)

    # 7. Kişisel Beceriler
    personal_text = sections.get("KİŞİSEL BECERİLER", sections.get("KISISEL BECERILER", sections.get("PERSONAL SKILLS", "")))
    if personal_text:
        structured_data["KİŞİSEL_BECERİLER"] = extract_skills(personal_text)

    # 8. Referanslar
    refs_text = sections.get("REFERANSLAR", sections.get("REFERANS", sections.get("REFERENCES", "")))
    if refs_text:
        structured_data["REFERANSLAR"] = extract_references(refs_text)


    return structured_data