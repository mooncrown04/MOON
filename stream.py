import re
import json
import os

def slugify(text):
    """ID'ler için metni temizler."""
    text = text.lower()
    tr_map = str.maketrans("çığöşü ", "cigosu-")
    text = text.translate(tr_map)
    return re.sub(r'[^\w\-]', '', text)

def process_all_stremio_assets(m3u_file):
    # Klasörleri Hazırla
    folders = ["stream/tv", "meta/tv", "catalog/tv"]
    for folder in folders:
        os.makedirs(folder, exist_ok=True)

    if not os.path.exists(m3u_file):
        print(f"Hata: {m3u_file} bulunamadı.")
        return

    with open(m3u_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex: group, logo, isim ve url
    pattern = re.compile(r'#EXTINF:.*?(?:group-title="(.*?)")?.*?(?:tvg-logo="(.*?)")?,(.*?)\n(http.*?)(?:\n|$)', re.MULTILINE)
    matches = pattern.findall(content)

    channels = {}
    categories = {}

    for group, logo, name, url in matches:
        clean_name = name.strip()
        # idPrefixes "ch" dediğin için ID'leri ch_ ile başlatıyoruz
        channel_id = f"ch_{slugify(clean_name)}"
        clean_url = url.strip()
        clean_group = group.strip() if group else "DİĞER"
        clean_logo = logo.strip() if logo else "https://via.placeholder.com/300x450?text=" + clean_name

        # 1. Stream & Meta Verisi
        if channel_id not in channels:
            channels[channel_id] = {
                "name": clean_name,
                "group": clean_group,
                "logo": clean_logo,
                "streams": []
            }
        
        if not any(s['url'] == clean_url for s in channels[channel_id]["streams"]):
            channels[channel_id]["streams"].append({
                "name": clean_name,
                "title": f"{clean_name} | {clean_group}",
                "url": clean_url,
                "behaviorHints": {"notClickable": False, "bingeGroup": channel_id}
            })

        # 2. Catalog Verisi
        group_id = f"cat_{slugify(clean_group)}"
        if group_id not in categories:
            categories[group_id] = {"name": clean_group, "metas": []}
        
        if not any(m['id'] == channel_id for m in categories[group_id]["metas"]):
            categories[group_id]["metas"].append({
                "id": channel_id,
                "type": "tv",
                "name": clean_name,
                "poster": clean_logo,
                "description": f"{clean_name} - {clean_group} Canlı Yayın"
            })

    # --- DOSYALARI YAZ ---

    # 1. stream/tv/ch_id.json
    for cid, info in channels.items():
        with open(f"stream/tv/{cid}.json", 'w', encoding='utf-8') as f:
            json.dump({"streams": info["streams"]}, f, ensure_ascii=False, indent=2)

    # 2. meta/tv/ch_id.json
    for cid, info in channels.items():
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

    # 3. catalog/tv/cat_id.json
    for gid, data in categories.items():
        with open(f"catalog/tv/{gid}.json", 'w', encoding='utf-8') as f:
            json.dump({"metas": data["metas"]}, f, ensure_ascii=False, indent=2)

    # 4. manifest.json (Dinamik Kataloglarla)
    manifest = {
        "id": "MoOnCrOwN-catalog",
        "version": "0.0.4",
        "name": "MoOnCrOwN-0o0-tv",
        "description": "MoOnCrOwN Canlı TV-Film-Dizi kanalları!",
        "resources": ["catalog", "meta", "stream"],
        "types": ["tv"],
        "idPrefixes": ["ch_"],
        "catalogs": [
            {"id": gid, "type": "tv", "name": f"📺 {data['name']}"} 
            for gid, data in categories.items()
        ]
    }
    with open("manifest.json", 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"Bitti! Manifest güncellendi, {len(categories)} kategori oluşturuldu.")

if __name__ == "__main__":
    process_all_stremio_assets("liste.m3u")
