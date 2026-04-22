import re
import json
import os

def slugify(text):
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

    pattern = re.compile(r'#EXTINF:.*?(?:group-title="(.*?)")?.*?(?:tvg-logo="(.*?)")?,(.*?)\n(http.*?)(?:\n|$)', re.MULTILINE)
    matches = pattern.findall(content)

    channels = {}
    categories = {}

    for group, logo, name, url in matches:
        clean_name = name.strip()
        clean_group = group.strip() if group else "GENEL"
        channel_id = f"ch_{slugify(clean_name)}"
        clean_url = url.strip()
        clean_logo = logo.strip() if logo else "https://via.placeholder.com/300x450?text=" + clean_name

        if channel_id not in channels:
            channels[channel_id] = {"name": clean_name, "group": clean_group, "logo": clean_logo, "streams": []}
        
        if not any(s['url'] == clean_url for s in channels[channel_id]["streams"]):
            channels[channel_id]["streams"].append({
                "name": clean_name, "title": f"{clean_name} | {clean_group}", "url": clean_url,
                "behaviorHints": {"notClickable": False, "bingeGroup": channel_id}
            })

        cat_id = f"cat_{slugify(clean_group)}"
        if cat_id not in categories:
            categories[cat_id] = {"display_name": clean_group, "items": []}
        
        if not any(item['id'] == channel_id for item in categories[cat_id]["items"]):
            categories[cat_id]["items"].append({
                "id": channel_id, "type": "tv", "name": clean_name, "poster": clean_logo, "description": f"{clean_name} Canlı Yayın"
            })

    # --- DOSYALARI YAZ ---
    for cid, info in channels.items():
        with open(f"stream/tv/{cid}.json", 'w', encoding='utf-8') as f:
            json.dump({"streams": info["streams"]}, f, ensure_ascii=False, indent=2)

    for cid, info in channels.items():
        meta_data = {"meta": {"id": cid, "type": "tv", "name": info["name"], "poster": info["logo"], "background": info["logo"], "description": f"{info['name']} Canlı Yayın Akışı"}}
        with open(f"meta/tv/{cid}.json", 'w', encoding='utf-8') as f:
            json.dump(meta_data, f, ensure_ascii=False, indent=2)

    for cat_id, data in categories.items():
        with open(f"catalog/tv/{cat_id}.json", 'w', encoding='utf-8') as f:
            json.dump({"metas": data["items"]}, f, ensure_ascii=False, indent=2)

    # --- MANIFEST.JSON OLUŞTURMA ---
    manifest_path = "manifest.json"
    manifest = {
        "id": "MoOnCrOwN-catalog",
        "version": "0.0.4",
        "name": "MoOnCrOwN-0o0-tv",
        "description": "MoOnCrOwN Canlı TV-Film-Dizi kanalları!",
        "resources": ["catalog", "meta", "stream"],
        "types": ["tv"],
        "idPrefixes": ["ch_"],
        "catalogs": [{"id": cat_id, "type": "tv", "name": f"📺 {data['display_name']}"} for cat_id, data in categories.items()]
    }
    
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    if os.path.exists(manifest_path):
        print(f"BAŞARILI: {manifest_path} dosyası ana dizinde oluşturuldu.")
    else:
        print("HATA: Manifest dosyası oluşturulamadı!")

if __name__ == "__main__":
    process_stremio_addon("liste.m3u")
