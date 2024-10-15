from telethon import TelegramClient, events
import os
import asyncio
from datetime import datetime

api_id = '29798494'
api_hash = '53273c1de3e68a9ecdb90de2dcf46f6c'

client = TelegramClient('userbot', api_id, api_hash)
device_owner_id = None
afk_reason = None

# Directory to store QR code images
QR_CODE_DIR = "qr_codes"

# Ensure the directory exists
os.makedirs(QR_CODE_DIR, exist_ok=True)

# Blacklisted group list
blacklisted_groups = []

# Watermark text
WATERMARK_TEXT = ""

# Function to append watermark to a message
def append_watermark_to_message(message):
    return f"{message}\n\n{WATERMARK_TEXT}"

async def main():
    await client.start()
    print("Client Created")

    global device_owner_id

    if not await client.is_user_authorized():
        phone_number = input("Please enter your phone number (with country code): ")
        try:
            await client.send_code_request(phone_number)
            print("Code sent successfully!")
        except Exception as e:
            print(f"Error requesting code: {e}")
            return
        
        code = input("Please enter the code you received: ")
        try:
            await client.sign_in(phone_number, code=code)
            print("Signed in successfully!")
        except Exception as e:
            print(f"Error during sign in: {e}")
            return

    print("Client Authenticated")

    device_owner = await client.get_me()
    device_owner_id = device_owner.id
    print(f"Device owner ID: {device_owner_id}")

def is_device_owner(sender_id):
    return sender_id == device_owner_id

@client.on(events.NewMessage(pattern='/p', outgoing=True))
async def promote(event):
    sender = await event.get_sender()
    if not is_device_owner(sender.id):
        await event.respond(append_watermark_to_message("❌ Anda tidak berwenang untuk menggunakan perintah ini."))
        print("Unauthorized access attempt blocked.")
        return

    reply_message = await event.get_reply_message()
    if not reply_message:
        await event.respond(append_watermark_to_message("❌ Silakan membalas pesan, gambar, atau video untuk digunakan sebagai konten jaseb"))
        return
    
    sent_count = 0
    failed_count = 0
    delay = 1 # Set your desired delay time in seconds
    status_message = await event.respond(append_watermark_to_message("🔎 Memulai Jaseb..."))

    groups = [dialog for dialog in await client.get_dialogs() if dialog.is_group]
    total_groups = len(groups)

    loading_symbols = [".", "..", "...", "...."]

    for dialog in groups:
        if dialog.id in blacklisted_groups:
            continue
        try:
            if reply_message.media:
                media_path = await client.download_media(reply_message.media)
                await client.send_file(dialog.id, media_path, caption=append_watermark_to_message(reply_message.message))
            else:
                message_with_watermark = append_watermark_to_message(reply_message.message)
                await client.send_message(dialog.id, message_with_watermark)
            sent_count += 1
            progress = (sent_count / total_groups) * 100
            
            for remaining_time in range(delay, 0, -1):
                loading_animation = "".join([symbol for symbol in loading_symbols[:sent_count % len(loading_symbols) + 1]])
                await status_message.edit(append_watermark_to_message(f"🔎 Mengirim jaseb ke grup{loading_animation} {progress:.2f}%\n\n✔️ Terkirim: {sent_count}\n❌ Gagal: {failed_count}\n⏭ Grup selanjutnya {remaining_time} detik lagi..."))
                await asyncio.sleep(1)
        except Exception as e:
            failed_count += 1
            print(f"Failed to send to {dialog.title}: {e}")
    
    await status_message.edit(append_watermark_to_message(f"✅ Selesai mengirim jaseb ke semua grup!\n\nTotal grup terkirim: {sent_count}\nTotal grup yang gagal: {failed_count}"))

@client.on(events.NewMessage(pattern='/blacklist', outgoing=True))
async def blacklist_group(event):
    sender = await event.get_sender()
    if not is_device_owner(sender.id):
        await event.respond(append_watermark_to_message("❌ Anda tidak berwenang untuk menggunakan perintah ini."))
        print("Unauthorized access attempt blocked.")
        return

    group_id = event.chat_id
    if group_id not in blacklisted_groups:
        blacklisted_groups.append(group_id)
        await event.respond(append_watermark_to_message("🚫 Grup telah berhasil masuk daftar hitam."))
    else:
        await event.respond(append_watermark_to_message("🚫 Grup ini sudah masuk daftar hitam."))

@client.on(events.NewMessage(pattern='/addqr', outgoing=True))
async def add_qr(event):
    sender = await event.get_sender()
    if not is_device_owner(sender.id):
        await event.respond(append_watermark_to_message("❌ Anda tidak berwenang untuk menggunakan perintah ini."))
        print("Unauthorized access attempt blocked.")
        return

    reply_message = await event.get_reply_message()
    if not reply_message or not reply_message.media:
        await event.respond(append_watermark_to_message("❌ Harap balas gambar kode QR untuk menggunakan perintah ini."))
        return

    try:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        file_path = os.path.join(QR_CODE_DIR, f"qr_{timestamp}.jpg")
        await client.download_media(reply_message.media, file_path)
        await event.respond(append_watermark_to_message("✅ QR Code berhasil ditambahkan!"))
        print(f"QR code added with timestamp: {timestamp}")
    except Exception as e:
        await event.respond(append_watermark_to_message("❌ Gagal menambahkan QR Code."))
        print(f"Error: {e}")

@client.on(events.NewMessage(pattern='/getqr', outgoing=True))
async def get_qr(event):
    qr_files = sorted(os.listdir(QR_CODE_DIR))
    if not qr_files:
        await event.respond(append_watermark_to_message("❌ Tidak ada Qr Code yang tersedia."))
        return

    try:
        for qr_file in qr_files:
            file_path = os.path.join(QR_CODE_DIR, qr_file)
            await client.send_file(event.chat_id, file_path, caption=append_watermark_to_message(f"🖼 QR Code: {qr_file}"))
            await asyncio.sleep(1)  # Optional delay to avoid spamming
    except Exception as e:
        await event.respond(append_watermark_to_message("❌ Gagal menambahkan QR Code."))
        print(f"Error sending QR code: {e}")

@client.on(events.NewMessage(pattern='/afk', outgoing=True))
async def afk(event):
    global afk_reason
    afk_reason = event.message.message[len('/afk '):].strip()
    if not afk_reason:
        afk_reason = "AFK"
    await event.respond(append_watermark_to_message(f"💤 Mode AFK diaktifkan dengan alasan: {afk_reason}"))
    print(f"AFK mode enabled with reason: {afk_reason}")

@client.on(events.NewMessage(incoming=True))
async def handle_incoming(event):
    global afk_reason
    if afk_reason and event.mentioned:
        await event.reply(append_watermark_to_message(f"{afk_reason}"))

@client.on(events.NewMessage(pattern='/back', outgoing=True))
async def back(event):
    global afk_reason
    afk_reason = None
    await event.respond(append_watermark_to_message("👋 Halo Aku On Kembali"))
    print("AFK mode disabled.")

@client.on(events.NewMessage(pattern='/help', outgoing=True))
async def show_help(event):
    help_text = (
        "🛠 **Perintah yang Tersedia:**\n"
        "/p - Promosikan pesan ke semua grup.\n"
        "/blacklist - Daftar hitamkan grup saat ini agar tidak menerima promosi.\n"
        "/addqr - Tambahkan kode QR (kirim gambar sebagai balasan atas perintah ini).\n"
        "/getqr - Ambil semua kode QR yang disimpan.\n"
        "/afk <alasan> - Tetapkan pesan AFK dengan alasannya.\n"
        "/back - Nonaktifkan mode AFK.\n"
        "/ping - Periksa waktu respons bot.\n"
        f"\n{WATERMARK_TEXT}"
    )
    await event.respond(help_text)

@client.on(events.NewMessage(pattern='/ping', outgoing=True))
async def ping(event):
    start = datetime.now()
    await event.respond(append_watermark_to_message("🏓 Pong!"))
    end = datetime.now()
    latency = (end - start).total_seconds() * 1000
    await event.respond(append_watermark_to_message(f"📈 Ping: {latency:.2f} ms"))

async def run_bot():
    await main()
    print("Bot is running...")
    await client.run_until_disconnected()

if __name__ == '__main__':
    client.loop.run_until_complete(run_bot())
            
