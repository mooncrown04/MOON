import re
import json
import os
import shutil
import requests

def slugify(text):
    """ID ve Dosya adları için metni temizler, büyük harf yapar ve alt tire kullanır."""
    if not text: return "DIGER"
    # Türkçe karakter dönüşümü
    tr_map = str.maketrans("çığöşüÇİĞÖŞÜ", "cigosucigosu")
    text = text.translate(tr_map)
    # Büyük harfe çevir
    text = text.upper()
    # Boşlukları ve tireleri alt tireye çevir
    text = text.replace(" ", "_").replace("-", "_")
    # Alfanümerik ve alt tire dışındakileri temizle
    text = re.sub(r'[^\w]', '', text)
    # Çift alt tire oluşursa teke indir ve kenarları temizle
    text = re.sub(r'_+', '_', text)
    return text.strip("_")

def process_stremio_addon():
    # --- 1. LİSTEYİ İNDİR ---
    m3u_url = "https://raw.githubusercontent.com/mooncrown04/m3ubirlestir/refs/heads/main/birlesik_tv.m3u"
    print(f"Liste indiriliyor: {m3u_url}")
    try:
        res = requests.get(m3u_url, timeout=15)
        res.raise_for_status()
        m3u_content = res.text
    except Exception as e:
        print(f"İndirme hatası: {e}")
        return

    # --- 2. TEMİZLİK VE KLASÖR HAZIRLIĞI ---
    folders = ["stream/tv", "meta/tv", "catalog/tv"]
    for folder_path in ["stream", "meta", "catalog"]:
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
    
    for folder in folders:
        os.makedirs(folder, exist_ok=True)

    # --- 3. KATEGORİ VE KANAL AYARLARI ---
    channels = {}
    categories = {}
    channel_count = 0 

    # Kategori eşleşmeleri (Key'ler slugify formatında olmalı)
    category_map = {
        "ULUSAL": "📺 Ulusal Kanallar",
        "SPOR": "⚽ Spor Dünyası",
        "HABERLER": "📰 Haber",
        "SINEMA": "🎬 Sinema & Dizi",
        "DIZI": "🎬 Sinema & Dizi",
        "FILM": "🎞️ FİLM",
        "BELGESEL": "🦒 Belgesel & Yaşam",
        "MUZIK": "🎵 Müzik",
        "ANIMASYON": "🎨 Animasyon",
        "COCUK": "🧸 Çocuk",
        "YETISKIN": "🔞 Yetişkin",
        "DIGER": "📡 Diğer Kanallar"
    }

    lines = m3u_content.splitlines()
    current_info = None

    for line in lines:
        if channel_count >= 100:
            break

        line = line.strip()
        
        if line.startswith("#EXTINF:"):
            group_match = re.search(r'group-title="([^"]+)"', line)
            logo_match = re.search(r'tvg-logo="([^"]+)"', line)
            name_parts = line.split(",")
            # Kanal adını direkt büyük harf yapıyoruz
            name = name_parts[-1].strip().upper() if len(name_parts) > 1 else "BILINMEYEN KANAL"
            
            current_info = {
                "group": group_match.group(1).upper() if group_match else "DIGER",
                "logo": logo_match.group(1) if logo_match else "https://via.placeholder.com/300",
                "name": name
            }
        
        elif line.startswith("http") and current_info:
            # ID'leri büyük harf ve alt tireli yapıyoruz
            chan_id = f"CH_{slugify(current_info['name'])}"
            cat_id = f"CAT_{slugify(current_info['group'])}"
            
            if chan_id not in channels:
                channels[chan_id] = {
                    "name": current_info['name'],
                    "group": current_info['group'],
                    "logo": current_info['logo'],
                    "streams": [{
                        "name": current_info['name'],
                        "title": f"{current_info['name']} | {current_info['group']}",
                        "url": line,
                        "behaviorHints": {"notClickable": False, "bingeGroup": chan_id}
                    }]
                }
                channel_count += 1 

                if cat_id not in categories:
                    raw_group_slug = slugify(current_info['group'])
                    display_name = category_map.get(raw_group_slug, f"📺 {current_info['group']}")
                    categories[cat_id] = {"display_name": display_name, "metas": []}
                
                categories[cat_id]["metas"].append({
                    "id": chan_id,
                    "type": "tv",
                    "name": current_info['name'],
                    "poster": current_info['logo'],
                    "description": f"{current_info['group']} KATEGORİSİNDE YAYIN."
                })
            current_info = None

    # --- 4. DOSYA ÜRETİMİ ---
    for cid, info in channels.items():
        with open(f"stream/tv/{cid}.json", 'w', encoding='utf-8') as f:
            json.dump({"streams": info["streams"]}, f, ensure_ascii=False)
        
        meta_data = {
            "meta": {
                "id": cid, "type": "tv", "name": info["name"], 
                "poster": info["logo"], "background": info["logo"]
            }
        }
        with open(f"meta/tv/{cid}.json", 'w', encoding='utf-8') as f:
            json.dump(meta_data, f, ensure_ascii=False)

    for cat_id, data in categories.items():
        with open(f"catalog/tv/{cat_id}.json", 'w', encoding='utf-8') as f:
            json.dump({"metas": data["metas"]}, f, ensure_ascii=False)

    manifest = {
        "id": "MOONCROWN_KATALOG",
        "version": "1.0.0",
        "name": "MOONCROWN_TV",
        "description": "MOONCROWN CANLI YAYINLAR (ILK 100 KANAL)",
        "resources": ["catalog", "meta", "stream"],
        "types": ["tv"],
        "idPrefixes": ["CH_"],
        "catalogs": [{"id": k, "type": "tv", "name": v['display_name']} for k, v in categories.items()]
    }
    
    with open("manifest.json", 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"İşlem Tamamlandı! {channel_count} kanal eklendi ve tümü büyük harfe/alt tireye dönüştürüldü.")

if __name__ == "__main__":
    process_stremio_addon()
