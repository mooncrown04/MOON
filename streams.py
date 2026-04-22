import re
import json
import os

def m3u_to_json_processor(m3u_file, output_folder):
    # 1. Klasör kontrolü ve oluşturma
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Klasör oluşturuldu: {output_folder}")

    output_json_path = os.path.join(output_folder, "streams.json")
    
    # 2. M3U dosyasını oku
    if not os.path.exists(m3u_file):
        print(f"Hata: '{m3u_file}' dosyası bulunamadı!")
        return

    with open(m3u_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 3. Mevcut JSON verisini yükle (Kontrol için)
    existing_urls = set()
    data = {"streams": []}
    
    if os.path.exists(output_json_path):
        with open(output_json_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                # Mevcut URL'leri set içine alarak mükerrer kayıt kontrolü yapıyoruz
                existing_urls = {s['url'] for s in data.get("streams", [])}
            except json.JSONDecodeError:
                data = {"streams": []}

    # 4. M3U İçeriğini Ayrıştır
    # Desen: #EXTINF:...,Kanal İsmi \n URL
    pattern = re.compile(r'#EXTINF:.*?,(.*?)\n(http.*?)(?:\n|$)', re.MULTILINE)
    matches = pattern.findall(content)

    new_count = 0
    for name, url in matches:
        clean_url = url.strip()
        clean_name = name.strip()

        # Eğer URL zaten dosyada varsa atla (Kontrol mekanizması)
        if clean_url in existing_urls:
            continue

        stream_obj = {
            "name": clean_name,
            "title": f"{clean_name} |ULUSAL",
            "url": clean_url,
            "behaviorHints": {
                "notClickable": False,
                "bingeGroup": clean_name.lower().replace(" ", "-")
            }
        }
        data["streams"].append(stream_obj)
        existing_urls.add(clean_url)
        new_count += 1

    # 5. Sonucu Kaydet
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    if new_count > 0:
        print(f"İşlem Başarılı! {new_count} yeni kanal eklendi.")
        print(f"Dosya Yolu: {output_json_path}")
    else:
        print("Yeni kanal bulunamadı, liste güncel.")

# --- KULLANIM ---
# Dosya adın: liste.m3u
# Kayıt yolun: /tv/stream (veya './tv/stream')
m3u_to_json_processor("liste.m3u", "./tv/stream")
