import re
import json
import os

def slugify(text):
    """Kanal ismini bingeGroup için uygun formata getirir."""
    text = text.lower()
    text = re.sub(r'\s+', '-', text)
    return re.sub(r'[^\w\-]', '', text)

def process_m3u_to_custom_jsons(m3u_file, output_folder):
    # 1. Klasör yapısını oluştur: stream/tv/
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Klasör yapısı oluşturuldu: {output_folder}")

    if not os.path.exists(m3u_file):
        print(f"Hata: {m3u_file} dosyası bulunamadı.")
        return

    with open(m3u_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 2. M3U Ayrıştırma (Grup, Logo ve İsim bilgilerini çeker)
    # Bu regex; logo, grup ismi, kanal ismi ve url'yi yakalamaya çalışır.
    pattern = re.compile(r'#EXTINF:.*?(?:group-title="(.*?)")?.*?(?:tvg-logo="(.*?)")?,(.*?)\n(http.*?)(?:\n|$)', re.MULTILINE)
    matches = pattern.findall(content)

    channels = {}

    for group, logo, name, url in matches:
        clean_name = name.strip()
        safe_filename = re.sub(r'[\\/*?:"<>|]', "-", clean_name) # Dosya adı güvenliği
        clean_url = url.strip()
        clean_group = group.strip().upper() if group else "ULUSAL"

        if safe_filename not in channels:
            channels[safe_filename] = {
                "display_name": clean_name,
                "group": clean_group,
                "streams": []
            }
        
        # Aynı URL'yi mükerrer eklememek için kontrol
        if not any(s['url'] == clean_url for s in channels[safe_filename]["streams"]):
            stream_obj = {
                "name": clean_name,
                "title": f"{clean_name} |{clean_group}",
                "url": clean_url,
                "behaviorHints": {
                    "notClickable": False,
                    "bingeGroup": slugify(clean_name)
                }
            }
            channels[safe_filename]["streams"].append(stream_obj)

    # 3. JSON Dosyalarını Oluştur
    for safe_name, info in channels.items():
        file_path = os.path.join(output_folder, f"{safe_name}.json")
        
        output_data = {
            "streams": info["streams"]
        }

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"Dosya oluşturuldu: {file_path}")

if __name__ == "__main__":
    # İstediğin klasör yapısı burada belirlendi
    process_m3u_to_custom_jsons("liste.m3u", "./stream/tv")
