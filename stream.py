import re
import json
import os

def slugify(text):
    """Metni temizleyip ID formatına getirir (Örn: 'Spor Dünyası' -> 'spor-dunyasi')"""
    text = text.lower()
    tr_map = str.maketrans("çığöşü ", "cigosu-")
    text = text.translate(tr_map)
    text = re.sub(r'[^\w\-]', '', text)
    return text.strip("-")

def process_stremio_addon(m3u_file):
    # Gerekli Klasörleri Oluştur
    folders = ["stream/tv", "meta/tv", "catalog/tv"]
    for folder in folders:
        os.makedirs(folder, exist_ok=True)

    if not os.path.exists(m3u_file):
        print(f"Hata: {m3u_file} bulunamadı!")
        return

    with open(m3u_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex: M3U'dan Group, Logo, İsim ve URL çekme
    pattern = re.compile(r'#EXTINF:.*?(?:group-title="(.*?)")?.*?(?:tvg-logo="(.*?)")?,(.*?)\n(http.*?)(?:\n|$)', re.MULTILINE)
    matches = pattern.findall(content)

    channels = {}
    categories = {} # Kategori isimlerini ve içindeki kanalları tutacak

    for group, logo, name, url in matches:
        clean_name = name.strip()
        clean_group = group.strip() if group else "GENEL"
        # Senin idPrefixes "ch" olduğu için ID'ler ch_ ile başlıyor
        channel_id = f"ch_{slugify(clean_name)}"
        clean_url = url.strip()
        clean_logo = logo.strip() if logo else "https://via.placeholder.com/300x450?text=" + clean_name

        # 1. Kanal Bilgilerini ve Streamleri Topla
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

        # 2. Katalogları ve Metaları Grupla
        cat_id = f"cat_{slugify(clean_group)}"
        if cat_id not in categories:
            categories[cat_id] = {"display_name": clean_group, "items": []}
        
        if not any(item['id'] == channel_id for item in categories[cat_id]["items"]):
            categories[cat_id]["items"].append({
                "id": channel_id,
                "type": "tv",
                "name": clean_name,
                "poster": clean_logo,
                "description": f"{clean_name} Canlı Yayın"
            })

    # --- DOSYA YAZIM İŞLEMLERİ ---

    # 1. Stream Dosyaları (stream/tv/ch_...json)
    for cid, info in channels.items():
        with open(f"stream/tv/{cid}.json", 'w', encoding='utf-8') as f:
            json.dump({"streams": info["streams"]}, f, ensure_ascii=False, indent=2)

    # 2. Meta Dosyaları (meta/tv/ch_...json)
    for cid, info in channels.items():
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

    # 3. Katalog Dosyaları (catalog/tv/cat_...json)
    for cat_id, data in categories.items():
        with open(f"catalog/tv/{cat_id}.json", 'w', encoding='utf-8') as f:
            json.dump({"metas": data["items"]}, f, ensure_ascii=False, indent=2)

    # 4. Manifest.json (M3U'ya göre otomatik oluşturulan kataloglarla)
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
                "id": cat_id, 
                "type": "tv", 
                "name": f"📺 {data['display_name']}"
            } for cat_id, data in categories.items()
        ]
    }
    with open("manifest.json", 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"İşlem tamam! {len(channels)} kanal ve {len(categories)} kategori için tüm dosyalar oluşturuldu.")

if __name__ == "__main__":
    process_stremio_addon("liste.m3u")
