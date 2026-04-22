import re
import json
import os

def slugify(text):
    """Metni temizleyip standart bir ID formatına getirir."""
    if not text:
        return "genel"
    text = text.lower()
    tr_map = str.maketrans("çığöşü ", "cigosu-")
    text = text.translate(tr_map)
    text = re.sub(r'[^\w\-]', '', text)
    return text.strip("-")

def process_stremio_addon(m3u_file):
    # Klasörleri Hazırla
    folders = ["stream/tv", "meta/tv", "catalog/tv"]
    for folder in folders:
        os.makedirs(folder, exist_ok=True)

    if not os.path.exists(m3u_file):
        print(f"Hata: {m3u_file} bulunamadı!")
        return

    with open(m3u_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex: Group-title, Logo, Kanal Adı ve URL çekme
    pattern = re.compile(r'#EXTINF:.*?(?:group-title="(.*?)")?.*?(?:tvg-logo="(.*?)")?,(.*?)\n(http.*?)(?:\n|$)', re.MULTILINE)
    matches = pattern.findall(content)

    channels = {}
    categories = {}

    for group_title, logo, name, url in matches:
        clean_name = name.strip()
        group_name = group_title.strip() if group_title else "GENEL"
        
        # ID Oluşturma
        channel_id = f"ch_{slugify(clean_name)}"
        cat_id = f"cat_{slugify(group_name)}"
        
        clean_url = url.strip()
        clean_logo = logo.strip() if logo else "https://via.placeholder.com/300x450?text=" + clean_name

        # 1. Kanalları ve Yayın Linklerini Eşleştir
        if channel_id not in channels:
            channels[channel_id] = {
                "name": clean_name,
                "group": group_name,
                "logo": clean_logo,
                "streams": []
            }
        
        if not any(s['url'] == clean_url for s in channels[channel_id]["streams"]):
            channels[channel_id]["streams"].append({
                "name": clean_name,
                "title": f"{clean_name} | {group_name}",
                "url": clean_url,
                "behaviorHints": {"notClickable": False, "bingeGroup": channel_id}
            })

        # 2. Kategorileri (Catalogs) ve İçeriklerini Eşleştir
        if cat_id not in categories:
            categories[cat_id] = {"display_name": group_name, "metas": []}
        
        if not any(m['id'] == channel_id for m in categories[cat_id]["metas"]):
            categories[cat_id]["metas"].append({
                "id": channel_id,
                "type": "tv",
                "name": clean_name,
                "poster": clean_logo,
                "description": f"{clean_name} - {group_name} Canlı Yayın"
            })

    # --- DOSYA YAZIM AŞAMASI ---

    # A. Stream ve Meta Dosyaları
    for cid, info in channels.items():
        # Stream
        with open(f"stream/tv/{cid}.json", 'w', encoding='utf-8') as f:
            json.dump({"streams": info["streams"]}, f, ensure_ascii=False, indent=2)
        # Meta
        meta_data = {
            "meta": {
                "id": cid,
                "type": "tv",
                "name": info["name"],
                "poster": info["logo"],
                "background": info["logo"],
                "description": f"{info['name']} Canlı Yayın Akışı"
            }
        }
        with open(f"meta/tv/{cid}.json", 'w', encoding='utf-8') as f:
            json.dump(meta_data, f, ensure_ascii=False, indent=2)

    # B. Catalog Dosyaları (Kategori bazlı liste)
    for cat_id, data in categories.items():
        with open(f"catalog/tv/{cat_id}.json", 'w', encoding='utf-8') as f:
            json.dump({"metas": data["metas"]}, f, ensure_ascii=False, indent=2)

    # C. Manifest.json (Dinamik Katalog Listesi)
    manifest = {
        "id": "MoOnCrOwN-catalog",
        "version": "0.0.4",
        "name": "MoOnCrOwN-0o0-tv",
        "description": "MoOnCrOwN Canlı TV-Film-Dizi kanalları!",
        "resources": ["catalog", "meta", "stream"],
        "types": ["tv"],
        "idPrefixes": ["ch_"],
        "catalogs": [
            {
                "id": cid, 
                "type": "tv", 
                "name": f"📺 {cdata['display_name']}"
            } for cid, cdata in categories.items()
        ]
    }
    
    with open("manifest.json", 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"İşlem bitti: {len(channels)} kanal, {len(categories)} kategori oluşturuldu.")

if __name__ == "__main__":
    process_stremio_addon("liste.m3u")
