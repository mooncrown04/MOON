import re
import json
import os

def process_m3u_to_single_list(m3u_file, output_path):
    # Klasör kontrolü
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # M3U dosyasını oku
    if not os.path.exists(m3u_file):
        print(f"Hata: {m3u_file} bulunamadı.")
        return

    with open(m3u_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Mevcut JSON'u yükle veya boş başlat
    if os.path.exists(output_path):
        with open(output_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except:
                data = {"streams": []}
    else:
        data = {"streams": []}

    # Regex: Kanal adı ve URL'yi yakalar
    pattern = re.compile(r'#EXTINF:.*?,(.*?)\n(http.*?)(?:\n|$)', re.MULTILINE)
    matches = pattern.findall(content)

    for name, url in matches:
        clean_name = name.strip()
        clean_url = url.strip()

        # Link zaten listede var mı kontrolü
        is_url_exists = any(clean_url == s.get("url") for s in data["streams"] if s["name"] == clean_name)
        
        if not is_url_exists:
            # Kanalın ilk linki mi yoksa alternatif mi olduğunu anla
            is_first = not any(s["name"] == clean_name for s in data["streams"])
            suffix = "ULUSAL" if is_first else "ALTERNATİF"
            
            new_entry = {
                "name": clean_name,
                "title": f"{clean_name} | {suffix}",
                "url": clean_url,
                "behaviorHints": {
                    "notClickable": False,
                    "bingeGroup": clean_name.lower().replace(" ", "-")
                }
            }
            data["streams"].append(new_entry)

    # JSON Olarak Kaydet
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Başarılı: {len(matches)} link işlendi.")

# GitHub Action için doğru yol ve dosya isimleri
if __name__ == "__main__":
    process_m3u_to_single_list("liste.m3u", "./tv/streams.json")
