import telebot
import phonenumbers
from phonenumbers import carrier, geocoder, timezone
from datetime import datetime

# ⚠️ PERINGATAN: Token ini sudah terekspos! Sebaiknya ganti segera
BOT_TOKEN = "8961612725:AAH85WMbx_O8n0ebpbNgTiBLFaot8Q1RRqk"
bot = telebot.TeleBot(BOT_TOKEN)

# Sumber resmi & penjelasan lengkap
SUMBER_CEK = {
    "aduannomor": {
        "nama": "AduanNomor.id — Kemenkominfo RI",
        "link": "https://aduannomor.id",
        "kegunaan": "Cek riwayat laporan + laporkan → nomor bisa diblokir dari seluruh jaringan seluler",
        "cara": "Buka → Cek Nomor → masukkan nomor → jika belum ada, klik 'Laporkan Nomor Seluler' → pilih kategori: Penipuan → unggah bukti → kirim"
    },
    "kredibel": {
        "nama": "Kredibel.co.id",
        "link": "https://kredibel.co.id",
        "kegunaan": "Database laporan masyarakat khusus Indonesia",
        "cara": "Masukkan nomor → lihat apakah sudah dilaporkan orang lain"
    },
    "truecaller": {
        "nama": "Truecaller",
        "link": "https://www.truecaller.com",
        "kegunaan": "Lihat nama yang dipakai nomor tersebut di kontak orang lain",
        "cara": "Cari nomor → perhatikan nama yang muncul, jika bertuliskan 'Penipu' = sudah banyak lapor"
    },
    "getcontact": {
        "nama": "GetContact",
        "link": "https://www.getcontact.com",
        "kegunaan": "Lihat nama apa yang disimpan orang lain untuk nomor tersebut",
        "cara": "Cek nama yang muncul — jika tertulis 'Penipu', 'Jangan Transfer' = berbahaya"
    },
    "cekrekening": {
        "nama": "CekRekening.id — Kemenkominfo RI",
        "link": "https://cekrekening.id",
        "kegunaan": "Jika sudah transfer uang → cek rekening tujuan",
        "cara": "Masukkan nomor rekening/e-wallet → laporkan dengan bukti transfer"
    },
    "patrolisiber": {
        "nama": "PatroliSiber.id — Kepolisian RI",
        "link": "https://patrolisiber.id",
        "kegunaan": "Lapor ke kepolisian resmi untuk kasus kerugian",
        "cara": "Isi laporan dengan kronologi lengkap + bukti pendukung"
    },
    "wa_profil": {
        "nama": "Cek Profil WhatsApp",
        "link": "wa.me/[nomor]",
        "kegunaan": "Lihat foto profil, status, kapan aktif terakhir",
        "cara": "Buka tautan → perhatikan: foto profil kosong, baru dibuat, atau sering ganti nama = berisiko tinggi"
    }
}

# Kode negara yang PERLU diwaspadai
KODE_MENCURIGAKAN = {
    "+44": "Inggris — sering dipakai VoIP/nokos",
    "+1": "AS/Kanada — periksa baik-baik",
    "+234": "Nigeria — sangat sering dipakai penipuan",
    "+372": "Estonia — umum layanan nomor maya",
    "+380": "Ukraina — periksa konteks",
    "+423": "Liechtenstein — nomor maya",
    "+500": "Kepulauan Falkland — jarang dipakai warga biasa",
    "+506": "Kosta Rika — periksa baik-baik",
    "+679": "Fiji — jarang dipakai warga biasa"
}

def bersihkan_nomor(nomor):
    return ''.join(c for c in nomor if c.isdigit() or c == '+')

def format_wa_link(nomor):
    n = bersihkan_nomor(nomor)
    if n.startswith('+'): n = n[1:]
    if n.startswith('0'): n = '62' + n[1:]
    return f"https://wa.me/{n}"

def cek_lengkap(nomor):
    try:
        n = bersihkan_nomor(nomor)
        if not n.startswith('+'):
            n = '+' + n
        
        nomor_obj = phonenumbers.parse(n, None)
        kode_awal = '+' + str(nomor_obj.country_code)
        
        info = {
            "nomor_awal": nomor,
            "nomor_resmi": phonenumbers.format_number(nomor_obj, phonenumbers.PhoneNumberFormat.INTERNATIONAL),
            "negara": geocoder.description_for_number(nomor_obj, "id") or "Tidak diketahui",
            "operator": carrier.name_for_number(nomor_obj, "id") or "Tidak teridentifikasi",
            "zona_waktu": ", ".join(timezone.time_zones_for_number(nomor_obj)) or "Tidak diketahui",
            "valid": phonenumbers.is_valid_number(nomor_obj),
            "indonesia": nomor_obj.country_code == 62,
            "kode_awal": kode_awal,
            "wa_link": format_wa_link(nomor),
            "peringatan": KODE_MENCURIGAKAN.get(kode_awal, None)
        }
        return True, info
    except Exception as e:
        return False, str(e)


@bot.message_handler(commands=['start', 'mulai'])
def selamat_datang(msg):
    teks = """
🛡️ SISTEM CEK & LAPOR NOMOR PENIPU
Semua Jalur Resmi & Aman ✅

Kirimkan nomor yang ingin diperiksa:
Contoh: +6281234567890

Saya akan tampilkan informasi lengkap + panduan lapor.
    """
    bot.send_message(msg.chat.id, teks)


@bot.message_handler(commands=['bantu', 'info'])
def penjelasan_hukum(msg):
    bot.send_message(msg.chat.id, """
📋 INFORMASI YANG BISA & TIDAK BISA DIKETAHUI

✅ BISA: Negara, operator, cek di sumber publik
❌ TIDAK BISA: Nama pemilik, lokasi, data perangkat — dilindungi hukum

Semua yang mengaku bisa "cek data pribadi" = PENIPUAN!
    """)


@bot.message_handler(func=lambda m: True)
def tampilkan_hasil(msg):
    nomor = msg.text.strip()
    sah, data = cek_lengkap(nomor)
    
    if not sah:
        bot.send_message(msg.chat.id, f"❌ Format tidak dikenali: {data}\nGunakan contoh: +6281234567890")
        return
    
    # Simpan catatan
    with open("laporan_nomor.txt", "a") as f:
        f.write(f"{datetime.now()} | Pengguna:{msg.from_user.id} | {data['nomor_resmi']}\n")
    
    res = f"""
🔍 HASIL PEMERIKSAAN LENGKAP

━━━━━━━━━━━━━━━━━━━━━━
📱 Nomor: {data['nomor_resmi']}
🌍 Negara: {data['negara']}
📡 Operator: {data['operator']}
⏰ Zona Waktu: {data['zona_waktu']}
✅ Format Valid: {'YA' if data['valid'] else 'TIDAK — periksa kembali'}
🇮🇩 Nomor Indonesia: {'YA' if data['indonesia'] else 'TIDAK — luar negeri'}
🔗 Cek WhatsApp: {data['wa_link']}
"""
    
    if data['peringatan']:
        res += f"""
⚠️ PERINGATAN KUAT ⚠️
Nomor ini berasal dari: {data['kode_awal']}
Keterangan: {data['peringatan']}
Banyak penipu memakai nomor dari negara ini.
JANGAN kirim uang atau data pribadi!
"""
    elif data['indonesia']:
        res += "\n✅ Nomor lokal — tetap waspada, cek sumber di bawah"
    
    res += f"""
━━━━━━━━━━━━━━━━━━━━━━
📋 CEK DI SEMUA SUMBER INI:

1️⃣ {SUMBER_CEK['aduannomor']['nama']}
   🔗 {SUMBER_CEK['aduannomor']['link']}
   {SUMBER_CEK['aduannomor']['kegunaan']}

2️⃣ {SUMBER_CEK['kredibel']['nama']}
   🔗 {SUMBER_CEK['kredibel']['link']}

3️⃣ {SUMBER_CEK['truecaller']['nama']}
   🔗 {SUMBER_CEK['truecaller']['link']}

4️⃣ {SUMBER_CEK['getcontact']['nama']}
   🔗 {SUMBER_CEK['getcontact']['link']}

5️⃣ Cek Profil WhatsApp
   🔗 {data['wa_link']}
   • Foto kosong / baru dibuat / sering ganti nama → BERISIKO
"""
    
    res += f"""
━━━━━━━━━━━━━━━━━━━━━━
🚨 CARA LAPORKAN AGAR DIBLOKIR:

✅ 1. AduanNomor.id (PALING PENTING!)
   🔗 https://aduannomor.id
   • Klik "Laporkan Nomor Seluler"
   • Nomor: {data['nomor_resmi']}
   • Kategori: Penipuan → unggah bukti → kirim
   • Banyak laporan → diblokir dari seluruh jaringan!

✅ 2. Dari WhatsApp
   • Buka: {data['wa_link']}
   • Ketuk nomor → Laporkan → Laporkan dan Blokir

✅ 3. Jika sudah kirim uang
   🔗 https://cekrekening.id
   • Laporkan nomor rekening/e-wallet tujuan

✅ 4. Lapor ke Polisi
   🔗 https://patrolisiber.id
   • Atau ke kantor polisi terdekat dengan bukti lengkap
"""
    
    res += """
━━━━━━━━━━━━━━━━━━━━━━
💡 TANDA PENIPU:
• Minta kode OTP/PIN/password → JANGAN KASIH
• Mendesak cepat, takut hilang → TOLAK
• Mengaku petugas bank/pemerintah → HUBUNGI NOMOR RESMI NYA
• Janji hadiah/uang mudah → PENIPUAN
• Tidak mau telepon langsung → CURIGA

⚠️ JANGAN KIRIM: OTP, PIN, KTP, Uang
Resmi TIDAK meminta data tersebut lewat WA!
━━━━━━━━━━━━━━━━━━━━━━
"""
    
    bot.send_message(msg.chat.id, res, disable_web_page_preview=True)


print("Bot berjalan...")
bot.infinity_polling()
