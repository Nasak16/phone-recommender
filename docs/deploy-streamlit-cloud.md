# วิธี deploy ระบบขึ้น Streamlit Community Cloud (ฟรี — ไม่ต้องใช้บัตรเครดิต)

ใช้ repo ของโปรเจกต์นี้ตรง ๆ ไม่ต้องแก้โค้ด เพราะแอปเลือก backend เองอัตโนมัติ

## 1) เปิดแอปด้วยข้อมูลชุดเดิม โดยไม่ต้องมีเซิร์ฟเวอร์ Neo4j
- ถ้าไม่มีค่า secrets ของ Neo4j แอปจะสลับไป **โหมดสาธิตในหน่วยความจำของเซสชัน**
  ใช้ข้อมูลชุดเดียวกับที่โหลดเข้า Neo4j (12 ผู้ใช้ / 23 รุ่น / 38 ความสนใจ)
  และผลการให้คะแนนผ่านการทดสอบว่าตรงกับ Cypher แล้ว (`tools/consistency_test.py`)
- การกด "เพิ่ม/ลบความสนใจ" ในหน้าเดโมสดจะแก้ข้อมูล **เฉพาะผู้เข้าชมคนนั้น** ไม่รบกวนคนอื่น

## 2) ขั้นตอน deploy (4 คลิก)
1. เข้า https://share.streamlit.io แล้ว **Sign in with GitHub** (บัญชี `Nasak16`)
2. กด **Create app** → **Deploy a public app from GitHub**
3. กรอก
   - Repository: `Nasak16/phone-recommender`
   - Branch: `main`
   - Main file path: `app.py`
   - App URL (ตั้งชื่อซับโดเมนได้เอง เช่น `phone-recommender-007`)
4. กด **Deploy** → รอ build 1–3 นาที → ได้ลิงก์ถาวร `https://<ชื่อ>.streamlit.app`

## 2.1) แก้ error "health check ... 8501: connection refused" (สำคัญมาก)
Streamlit Cloud ตรวจสุขภาพแอปที่พอร์ต **8501** เสมอ ถ้าไฟล์ `.streamlit/config.toml`
ที่ commit ขึ้นไปตั้ง `[server] port = 8779` (แบบที่ใช้รันในเครื่อง) cloud จะสตาร์ทแอปที่ 8779
แล้วขึ้น `❗ The service has encountered an error while checking the health of the Streamlit app`

**วิธีแก้:** อย่า pin `port` ในไฟล์ที่ commit — ให้ระบุพอร์ตตอนรันในเครื่องผ่าน command line แทน

```bash
py -3.13 -m streamlit run app.py --server.port 8783     # ในเครื่อง
```

ไฟล์ `.streamlit/config.toml` ใน repo นี้ตั้งไว้แค่ธีม + headless เท่านั้น
(ถ้าแก้แล้วยังไม่หาย ให้กด **Reboot app** ที่หน้าแอปใน share.streamlit.io อีกครั้ง)

## 3) ถ้าต้องการต่อ Neo4j จริง (ไม่บังคับ)
สร้าง Neo4j Aura (free tier) แล้วใส่ใน **Settings → Secrets** ของแอป:

```toml
NEO4J_URI = "neo4j+s://xxxxxxxx.databases.neo4j.io"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "รหัสของ instance"
NEO4J_DATABASE = "neo4j"
```

แอปจะสลับไปใช้ฐานข้อมูลกราฟให้เองโดยไม่ต้องแก้โค้ด (ตรวจสถานะได้ที่แท็บ "เกี่ยวกับระบบ")
โหลดข้อมูลขึ้น Aura ด้วย `py -3.13 tools/load_neo4j.py <uri> neo4j <password> neo4j`

## 4) ลิงก์สำหรับนำเสนอ
- เดโมออนไลน์: ลิงก์ `*.streamlit.app` ของเรา
- ลิงก์รวมงานทุกชิ้น: https://nasak16.github.io/homework/
- โน๊ตบุ๊กอธิบายวิธีทำ: ปุ่ม Open in Colab ใน README
- ทดสอบโหมด cloud ก่อนได้ในเครื่อง: `py -3.13 tools/test_deploy_mode.py` (ดูวิธีในหัวไฟล์)
