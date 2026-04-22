import re
import json
import os

def process_m3u_to_individual_jsons(m3u_file, output_folder):
    # Klasör yapısını oluştur: stream/tv/
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    if not os.path.exists(m3u_file):
        print(f"Hata: {m3u_file} bulunamadı.")
        return

    with open(m3u_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex: Kanal adı (#EXTINF sonrası virgül) ve altındaki URL'yi yakalar
    pattern = re.compile(r'#EXTINF:.*?,(.*?)\n(http.*?)(?:\n|$)', re.MULTILINE)
    matches = pattern.findall(content)

    # Kanalları grupla
    channels = {}

    for name, url in matches:
        clean_name = name.strip()
        # Dosya ismi için geçersiz karakterleri ( / \ : * ? " < > | ) temizle
        safe_filename = re.sub(r'[\\/*?:"<>|]', "-", clean_name)
        clean_url = url.strip()

        if safe_filename not in channels:
            channels[safe_filename] = {"display_name": clean_name, "urls": []}
        
        if clean_url not in channels[safe_filename]["urls"]:
            channels[safe_filename]["urls"].append(clean_url)

    # Her kanal için ayrı JSON
    for safe_name, info in channels.items():
        output_data = {"streams": []}
        display_name = info["display_name"]
        
        for index, url in enumerate(info["urls"]):
            # Birden fazla kaynak varsa ismi koru ama yanına numara ekle (isteğe bağlı)
            label = display_name if len(info["urls"]) == 1 else f"{display_name} (Kaynak {index + 1})"
            
            stream_obj = {
                "name": label, # Burada "SERVER 1" yerine kanalın kendi ismi var
                "title": f"{display_name} - Yayın Hattı {index + 1}",
                "url": url
            }
            output_data["streams"].append(stream_obj)

        file_path = os.path.join(output_folder, f"{safe_name}.json")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"Başarılı: {file_path}")

if __name__ == "__main__":
    process_m3u_to_individual_jsons("liste.m3u", "./stream/tv")
