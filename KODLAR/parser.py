import os
import pdfplumber
import re

cv_klasor_yolu = "CV DOSYALARI/" 
dosya_listesi = os.listdir(cv_klasor_yolu)

print(f"'{cv_klasor_yolu}' klasöründe toplam {len(dosya_listesi)} adet dosya bulundu.\n")

# Analiz sonuçlarını saklamak için boş bir liste oluşturalım.
tum_cv_bilgileri = []

for pdf_adi in dosya_listesi:
    
    if not pdf_adi.endswith(".pdf"):
        continue

    tam_dosya_yolu = os.path.join(cv_klasor_yolu, pdf_adi)

    metin = ""
    isim = "Bulunamadı"
    email = "Bulunamadı"

    try:
        with pdfplumber.open(tam_dosya_yolu) as pdf:
            ilk_sayfa = pdf.pages[0]
            metin = ilk_sayfa.extract_text() or ""
    except Exception as e:
        print(f"'{pdf_adi}' dosyası okunurken bir hata oluştu: {e}")
        continue

    # E-posta bulma (Bu kısım zaten doğru çalışıyor)
    email_eslesmesi = re.search(r'[\w\.-]+@[\w\.-]+', metin)
    if email_eslesmesi:
        email = email_eslesmesi.group(0)

    # --- İSİM BULMA KISMINI GÜNCELLEDİK ---
    # Aranacak etiketler listesine "ad:" ekledik.
    aranacak_etiketler = ["name:", "isim:", "ad soyad:", "ad:"]
    
    for satir in metin.split('\n'):
        # Satırı küçük harfe çevirip BÜTÜN BOŞLUKLARI SİLİYORUZ.
        # Böylece "N ame:" ifadesi "name:" haline gelir ve eşleşir.
        satir_temiz = satir.lower().replace(" ", "")
        
        for etiket in aranacak_etiketler:
            if satir_temiz.startswith(etiket):
                # Bilgiyi orijinal, boşluklu satırdan alıyoruz.
                isim = satir.split(':', 1)[1].strip()
                break # İsmi bulduktan sonra etiket aramayı durdur
        if isim != "Bulunamadı":
            break # İsmi bulduktan sonra diğer satırlara bakmayı bırak

    # Bulduğumuz bilgileri bir sözlük olarak listeye ekleyelim
    cv_verisi = {"Dosya Adı": pdf_adi, "İsim": isim, "E-posta": email}
    tum_cv_bilgileri.append(cv_verisi)


# --- DÖNGÜ BİTTİ, ŞİMDİ TOPLU SONUÇLARI YAZDIRALIM ---

print("--- TÜM CV'LER İÇİN AYRIŞTIRMA SONUÇLARI ---")
for cv in tum_cv_bilgileri:
    print(f"Dosya Adı: {cv['Dosya Adı']}")
    print(f"İsim     : {cv['İsim']}")
    print(f"E-posta  : {cv['E-posta']}")
    print("="*50)