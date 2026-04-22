import re
import json
import os

def slugify(text):
    """Kanal ismini bingeGroup için uygun formata (ör: a2-tv) getirir."""
    text = text.lower()
    text = re.sub(r'\s+', '-', text)
    return re.sub(r'[^\w\-]', '', text)

def process_m3u_to_custom_jsons(m3u_file, output_folder):
    # Klasör yapısını oluştur: stream/tv/
    if not os.path.exists(output_folder):
        os.makedirs(output_folder, exist_ok=True)

    if not os.path.exists(m3u_file):
        print(f"Hata: {m3u_file} bulunamadı.")
        return

    with open(m3u_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex: grup, logo, isim ve url bilgilerini yakalar
    pattern = re.compile(r'#EXTINF:.*?(?:group-title="(.*?)")?.*?(?:tvg-logo="(.*?)")?,(.*?)\n(http.*?)(?:\n|$)', re.MULTILINE)
    matches = pattern.findall(content)

    channels = {}

    for group, logo, name, url in matches:
        clean_name = name.strip()
        # Dosya adı için geçersiz karakterleri temizle
        safe_filename = re.sub(r'[\\/*?:"<>|]', "-", clean_name)
        clean_url = url.strip()
        clean_group = group.strip().upper() if group else "ULUSAL"

        if safe_filename not in channels:
            channels[safe_filename] = {
                "display_name": clean_name,
                "group": clean_group,
                "streams": []
            }
        
        # Mükerrer URL kontrolü
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

    # JSON dosyalarını kaydet
    for safe_name, info in channels.items():
        file_path = os.path.join(output_folder, f"{safe_name}.json")
        output_data = {"streams": info["streams"]}

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
    print(f"İşlem bitti. {len(channels)} adet kanal dosyası 'stream/tv/' klasörüne kaydedildi.")

if __name__ == "__main__":
    process_m3u_to_custom_jsons("liste.m3u", "./stream/tv")
