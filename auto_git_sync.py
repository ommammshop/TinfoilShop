import os
import time
import subprocess
import requests

# --- ตั้งค่าบัญชีของคุณ ---
WATCH_DIR = r"./covers"            
GITHUB_USER = "ommammshop"         
GITHUB_REPO = "TinfoilShop"     
GITHUB_BRANCH = "main"             
IMAGE_FOLDER_IN_REPO = "covers"    

# URL เซิร์ฟเวอร์ร้านของคุณ
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
        self.pending_files = set() # คิวสำหรับเก็บรายชื่อไฟล์ที่เพิ่งเข้ามา
        self.last_event_time = time.time()

    def on_created(self, event):
        self.add_to_queue(event)

    def on_modified(self, event):
        self.add_to_queue(event)

    def add_to_queue(self, event):
        if not event.is_directory and event.src_path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            # โยนชื่อไฟล์เข้าคิว และรีเซ็ตเวลานับถอยหลังใหม่
            self.pending_files.add(event.src_path)
            self.last_event_time = time.time()

def process_batch(files_to_process):
    repo_dir = os.path.dirname(os.path.abspath(WATCH_DIR))
    print(f"\n[+] ก๊อปปี้ไฟล์เสร็จแล้ว! กำลังเตรียมอัปโหลด {len(files_to_process)} รูปขึ้น GitHub...")
    
    try:
        # 1. สั่ง Add ไฟล์ทั้งหมด (รวบยอด)
        subprocess.run(["git", "add", "."], cwd=repo_dir, check=True, stdout=subprocess.DEVNULL)
        
        # 2. เช็คสถานะ
        status = subprocess.run(["git", "status", "--porcelain"], cwd=repo_dir, capture_output=True, text=True)
        if not status.stdout.strip():
            print("[-] ไม่มีไฟล์ใหม่ ข้ามการทำงาน...")
            return

        # 3. สั่ง Commit และ Push ครั้งเดียว
        commit_msg = f"Auto-sync {len(files_to_process)} new covers"
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=repo_dir, check=True, stdout=subprocess.DEVNULL)
        print("[>] กำลัง Push ขึ้นเซิร์ฟเวอร์ GitHub (อาจใช้เวลาสักครู่หากไฟล์เยอะ)...")
        subprocess.run(["git", "push", "origin", GITHUB_BRANCH], cwd=repo_dir, check=True, stdout=subprocess.DEVNULL)
        print(f"[✓] อัปโหลดทั้ง {len(files_to_process)} รูปขึ้น GitHub สำเร็จรวดเดียว!")
        
        # 4. ส่งข้อมูลไปที่หลังบ้านของร้าน (วนลูปส่งข้อมูลทีละรูปให้ Database)
        print("[>] กำลังซิงก์ข้อมูลกับเซิร์ฟเวอร์ร้าน...")
        api_error_shown = False
        for file_path in files_to_process:
            file_name = os.path.basename(file_path)
            game_code, _ = os.path.splitext(file_name)
            github_raw_url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/{IMAGE_FOLDER_IN_REPO}/{file_name}"
            
            # ยิง API
            payload = {
                "game_code": game_code,
                "cover_url": github_raw_url,
                "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            try:
                response = requests.post(STORE_SERVER_URL, json=payload, timeout=5)
                if response.status_code == 200:
                    print(f"    - [✓] {game_code}")
            except requests.exceptions.RequestException:
                if not api_error_shown:
                    print(f"[!] ไม่สามารถเชื่อมต่อเซิร์ฟเวอร์ฝั่งร้านได้ (แต่รูปขึ้น GitHub ไปแล้วนะ)")
                    api_error_shown = True # แจ้งเตือนแค่ครั้งเดียวพอ จะได้ไม่รกจอ 500 บรรทัด
                    
    except subprocess.CalledProcessError as e:
        print(f"[X] เกิดข้อผิดพลาดกับคำสั่ง Git: {e}")
    except Exception as e:
        print(f"[X] เกิดข้อผิดพลาดระบบ: {e}")

if __name__ == "__main__":
    if not os.path.exists(WATCH_DIR):
        os.makedirs(WATCH_DIR)
        
    event_handler = AutoSyncHandler()
    observer = Observer()
    observer.schedule(event_handler, path=WATCH_DIR, recursive=False)
    
    print("=" * 60)
    print(" 🚀 สคริปต์ Auto-Sync GitHub แบบทำงานเป็นกลุ่ม (Batch) เริ่มทำงานแล้ว")
    print(f" 📂 โฟลเดอร์ที่ต้องเอารูปมาใส่: {os.path.abspath(WATCH_DIR)}")
    print("=" * 60)
    
    observer.start()
    try:
        while True:
            # ตรวจสอบว่าในคิวมีไฟล์ไหม และไม่ได้มีการเพิ่มไฟล์ใหม่มาเกิน 3 วินาทีแล้ว
            if event_handler.pending_files and (time.time() - event_handler.last_event_time > 3):
                # ดึงข้อมูลไฟล์ออกจากคิวมาทำงาน
                files_snapshot = list(event_handler.pending_files)
                event_handler.pending_files.clear()
                
                # ส่งไปจัดการรวดเดียว
                process_batch(files_snapshot)
                
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()