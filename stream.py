import re
import json
import os

def slugify(text):
    """Metni temizleyip ID formatına getirir (Örn: 'Ulusal Kanallar' -> 'ulusal-kanallar')"""
    if not text:
        return "diger"
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

    # GELİŞMİŞ REGEX: group-title, tvg-logo ve kanal ismini yakalar.
    # Group title yoksa "DİĞER" varsayılanını atar.
    pattern = re.compile(r'#EXTINF:.*?(?:group-title="(?P<group>.*?)")?.*?(?:tvg-logo="(?P<logo>.*?)")?,(?P<name>.*?)\n(?P<url>http.*?)(?:\n|$)', re.MULTILINE)
    
    matches = pattern.finditer(content)

    channels = {}
    categories = {}

    for match in matches:
        # Verileri çek
        group_val = match.group('group')
        logo_val = match.group('logo')
        name_val = match.group('name')
        url_val = match.group('url')

        if not name_val or not url_val:
            continue

        clean_name = name_val.strip()
        group_name = group_val.strip() if group_val else "DİĞER"
        
        # ID'leri Oluştur
        channel_id = f"ch_{slugify(clean_name)}"
        cat_id = f"cat_{slugify(group_name)}"
        
        clean_url = url_val.strip()
        clean_logo = logo_val.strip() if logo_val else "https://picon.pics/TR/Ulusal/Trt1.png"

        # 1. Kanal ve Yayın Bilgilerini Sakla
        if channel_id not in channels:
            channels[channel_id] = {
                "name": clean_name,
                "group": group_name,
                "logo": clean_logo,
                "streams": []
            }
        
        # Aynı kanala birden fazla link varsa ekle
        if not any(s['url'] == clean_url for s in channels[channel_id]["streams"]):
            channels[channel_id]["streams"].append({
                "name": f"{clean_name} (Kaynak {len(channels[channel_id]['streams']) + 1})",
                "title": f"{clean_name} | {group_name}",
                "url": clean_url
            })

        # 2. Kategoriyi ve Katalog İçeriğini Sakla
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

    # --- DOSYA YAZIM İŞLEMLERİ ---

    # A. Kanalların Stream ve Meta Dosyaları
    for cid, info in channels.items():
        with open(f"stream/tv/{cid}.json", 'w', encoding='utf-8') as f:
            json.dump({"streams": info["streams"]}, f, ensure_ascii=False, indent=2)
        
        meta_obj = {
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
            json.dump(meta_obj, f, ensure_ascii=False, indent=2)

    # B. Katalog Listeleri (Kategori Bazlı)
    for cat_id, data in categories.items():
        with open(f"catalog/tv/{cat_id}.json", 'w', encoding='utf-8') as f:
            json.dump({"metas": data["metas"]}, f, ensure_ascii=False, indent=2)

    # C. MANIFEST.JSON (Dinamik Kataloglarla)
    manifest = {
        "id": "MoOnCrOwN-catalog",
        "version": "1.0.0",
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

    print(f"Başarılı! {len(channels)} kanal ve {len(categories)} kategori işlendi.")

if __name__ == "__main__":
    process_stremio_addon("liste.m3u")
