import re
import json
import os

def process_m3u_to_single_list(m3u_file, output_path):
    # 1. Klasör kontrolü
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 2. M3U dosyasını oku
    if not os.path.exists(m3u_file):
        print(f"Hata: {m3u_file} bulunamadı.")
        return

    with open(m3u_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 3. Mevcut JSON'u yükle veya yeni oluştur
    if os.path.exists(output_path):
        with open(output_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except:
                data = {"streams": []}
    else:
        data = {"streams": []}

    # 4. M3U Ayrıştırma
    # Desen: Kanal adını ve linki yakalar
    pattern = re.compile(r'#EXTINF:.*?,(.*?)\n(http.*?)(?:\n|$)', re.MULTILINE)
    matches = pattern.findall(content)

    for name, url in matches:
        clean_name = name.strip()
        clean_url = url.strip()

        # Kanal daha önce eklenmiş mi kontrol et
        found_channel = None
        for item in data["streams"]:
            if item["name"] == clean_name:
                found_channel = item
                break

        if found_channel:
            # Kanal var, link daha önce eklenmemişse listeye ekle
            # Not: Senin formatında linkler tek bir objede mi yoksa 
            # dizi içinde mi olmalı? Eğer dizi içindeyse 'url' yerine 'urls' yapabiliriz.
            # Ama senin verdiğin örnekte tek 'url' var. 
            # Alternatifleri 'title' üzerinden ayırt ederek ekliyoruz:
            
            # Eğer bu spesifik URL zaten yoksa ekle
            is_url_exists = any(clean_url == s.get("url") for s in data["streams"] if s["name"] == clean_name)
            
            if not is_url_exists:
                new_entry = {
                    "name": clean_name,
                    "title": f"{clean_name} | ALTERNATIF",
                    "url": clean_url,
                    "behaviorHints": {
                        "notClickable": False,
                        "bingeGroup": clean_name.lower().replace(" ", "-")
                    }
                }
                data["streams"].append(new_entry)
        else:
            # Kanal yok, yeni kanal olarak ekle
            new_entry = {
                "name": clean_name,
                "title": f"{clean_name} | ULUSAL",
                "url": clean_url,
                "behaviorHints": {
                    "notClickable": False,
                    "bingeGroup": clean_name.lower().replace(" ", "-")
                }
            }
            data["streams"].append(new_entry)

    # 5. Kaydet
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"İşlem tamamlandı. Liste güncellendi: {output_path}")

# Kullanım
process_m3u_to_single_list("liste.m3u", "./tv/streams.json")
