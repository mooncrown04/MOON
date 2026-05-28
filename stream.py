import re
import json
import os
import shutil
import requests

# --- AYARLAR ---

# 1. 🆕 KENDİ ÖZEL KATEGORİLERİNİZ VE KANALLARINIZ
MANUEL_OZEL_KATEGORILER = {
    "⭐ ULUSAL KANALLAR": ["TRT 1", "ATV", "KANAL D","SHOW TV", "NOW TV", "STAR TV","KANAL 7","TV 8", "TV 8.5", "BEYAZ TV"],
    "⚽ SPOR": ["BEIN SPORTS 1", "HT SPOR","TIVIBU SPOR", "A SPOR","TRT SPOR YILDIZ", "FUTBOL TV", "BEIN SPORTS 2"],
    "BELGESEL": ["NATGEO CHANNEL","NAT GEO WILD", "TLC","DMAX", "TRT BELGESEL","YABAN TV", "ÇIFTÇI TV"],
    "📰 HABER": ["HALK TV", "TV 100", "SÖZCÜ TV","NTV", "HABERTÜRK", "HABER GLOBAL","TRT HABER","24 TV", "FLASH HABER TV", "A HABER",  "TGRT HABER", "ULUSAL KANAL", "NEO HABER"],
    "🎬 SİNEMA & DİZİ": ["FILM SCREEN","TABII TV", "TIVI6","EKOL TV", "TEVE 2","A2", "DIZI-FILM TV", "SIYAH BEYAZ AŞK","TATLI İNTIKAM","ZALIM İSTANBUL"],
}

# 2. Bu kelimeler M3U KATEGORİ (group-title) adında geçerse kendi adıyla kategori olur:
OZEL_KATEGORILER = ["GLWIZ","TOUCHTV","FREESHOT"]

# 3. Bu kelimeler KANAL İSMİNDE geçerse "SEÇILI" kategorisinde toplanır:
SECILI_KANAL_FILTRESI = ["194", "198", "202", "204", "206", "208", "210", "212", "214", "216", "KARESİ RADYO"]

# 4. 🚫 ENGELLENEN KATEGORİLER (Stremio'da bağımsız katalog olarak oluşmasını istemediğin gruplar)
# M3U'daki group-title adını buraya yazarsan o grup adına bir kategori OLUŞMAZ.
# Ancak içindeki kanal senin yukarıdaki listelerinde (Örn: SPOR, HABER) varsa, o listelere dahil edilir ve ENGELLEYENMEZ.
ENGELLENEN_KATEGORILER = ["DINI", "TURK HD+ LINE", "SARKORTV", "GLWIZ", "ARABESK RADYOLAR", "Freeshot Arabia", "Freeshot Ex-Yu", "Freeshot Albania & Kosovo", "Freeshot Brasil", "GLWIZ", "Freeshot Cyprus & Greece", "FREESHOT", "TOUCHTV"]


def slugify(text):
    """ID ve Dosya adları için metni temizler, büyük harf yapar ve tireleri boşlukla değiştirir."""
    if not text: return "DIGER"
    text = text.lower()
    tr_map = str.maketrans("çığöşü", "cigosu")
    text = text.translate(tr_map)
    text = text.upper()
    text = text.replace("-", " ")
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text.replace(" ", "_")

def process_stremio_addon():
    # --- 0. DIŞARIDAN KANAL AÇIKLAMALARINI YÜKLE ---
    kanal_aciklamalari = {}
    json_dosya_adi = "kanallar_bilgi.json"
    
    if os.path.exists(json_dosya_adi):
        try:
            # DÜZELTME: Dosyayı korumak ve sadece okumak için 'r' modu kullanıldı.
            with open(json_dosya_adi, 'r', encoding='utf-8') as f:
                content = f.read()
                if content.strip():
                    kanal_aciklamalari = json.loads(content)
            print(f"ℹ️ {json_dosya_adi} başarıyla yüklendi. {len(kanal_aciklamalari)} adet kanal açıklaması eşleştirilecek.")
        except Exception as e:
            print(f"⚠️ {json_dosya_adi} okunurken hata oluştu, varsayılan açıklamalar kullanılacak: {e}")
    else:
        print(f"⚠️ {json_dosya_adi} bulunamadı! Kanallar varsayılan açıklamalarla üretilecek.")

    # Engellenen kategorileri büyük harf standardına çeviriyoruz
    engellenenler_upper = [kat.upper() for kat in ENGELLENEN_KATEGORILER]

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
    engellenen_kategori_kanal_sayisi = 0

    category_map = {
        "ULUSAL": "📺 Ulusal Kanallar",
        "SPOR KANALLARI": "⚽ SPOR", 
        "SPOR": "⚽ SPOR",
        "HABERLER": "📰 Haber",
        "SINEMA": "🎬 SİNEMA & DİZİ",
        "DIZI": "🎬 SİNEMA & DİZİ",
        "FILM": "🎞️ FİLM",
        "BELGESEL": "🦒 Belgesel & Yaşam",
        "MUZIK": "🎵 Müzik",
        "ANIMASYON": "🎨 Animasyon",
        "COCUK": "🧸 Çocuk",
        "YETISKIN": "🔞 Yetişkin",
        "TOUCHTV SLOVAKIA": "📡 YABANCI ",
        "TOUCHTV": "📡 YABANCI",
        "FREESHOT": "📡 YABANCI",
        "SARKORTV": "📡 YABANCI ",
        "DIGER": "📡 Diğer Kanallar"
    }

    manuel_slugs = {}
    for custom_cat_name in MANUEL_OZEL_KATEGORILER.keys():
        manuel_slugs[slugify(custom_cat_name)] = custom_cat_name

    lines = m3u_content.splitlines()
    current_info = None

    for line in lines:
        line = line.strip()
        
        if line.startswith("#EXTINF:"):
            group_match = re.search(r'group-title="([^"]+)"', line)
            logo_match = re.search(r'tvg-logo="([^"]+)"', line)
            author_match = re.search(r'group-author="([^"]+)"', line)
            
            name_parts = line.split(",")
            name = name_parts[-1].strip().replace("-", " ").upper() if len(name_parts) > 1 else "BILINMEYEN KANAL"
            
            raw_group = group_match.group(1).upper() if group_match else "DIGER"
            assigned_group = raw_group
            
            matched_keyword_name = None
            
            # --- ÖNCELİKLİ ADIM: KANAL SENİN ÖZEL LİSTELERİNDE VAR MI? ---
            found_custom = False
            for custom_cat, keywords in MANUEL_OZEL_KATEGORILER.items():
                for kw in keywords:
                    if kw.upper() in name:
                        assigned_group = custom_cat
                        matched_keyword_name = kw.upper()
                        found_custom = True
                        break
                if found_custom:
                    break

            if not found_custom:
                found_by_cat = False
                for cat_word in OZEL_KATEGORILER:
                    if cat_word in raw_group:
                        assigned_group = cat_word
                        found_by_cat = True
                        break
                
                if not found_by_cat:
                    for name_word in SECILI_KANAL_FILTRESI:
                        if name_word in name:
                            assigned_group = "SECILI"
                            found_by_cat = True
                            break

                # --- KATEGORİ ENGELLEME FİLTRESİ ---
                # Eğer kanal senin hiçbir listene eşleşmediyse VE orijinal grubu engellenenler listesindeyse:
                # O zaman kategorinin oluşmasını engellemek için kanalı tamamen atla.
                if not found_by_cat and raw_group in engellenenler_upper:
                    current_info = None
                    engellenen_kategori_kanal_sayisi += 1
                    continue

            current_info = {
                "group": assigned_group,
                "logo": logo_match.group(1) if logo_match else "https://via.placeholder.com/300",
                "name": name,
                "keyword_name": matched_keyword_name if matched_keyword_name else name,
                "author": author_match.group(1) if author_match else "Bilinmeyen Kaynak"
            }
        
        elif line.startswith("http") and current_info:
            chan_id = f"CH_{slugify(current_info['name'])}"
            cat_id = f"CAT_{slugify(current_info['group'])}"
            
            # JSON'dan eşleşen açıklamayı bulma
            description_text = f"{current_info['group']} KATEGORISINDE YAYIN."
            for json_key, desc in kanal_aciklamalari.items():
                if json_key.upper() in current_info['name']:
                    description_text = desc
                    break
            
            if chan_id not in channels:
                channels[chan_id] = {
                    "name": current_info['name'],
                    "group": current_info['group'],
                    "logo": current_info['logo'],
                    "description": description_text,
                    "streams": []
                }
                channel_count += 1 

                if cat_id not in categories:
                    raw_slug = slugify(current_info['group'])
                    
                    if current_info['group'] == "SECILI":
                        display_name = "⭐ SEÇİLİ KANALLAR"
                    elif raw_slug in manuel_slugs:
                        display_name = manuel_slugs[raw_slug]
                    else:
                        display_name = category_map.get(raw_slug, f"📂 {current_info['group']}")
                    
                    categories[cat_id] = {"display_name": display_name, "metas": []}
                
                categories[cat_id]["metas"].append({
                    "id": chan_id,
                    "type": "tv",
                    "name": current_info['name'],
                    "poster": current_info['logo'],
                    "description": description_text
                })

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
                "id": cid, 
                "type": "tv", 
                "name": info["name"], 
                "poster": info["logo"], 
                "background": info["logo"],
                "description": info["description"]
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

    print(f"İşlem Tamamlandı! {channel_count} kanal güncellendi. İstediğin özel kanallar korundu, sahipsiz kalan engellenmiş kategoriler ({engellenen_kategori_kanal_sayisi} adet kanal) oluşturulmadı.")

if __name__ == "__main__":
    process_stremio_addon()
