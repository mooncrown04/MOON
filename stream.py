import re
import json
import os

def slugify(text):
    """ID ve Dosya adları için metni temizler."""
    if not text: return "diger"
    text = text.lower()
    tr_map = str.maketrans("çığöşü ", "cigosu-")
    text = text.translate(tr_map).replace(" ", "-")
    text = re.sub(r'[^\w\-]', '', text)
    return text.strip("-")

def process_stremio_addon(m3u_file):
    # Klasörleri temizle/hazırla
    folders = ["stream/tv", "meta/tv", "catalog/tv"]
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
            # M3U içindeki group-title, logo ve kanal ismini alıyoruz
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
            cat_id = f"cat_{slugify(current_info['group'])}" # Dosya ismi ve ID burası
            
            # 1. Kanalları Kaydet (Stream & Meta)
            if chan_id not in channels:
                channels[chan_id] = {
                    "name": current_info['name'],
                    "group": current_info['group'],
                    "logo": current_info['logo'],
                    "streams": []
                }
            
            channels[chan_id]["streams"].append({
                "title": f"{current_info['name']} - Yayın Kaynağı",
                "url": url
            })

            # 2. Katalogları Kaydet (Manifest ve Klasör uyumu için)
            if cat_id not in categories:
                categories[cat_id] = {
                    "display_name": current_info['group'], # Görünecek isim: "Haberler"
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

    # stream/tv/*.json ve meta/tv/*.json
    for cid, info in channels.items():
        with open(f"stream/tv/{cid}.json", 'w', encoding='utf-8') as f:
            json.dump({"streams": info["streams"]}, f, ensure_ascii=False, indent=2)
        
        meta = {"meta": {"id": cid, "type": "tv", "name": info["name"], "poster": info["logo"], "background": info["logo"], "description": info["name"]}}
        with open(f"meta/tv/{cid}.json", 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

    # catalog/tv/*.json (Dosya adı cat_id ile tam uyumlu)
    for cat_id, data in categories.items():
        with open(f"catalog/tv/{cat_id}.json", 'w', encoding='utf-8') as f:
            json.dump({"metas": data["metas"]}, f, ensure_ascii=False, indent=2)

    # manifest.json (Katalog ID'leri dosya isimleriyle aynı)
    manifest = {
        "id": "MoOnCrOwN-catalog",
        "version": "1.0.0",
        "name": "MoOnCrOwN-0o0-tv",
        "description": "MoOnCrOwN Canlı Yayınlar",
        "resources": ["catalog", "meta", "stream"],
        "types": ["tv"],
        "idPrefixes": ["ch_"],
        "catalogs": [
            {
                "id": k, # cat_haberler gibi
                "type": "tv", 
                "name": f"📺 {v['display_name']}" # "Haberler" gibi
            } for k, v in categories.items()
        ]
    }
    
    with open("manifest.json", 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"Bitti! {len(categories)} adet katalog ve manifest başarıyla güncellendi.")

if __name__ == "__main__":
    process_stremio_addon("liste.m3u")
