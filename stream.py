import re
import json
import os
import shutil
import requests

# --- AYARLAR ---
# 1. Bu kelimeler M3U KATEGORİ (group-title) adında geçerse kendi adıyla kategori olur:
OZEL_KATEGORILER = ["FREESHOT","GLWIZ"]

# 2. Bu kelimeler KANAL İSMİNDE geçerse "SEÇİLİ" kategorisinde toplanır:
SECILI_KANAL_FILTRESI = ["194", "198", "202","204", "206", "208", "210", "212","214"]

def slugify(text):
    """ID ve Dosya adları için metni temizler, büyük harf yapar ve tireleri boşlukla değiştirir."""
    if not text: return "DIGER"
    tr_map = str.maketrans("çığöşüÇİĞÖŞÜ", "cigosucigosu")
    text = text.translate(tr_map)
    text = text.upper()
    text = text.replace("-", " ")
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text.replace(" ", "_")

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
        line = line.strip()
        
        if line.startswith("#EXTINF:"):
            group_match = re.search(r'group-title="([^"]+)"', line)
            logo_match = re.search(r'tvg-logo="([^"]+)"', line)
            # Yeni eklenen: group-author bilgisini yakalar
            author_match = re.search(r'group-author="([^"]+)"', line)
            
            name_parts = line.split(",")
            name = name_parts[-1].strip().replace("-", " ").upper() if len(name_parts) > 1 else "BILINMEYEN KANAL"
            
            raw_group = group_match.group(1).upper() if group_match else "DIGER"
            assigned_group = raw_group
            found_by_cat = False

            # ÖNCE: Kategori araması (Kendi adıyla kategori olur)
            for cat_word in OZEL_KATEGORILER:
                if cat_word in raw_group:
                    assigned_group = cat_word
                    found_by_cat = True
                    break
            
            # SONRA: Eğer kategori bulunamadıysa kanal ismi araması (SEÇİLİ olur)
            if not found_by_cat:
                for name_word in SECILI_KANAL_FILTRESI:
                    if name_word in name:
                        assigned_group = "SECILI"
                        break

            current_info = {
                "group": assigned_group,
                "logo": logo_match.group(1) if logo_match else "https://via.placeholder.com/300",
                "name": name,
                "author": author_match.group(1) if author_match else "Bilinmeyen Kaynak"
            }
        
        elif line.startswith("http") and current_info:
            chan_id = f"CH_{slugify(current_info['name'])}"
            cat_id = f"CAT_{slugify(current_info['group'])}"
            
            if chan_id not in channels:
                channels[chan_id] = {
                    "name": current_info['name'],
                    "group": current_info['group'],
                    "logo": current_info['logo'],
                    "streams": []
                }
                channel_count += 1 

                if cat_id not in categories:
                    if current_info['group'] == "SECILI":
                        display_name = "⭐ SEÇİLİ KANALLAR"
                    else:
                        raw_slug = slugify(current_info['group'])
                        display_name = category_map.get(raw_slug, f"📂 {current_info['group']}")
                    
                    categories[cat_id] = {"display_name": display_name, "metas": []}
                
                categories[cat_id]["metas"].append({
                    "id": chan_id,
                    "type": "tv",
                    "name": current_info['name'],
                    "poster": current_info['logo'],
                    "description": f"{current_info['group']} KATEGORISINDE YAYIN."
                })

            # Streamleri birleştir (Aynı kanalda birden fazla link varsa)
            s_idx = len(channels[chan_id]["streams"]) + 1
            channels[chan_id]["streams"].append({
                "name": f"{current_info['name']}",
                "title": f"{current_info['author']} | Kaynak {s_idx} | ({current_info['group']})",
                "url": line,
                "behaviorHints": {"notClickable": False, "bingeGroup": chan_id}
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
        "logo": "https://st5.depositphotos.com/1041725/67731/v/380/depositphotos_677319750-stock-illustration-ararat-mountain-illustration-vector-white.jpg",
        "resources": ["catalog", "meta", "stream"],
        "types": ["tv"],
        "idPrefixes": ["CH_"],
        "catalogs": [{"id": k, "type": "tv", "name": v['display_name']} for k, v in categories.items()]
    }
    
    with open("manifest.json", 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"İşlem Tamamlandı! {channel_count} kanal güncellendi. Tireler boşluğa çevrildi.")

if __name__ == "__main__":
    process_stremio_addon()
