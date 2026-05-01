import re
import json
import os
import shutil
import requests

# --- AYARLAR ---
# 1. Bu kelimeler M3U KATEGORİ (group-title) adında geçerse kendi adıyla kategori olur:
OZEL_KATEGORILER = ["FREESHOT"]

# 2. Bu kelimeler KANAL İSMİNDE geçerse "SEÇİLİ" kategorisinde toplanır:
SECILI_KANAL_FILTRESI = ["123", "124", "125"]

def slugify(text):
    if not text: return "DIGER"
    tr_map = str.maketrans("çığöşüÇİĞÖŞÜ", "cigosucigosu")
    text = text.translate(tr_map).upper().replace("-", " ")
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text.replace(" ", "_")

def process_stremio_addon():
    m3u_url = "https://raw.githubusercontent.com/mooncrown04/m3ubirlestir/refs/heads/main/birlesik_tv.m3u"
    print(f"Liste indiriliyor: {m3u_url}")
    try:
        res = requests.get(m3u_url, timeout=15)
        res.raise_for_status()
        m3u_content = res.text
    except Exception as e:
        print(f"Hata: {e}")
        return

    for folder in ["stream", "meta", "catalog"]:
        if os.path.exists(folder): shutil.rmtree(folder)
        os.makedirs(f"{folder}/tv", exist_ok=True)

    channels = {}
    categories = {}

    lines = m3u_content.splitlines()
    current_info = None

    for line in lines:
        line = line.strip()
        if line.startswith("#EXTINF:"):
            group_match = re.search(r'group-title="([^"]+)"', line)
            logo_match = re.search(r'tvg-logo="([^"]+)"', line)
            name = line.split(",")[-1].strip().replace("-", " ").upper()
            raw_group = group_match.group(1).upper() if group_match else "DIGER"
            
            assigned_group = raw_group
            is_found = False

            # İŞLEM 1: Kategori Bazlı Arama (Kendi adıyla kategori açar)
            for cat_word in OZEL_KATEGORILER:
                if cat_word in raw_group:
                    assigned_group = cat_word
                    is_found = True
                    break
            
            # İŞLEM 2: Kanal İsmi Bazlı Arama (Eğer kategori bulunamadıysa SEÇİLİ'ye atar)
            if not is_found:
                for name_word in SECILI_KANAL_FILTRESI:
                    if name_word in name:
                        assigned_group = "SECILI"
                        is_found = True
                        break

            current_info = {
                "group": assigned_group,
                "logo": logo_match.group(1) if logo_match else "https://via.placeholder.com/300",
                "name": name
            }
        
        elif line.startswith("http") and current_info:
            chan_id = f"CH_{slugify(current_info['name'])}"
            cat_id = f"CAT_{slugify(current_info['group'])}"
            
            # Kanal Birleştirme (Aynı isimli kanalları tek kartta toplar)
            if chan_id not in channels:
                channels[chan_id] = {
                    "name": current_info['name'],
                    "logo": current_info['logo'],
                    "streams": []
                }
                
                if cat_id not in categories:
                    d_name = "⭐ SEÇİLİ KANALLAR" if current_info['group'] == "SECILI" else f"📂 {current_info['group']}"
                    categories[cat_id] = {"display_name": d_name, "metas": []}
                
                categories[cat_id]["metas"].append({
                    "id": chan_id, "type": "tv", "name": current_info['name'], "poster": current_info['logo']
                })

            # Yayınları (Stream) Ekle
            s_idx = len(channels[chan_id]["streams"]) + 1
            channels[chan_id]["streams"].append({
                "name": f"Kaynak {s_idx}",
                "title": f"{current_info['name']} | Kaynak {s_idx}\n({current_info['group']})",
                "url": line
            })
            current_info = None

    # Dosya Kayıtları
    for cid, info in channels.items():
        with open(f"stream/tv/{cid}.json", 'w', encoding='utf-8') as f:
            json.dump({"streams": info["streams"]}, f, ensure_ascii=False)
        with open(f"meta/tv/{cid}.json", 'w', encoding='utf-8') as f:
            json.dump({"meta": {"id": cid, "type": "tv", "name": info["name"], "poster": info["logo"]}}, f, ensure_ascii=False)

    for cat_id, data in categories.items():
        with open(f"catalog/tv/{cat_id}.json", 'w', encoding='utf-8') as f:
            json.dump({"metas": data["metas"]}, f, ensure_ascii=False)

    manifest = {
        "id": "MOONCROWN_V3",
        "version": "3.1.0",
        "name": "MOONCROWN TV",
        "resources": ["catalog", "meta", "stream"],
        "types": ["tv"],
        "idPrefixes": ["CH_"],
        "catalogs": [{"id": k, "type": "tv", "name": v['display_name']} for k, v in categories.items()]
    }
    with open("manifest.json", 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"Tamamlandı! {len(channels)} benzersiz kanal hazır.")

if __name__ == "__main__":
    process_stremio_addon()
