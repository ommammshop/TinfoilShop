import os
import time
import subprocess
import requests

# --- ตั้งค่าบัญชีของคุณ (ปรับให้ตรงกับบัญชี ommammshop แล้ว) ---
WATCH_DIR = r"./covers"            # โฟลเดอร์สำหรับลากรูปมาใส่
GITHUB_USER = "ommammshop"         # บัญชี GitHub ของคุณ
GITHUB_REPO = "TinfoilShop"     # ชื่อ Repository ที่ตั้งในขั้นตอนที่ 1
GITHUB_BRANCH = "main"             
IMAGE_FOLDER_IN_REPO = "covers"    

# URL เซิร์ฟเวอร์ร้านของคุณสำหรับรับข้อมูลไปอัปเดตไฟล์ JSON
STORE_SERVER_URL = "http://localhost:8000/api/update-cover" 
# ----------------------------------------------------

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("[!] กำลังติดตั้ง watchdog...")
    subprocess.run(["pip", "install", "watchdog"], check=True)
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

class AutoSyncHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.last_sync_time = 0
        self.cooldown = 2

    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            print(f"\n[+] เจอรูปใหม่: {os.path.basename(event.src_path)}")
            self.process_sync(event.src_path)

    def on_modified(self, event):
        if not event.is_directory and event.src_path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            current_time = time.time()
            if current_time - self.last_sync_time > self.cooldown:
                self.process_sync(event.src_path)
                self.last_sync_time = current_time

    def process_sync(self, file_path):
        file_name = os.path.basename(file_path)
        game_code, _ = os.path.splitext(file_name)
        repo_dir = os.path.dirname(os.path.abspath(WATCH_DIR))
        
        try:
            # สั่ง GitHub Desktop (git) ทำงานอัตโนมัติ
            subprocess.run(["git", "add", "."], cwd=repo_dir, check=True, stdout=subprocess.DEVNULL)
            subprocess.run(["git", "commit", "-m", f"Auto-sync cover: {file_name}"], cwd=repo_dir, check=True, stdout=subprocess.DEVNULL)
            subprocess.run(["git", "push", "origin", GITHUB_BRANCH], cwd=repo_dir, check=True, stdout=subprocess.DEVNULL)
            print(f"[✓] อัปโหลดรูป {file_name} ขึ้น GitHub สำเร็จ!")
            
            # สร้างลิงก์ตรงสำหรับ Tinfoil
            github_raw_url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/{IMAGE_FOLDER_IN_REPO}/{file_name}"
            print(f"[L] ลิงก์รูป: {github_raw_url}")
            
            # ส่งข้อมูลกลับไปที่หลังบ้านของร้าน
            self.sync_with_store_server(game_code, github_raw_url)
            
        except Exception as e:
            print(f"[X] เกิดข้อผิดพลาด: {e}")

    def sync_with_store_server(self, game_code, raw_url):
        payload = {
            "game_code": game_code,
            "cover_url": raw_url,
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        try:
            response = requests.post(STORE_SERVER_URL, json=payload, timeout=5)
            if response.status_code == 200:
                print(f"[✓] ซิงก์ข้อมูลรหัส [{game_code}] กับเซิร์ฟเวอร์ร้านเรียบร้อย")
        except requests.exceptions.RequestException:
            print(f"[!] ยังไม่ได้เปิดเซิร์ฟเวอร์รับข้อมูลฝั่งร้าน แต่รูปอัปโหลดขึ้น GitHub แล้ว")

if __name__ == "__main__":
    if not os.path.exists(WATCH_DIR):
        os.makedirs(WATCH_DIR)
        
    event_handler = AutoSyncHandler()
    observer = Observer()
    observer.schedule(event_handler, path=WATCH_DIR, recursive=False)
    
    print("=" * 60)
    print(" 🚀 สคริปต์ Auto-Sync GitHub เริ่มทำงานแล้ว")
    print(f" 📂 โฟลเดอร์ที่ต้องเอารูปมาใส่: {os.path.abspath(WATCH_DIR)}")
    print("=" * 60)
    
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()