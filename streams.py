import re
import json
import os

def m3u_to_json_converter(m3u_file_path, output_json_path):
    streams = []
    
    # 1. M3U dosyasını oku
    if not os.path.exists(m3u_file_path):
        print(f"Hata: {m3u_file_path} bulunamadı.")
        return

    with open(m3u_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 2. Regex ile Kanal Adı ve Linkleri eşleştir
    # #EXTINF:-1 ... ,Kanal Adı
    # http://...
    pattern = re.compile(r'#EXTINF:.*?,(.*?)\n(http.*?)(?:\n|$)', re.MULTILINE)
    matches = pattern.findall(content)

    for name, url in matches:
        stream_obj = {
            "name": name.strip(),
            "title": f"{name.strip()} |ULUSAL",
            "url": url.strip(),
            "behaviorHints": {
                "notClickable": False,
                "bingeGroup": name.strip().lower().replace(" ", "-")
            }
        }
        streams.append(stream_obj)

    # 3. Mevcut JSON dosyasını kontrol et ve ekleme yap
    if os.path.exists(output_json_path):
        with open(output_json_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                if "streams" in data:
                    data["streams"].extend(streams)
                else:
                    data["streams"] = streams
            except json.JSONDecodeError:
                data = {"streams": streams}
    else:
        data = {"streams": streams}

    # 4. Sonucu kaydet
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"İşlem tamamlandı. {len(streams)} kanal '{output_json_path}' dosyasına eklendi.")

# Kullanım:
# m3u_to_json_converter("kanallar.m3u", "streams.json")
