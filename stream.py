import re
import json
import os

def slugify(text):
    """ID ve Dosya adları için metni temizler (Örn: 'TRT 1' -> 'trt1')"""
    text = text.lower()
    text = text.replace("ı", "i").replace("ğ", "g").replace("ü", "u").replace("ş", "s").replace("ö", "o").replace("ç", "c")
    text = re.sub(r'\s+', '', text)
    return re.sub(r'[^\w]', '', text)

def process_m3u_to_stremio_format(m3u_file):
    # Klasör yolları
    folders = ["stream/tv", "meta/tv", "catalog/tv"]
    for folder in folders:
        os.makedirs(folder, exist_ok=True)

    if not os.path.exists(m3u_file):
        print(f"Hata: {m3u_file} bulunamadı.")
        return

    with open(m3u_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex: grup, logo, isim ve url bilgilerini yakalar
    pattern = re.compile(r'#EXTINF:.*?(?:group-title="(.*?)")?.*?(?:tvg-logo="(.*?)")?,(.*?)\n(http.*?)(?:\n|$)', re.MULTILINE)
    matches = pattern.findall(content)

    channels = {}
    categories = {}

    for group, logo, name, url in matches:
        clean_name = name.strip()
        channel_id = f"tv_{slugify(clean_name)}"
        clean_url = url.strip()
        clean_group = group.strip() if group else "GENEL"
        clean_logo = logo.strip() if logo else "https://via.placeholder.com/300x450?text=" + clean_name

        # --- KANAL VERİSİNİ GRUPLA ---
        if channel_id not in channels:
            channels[channel_id] = {
                "name": clean_name,
                "group": clean_group,
                "logo": clean_logo,
                "streams": []
            }
        
        # Mükerrer URL engelleme ve yayın ekleme
        if not any(s['url'] == clean_url for s in channels[channel_id]["streams"]):
            channels[channel_id]["streams"].append({
                "name": clean_name,
                "title": f"{clean_name} | {clean_group}",
                "url": clean_url,
                "behaviorHints": {
                    "notClickable": False,
                    "bingeGroup": channel_id
                }
            })

        # --- KATALOG VERİSİNİ GRUPLA (Kategorilere Göre) ---
        if clean_group not in categories:
            categories[clean_group] = []
        
        # Katalog listesine ekle (zaten eklenmemişse)
        if not any(m['id'] == channel_id for m in categories[clean_group]):
            categories[clean_group].append({
                "id": channel_id,
                "type": "tv",
                "name": clean_name,
                "poster": clean_logo,
                "description": f"{clean_name} Canlı Yayın"
            })

    # --- 1. STREAM DOSYALARINI YAZ (stream/tv/id.json) ---
    for cid, info in channels.items():
        with open(f"stream/tv/{cid}.json", 'w', encoding='utf-8') as f:
            json.dump({"streams": info["streams"]}, f, ensure_ascii=False, indent=2)

    # --- 2. META DOSYALARINI YAZ (meta/tv/id.json) ---
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

    # --- 3. CATALOG DOSYALARINI YAZ (catalog/tv/Kategori_Ismi.json) ---
    for cat_name, metas in categories.items():
        safe_cat_name = slugify(cat_name)
        with open(f"catalog/tv/{safe_cat_name}.json", 'w', encoding='utf-8') as f:
            json.dump({"metas": metas}, f, ensure_ascii=False, indent=2)

    print(f"İşlem Başarılı!")
    print(f"Oluşturulan: {len(channels)} Kanal, {len(categories)} Kategori.")

if __name__ == "__main__":
    process_m3u_to_stremio_format("liste.m3u")
