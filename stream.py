import re
import json
import os
import shutil

def slugify(text):
    if not text: return "diger"
    text = text.lower()
    tr_map = str.maketrans("çığöşü ", "cigosu-")
    text = text.translate(tr_map).replace(" ", "-")
    text = re.sub(r'[^\w\-]', '', text)
    return text.strip("-")

def process_stremio_addon(m3u_file):
    # Temiz bir başlangıç için eski klasörleri siliyoruz
    for folder in ["stream", "meta", "catalog"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            
    folders = ["stream/tv", "meta/tv", "catalog/tv"]
    for folder in folders: os.makedirs(folder, exist_ok=True)

    if not os.path.exists(m3u_file):
        print(f"Hata: {m3u_file} bulunamadı!")
        return

    channels = {}
    categories = {}

    with open(m3u_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # M3U ayrıştırma (Regex)
    pattern = re.compile(r'#EXTINF:.*?(?:group-title="(?P<group>.*?)")?.*?(?:tvg-logo="(?P<logo>.*?)")?,(?P<name>.*?)\n(?P<url>http.*?)(?:\n|$)', re.MULTILINE)
    
    for match in pattern.finditer(content):
        group_name = match.group('group').strip() if match.group('group') else "DİĞER"
        logo = match.group('logo').strip() if match.group('logo') else "https://via.placeholder.com/300"
        name = match.group('name').strip()
        url = match.group('url').strip()

        chan_id = f"ch_{slugify(name)}"
        cat_id = f"cat_{slugify(group_name)}"

        # 1. STREAM VERİSİ (İstediğin Format: Kanal İsmi | Kategori)
        if chan_id not in channels:
            channels[chan_id] = {
                "name": name,
                "group": group_name,
                "logo": logo,
                "streams": []
            }
        
        channels[chan_id]["streams"].append({
            "name": name,
            "title": f"{name} | {group_name}", # BURASI DÜZELTİLDİ
            "url": url,
            "behaviorHints": {
                "notClickable": False,
                "bingeGroup": chan_id
            }
        })

        # 2. KATALOG VERİSİ
        if cat_id not in categories:
            categories[cat_id] = {"display_name": group_name, "metas": []}
        
        if not any(m['id'] == chan_id for m in categories[cat_id]["metas"]):
            categories[cat_id]["metas"].append({
                "id": chan_id,
                "type": "tv",
                "name": name,
                "poster": logo,
                "description": f"{group_name} kategorisinde canlı yayın."
            })

    # DOSYALARI YAZ
    for cid, info in channels.items():
        with open(f"stream/tv/{cid}.json", 'w', encoding='utf-8') as f:
            json.dump({"streams": info["streams"]}, f, ensure_ascii=False, indent=2)
        
        meta = {"meta": {"id": cid, "type": "tv", "name": info["name"], "poster": info["logo"], "background": info["logo"], "description": info["name"]}}
        with open(f"meta/tv/{cid}.json", 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

    for cat_id, data in categories.items():
        with open(f"catalog/tv/{cat_id}.json", 'w', encoding='utf-8') as f:
            json.dump({"metas": data["metas"]}, f, ensure_ascii=False, indent=2)

    # MANIFEST (Otomatik Kataloglar)
    manifest = {
        "id": "MoOnCrOwN-catalog",
        "version": "1.0.0",
        "name": "MoOnCrOwN-0o0-tv",
        "description": "MoOnCrOwN Canlı TV Kanalları",
        "resources": ["catalog", "meta", "stream"],
        "types": ["tv"],
        "idPrefixes": ["ch_"],
        "catalogs": [{"id": k, "type": "tv", "name": f"📺 {v['display_name']}"} for k, v in categories.items()]
    }
    with open("manifest.json", 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print("İşlem Başarılı: Eski dosyalar temizlendi ve yeni yapı kuruldu.")

if __name__ == "__main__":
    process_stremio_addon("liste.m3u")
