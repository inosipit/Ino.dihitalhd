import os
import asyncio
import threading
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
from telethon import TelegramClient, events

# --- KONFIGURASI ---
API_ID = '37350663'
API_HASH = '2576953ef710f5acfe5628a9fc46c833'
TARGET_BOT = 'HdFotoBot'

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

if not os.path.exists("static"): os.makedirs("static")

telethon_loop = None
client = TelegramClient('ino_session', API_ID, API_HASH)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({"status": "Error", "message": "File gak ada"}), 400

    file = request.files['file']
    path = f"static/{file.filename}"
    file.save(path)
    
    if telethon_loop:
        # Fungsi internal untuk kirim foto dan klik otomatis
        async def send_and_confirm():
            # 1. Kirim Foto
            sent_msg = await client.send_file(TARGET_BOT, path)
            # 2. Tunggu sebentar biar bot munculin tombol
            await asyncio.sleep(1.5)
            # 3. Kirim teks "Evet" (Otomatis konfirmasi)
            await client.send_message(TARGET_BOT, "Evet")
            print(f"🚀 Sent to bot: {file.filename} and confirmed 'Evet'")

        asyncio.run_coroutine_threadsafe(send_and_confirm(), telethon_loop)
        return jsonify({"status": "Processing"})
    
    return jsonify({"status": "Error", "message": "Server belum siap"}), 500

@client.on(events.NewMessage(from_users=TARGET_BOT))
async def handler(event):
    # Cari dokumen/file yang dikirim balik oleh bot
    if event.document:
        path = await event.download_media(file="static/")
        filename = os.path.basename(path)
        # Kasih tau web kalau hasil sudah siap
        socketio.emit('hasil_siap', {'url': f'/static/{filename}'})
        print(f"✅ Ino.digital: Hasil HD Ready -> {filename}")

def run_telethon():
    global telethon_loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    telethon_loop = loop 
    client.start()
    client.run_until_disconnected()

if __name__ == '__main__':
    threading.Thread(target=run_telethon, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=8080, allow_unsafe_werkzeug=True)
