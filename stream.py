import re
import json
import os
import shutil

def slugify(text):
    """ID ve Dosya adları için metni temizler."""
    if not text: return "diger"
    text = text.lower()
    tr_map = str.maketrans("çığöşü ", "cigosu-")
    text = text.translate(tr_map).replace(" ", "-")
    text = re.sub(r'[^\w\-]', '', text)
    return text.strip("-")

def process_stremio_addon(m3u_file):
    # --- KRİTİK: FAZLA DOSYALARI SİLME ---
    # Her çalıştığında klasörleri silip baştan oluşturur, böylece m3u'da olmayanlar silinmiş olur.
    folders = ["stream/tv", "meta/tv", "catalog/tv"]
    for folder_path in ["stream", "meta", "catalog"]:
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
    
    for folder in folders:
        os.makedirs(folder, exist_ok=True)

    if not os.path.exists(m3u_file):
        print(f"Hata: {m3u_file} dosyası bulunamadı!")
        return

    channels = {}
    categories = {}

    with open(m3u_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    current_info = None
    for line in lines:
        line = line.strip()
        
        if line.startswith("#EXTINF:"):
            group_match = re.search(r'group-title="([^"]+)"', line)
            logo_match = re.search(r'tvg-logo="([^"]+)"', line)
            name_parts = line.split(",")
            name = name_parts[-1].strip() if len(name_parts) > 1 else "Bilinmeyen Kanal"
            
            current_info = {
                "group": group_match.group(1) if group_match else "DİĞER",
                "logo": logo_match.group(1) if logo_match else "https://via.placeholder.com/300",
                "name": name
            }
        
        elif line.startswith("http") and current_info:
            url = line
            chan_id = f"ch_{slugify(current_info['name'])}"
            cat_id = f"cat_{slugify(current_info['group'])}"
            
            # 1. Kanalları Kaydet (Stream & Meta)
            if chan_id not in channels:
                channels[chan_id] = {
                    "name": current_info['name'],
                    "group": current_info['group'],
                    "logo": current_info['logo'],
                    "streams": []
                }
            
            # --- DÜZELTME: STREAM TITLE (Kanal Adı | Kategori Adı) ---
            channels[chan_id]["streams"].append({
                "name": current_info['name'],
                "title": f"{current_info['name']} | {current_info['group']}",
                "url": url,
                "behaviorHints": {
                    "notClickable": False,
                    "bingeGroup": chan_id
                }
            })

            # 2. Katalogları Kaydet
            if cat_id not in categories:
                categories[cat_id] = {
                    "display_name": current_info['group'],
                    "metas": []
                }
            
            if not any(m['id'] == chan_id for m in categories[cat_id]["metas"]):
                categories[cat_id]["metas"].append({
                    "id": chan_id,
                    "type": "tv",
                    "name": current_info['name'],
                    "poster": current_info['logo'],
                    "description": f"{current_info['group']} kategorisinde yayın."
                })
            current_info = None

    # --- DOSYALARI OLUŞTUR ---

    # stream ve meta dosyaları
    for cid, info in channels.items():
        with open(f"stream/tv/{cid}.json", 'w', encoding='utf-8') as f:
            json.dump({"streams": info["streams"]}, f, ensure_ascii=False, indent=2)
        
        meta = {
            "meta": {
                "id": cid, 
                "type": "tv", 
                "name": info["name"], 
                "poster": info["logo"], 
                "background": info["logo"], 
                "description": info["name"]
            }
        }
        with open(f"meta/tv/{cid}.json", 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

    # catalog dosyaları
    for cat_id, data in categories.items():
        with open(f"catalog/tv/{cat_id}.json", 'w', encoding='utf-8') as f:
            json.dump({"metas": data["metas"]}, f, ensure_ascii=False, indent=2)

    # manifest.json
    manifest = {
        "id": "MoOnCrOwN-KATALOG",
        "version": "1.0.0",
        "name": "MoOnCrOwN-TV",
        "description": "MoOnCrOwN Canlı Yayınlar",
        "resources": ["catalog", "meta", "stream"],
        "types": ["tv"],
        "idPrefixes": ["ch","iptv_"],
        "catalogs": [
            {
                "id": k,
                "type": "tv", 
                "name": f"📺 {v['display_name']}"
            } for k, v in categories.items()
        ]
    }
    
    with open("manifest.json", 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"Bitti! {len(channels)} kanal ve {len(categories)} kategori işlendi. Artık dosyalar temizlendi.")

if __name__ == "__main__":
    process_stremio_addon("liste.m3u")
