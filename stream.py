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

    # GELİŞMİŞ REGEX: Etiketlerin sırasından bağımsız olarak group-title, logo ve kanal ismini çeker
    # Bu patern hem tırnaklı hem tırnaksız yapıları ve farklı sıralamaları yakalar
    pattern = re.compile(r'#EXTINF:-1.*?(?:group-title="(?P<group>.*?)")?.*?(?:tvg-logo="(?P<logo>.*?)")?,(?P<name>.*?)\n(?P<url>http.*?)(?:\n|$)', re.MULTILINE | re.DOTALL)
    
    matches = pattern.finditer(content)

    channels = {}
    categories = {}

    for match in matches:
        group_val = match.group('group')
        logo_val = match.group('logo')
        name_val = match.group('name')
        url_val = match.group('url')

        clean_name = name_val.strip()
        group_name = group_val.strip() if group_val else "DİĞER"
        
        # ID Oluşturma
        channel_id = f"ch_{slugify(clean_name)}"
        cat_id = f"cat_{slugify(group_name)}"
        
        clean_url = url_val.strip()
        clean_logo = logo_val.strip() if logo_val else "https://via.placeholder.com/300x450?text=" + clean_name

        # 1. Kanalları ve Yayın Linklerini Kaydet
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

        # 2. Kategorileri (Catalog) Eşleştir
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

    # --- DOSYA YAZMA ---

    # A. Stream ve Meta
    for cid, info in channels.items():
        # Stream JSON
        with open(f"stream/tv/{cid}.json", 'w', encoding='utf-8') as f:
            json.dump({"streams": info["streams"]}, f, ensure_ascii=False, indent=2)
        
        # Meta JSON
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

    # B. Catalog JSON'ları
    for cat_id, data in categories.items():
        with open(f"catalog/tv/{cat_id}.json", 'w', encoding='utf-8') as f:
            json.dump({"metas": data["metas"]}, f, ensure_ascii=False, indent=2)

    # C. MANIFEST.JSON (Tam Dinamik)
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

    print(f"İşlem bitti: {len(channels)} kanal ve {len(categories)} kategori (manifest dahil) oluşturuldu.")

if __name__ == "__main__":
    process_stremio_addon("liste.m3u")
