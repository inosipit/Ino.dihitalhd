import os
import asyncio
import uvicorn
from fastapi import FastAPI, UploadFile, File, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_socketio import SocketManager
from telethon import TelegramClient, events

# --- KONFIGURASI PENTING ---
# Ambil ID dan HASH kamu di https://my.telegram.org
API_ID = '37350663' 
API_HASH = '2576953ef710f5acfe5628a9fc46c833'
TARGET_BOT = 'HdFotoBot' 

app = FastAPI()
sio = SocketManager(app=app)

# Pastikan folder penyimpanan ada agar tidak error
if not os.path.exists("static"):
    os.makedirs("static")

# Koneksi ke folder static dan templates yang kamu buat di Acode
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Inisialisasi Userbot
client = TelegramClient('ino_session', API_ID, API_HASH)

@app.on_event("startup")
async def startup():
    # Menjalankan userbot saat server aktif
    await client.start()

@app.get("/")
async def home(request: Request):
    # Menampilkan halaman utama website
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
async def upload_photo(file: UploadFile = File(...)):
    # 1. Simpan foto input dari website ke folder static
    temp_path = f"static/input_{file.filename}"
    with open(temp_path, "wb") as buffer:
        buffer.write(await file.read())
    
    # 2. Kirim foto tersebut ke bot target (@HdFotoBot)
    async with client:
        await client.send_file(TARGET_BOT, temp_path)
    
    return {"status": "Processing"}

# --- LOGIKA PENANGKAP BALASAN TELEGRAM ---
@client.on(events.NewMessage(from_users=TARGET_BOT))
async def handler(event):
    # Cek jika bot mengirim pesan teks (biasanya info LIMIT)
    if event.text and not event.document:
        msg = event.text.lower()
        if any(x in msg for x in ["limit", "sınır", "reached", "wait", "tunggu"]):
            await sio.emit('limit_info', {'msg': 'PROTOCOL ERROR: BOT LIMIT REACHED'})
            return

    # Cek jika bot mengirim dokumen (File HD kualitas asli)
    if event.document:
        # Beri nama file unik dengan awalan INO_HD
        filename = f"INO_HD_{event.document.id}.jpg"
        save_path = f"static/{filename}"
        
        # Download file dari Telegram ke folder static di server/hosting
        await event.download_media(file=save_path)
        
        # Beritahu website lewat Socket agar foto langsung muncul tanpa refresh
        await sio.emit('hasil_siap', {'url': f'/static/{filename}'})
        print(f"Sistem: Foto {filename} berhasil di-HD-kan!")

if __name__ == "__main__":
    # Jalankan di port 8080 (standar untuk testing dan hosting)
    uvicorn.run(app, host="0.0.0.0", port=8080)
