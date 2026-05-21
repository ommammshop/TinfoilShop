import os
from PIL import Image

# 1. ตั้งค่าโฟลเดอร์
INPUT_FOLDER = r"C:\Games\fiddz\covers\b"  # โฟลเดอร์รูปต้นฉบับของคุณ (ที่ไฟล์ใหญ่ๆ)
OUTPUT_FOLDER = r"C:\Games\fiddz\covers\c" # โฟลเดอร์ที่ย่อเสร็จแล้ว (ให้มันสร้างใหม่)
TARGET_WIDTH = 500 # กำหนดความกว้าง (500px กำลังสวยสำหรับ Tinfoil)

if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

print("⏳ กำลังเริ่มย่อรูปภาพ... (อาจใช้เวลาสักครู่)")
count = 0

for filename in os.listdir(INPUT_FOLDER):
    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
        img_path = os.path.join(INPUT_FOLDER, filename)
        try:
            with Image.open(img_path) as img:
                # คำนวณความสูงให้ได้สัดส่วนเดิม
                wpercent = (TARGET_WIDTH / float(img.size[0]))
                hsize = int((float(img.size[1]) * float(wpercent)))
                
                # ย่อรูป
                img_resized = img.resize((TARGET_WIDTH, hsize), Image.Resampling.LANCZOS)
                
                # บันทึกเป็น .jpg และบีบอัดให้ไฟล์เล็ก (Quality 85 ถือว่าชัดและไฟล์เล็กมาก)
                out_name = os.path.splitext(filename)[0] + ".jpg"
                out_path = os.path.join(OUTPUT_FOLDER, out_name)
                
                # ถ้าไฟล์เป็น RGBA (มีพื้นหลังใส) ต้องแปลงเป็น RGB ก่อนเซฟเป็น JPG
                if img_resized.mode in ("RGBA", "P"):
                    img_resized = img_resized.convert("RGB")
                    
                img_resized.save(out_path, "JPEG", quality=85)
                count += 1
                
                # พิมพ์แจ้งเตือนทุกๆ 500 รูป จะได้รู้ว่าคอมไม่ค้าง
                if count % 500 == 0:
                    print(f"[-] ย่อเสร็จแล้ว {count} รูป...")
                    
        except Exception as e:
            print(f"[X] รูป {filename} มีปัญหา: {e}")

print(f"✅ ย่อรูปเสร็จสมบูรณ์ทั้งหมด {count} รูป! เข้าไปดูได้ที่: {OUTPUT_FOLDER}")