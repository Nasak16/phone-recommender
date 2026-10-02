# วิธี deploy ระบบขึ้น Streamlit Community Cloud (ฟรี — ไม่ต้องใช้บัตรเครดิต)

ใช้ repo ของโปรเจกต์นี้ตรง ๆ ไม่ต้องแก้โค้ด เพราะแอปเลือก backend เองอัตโนมัติ

## 1) แอปใช้ Neo4j จริงเท่านั้น (ไม่มีโหมดข้อมูลจำลอง)
- ถ้ายังไม่ได้ตั้งค่า secrets หรือต่อฐานข้อมูลไม่ได้ แอปจะขึ้น **หน้าวิธีตั้งค่า** (บอกทั้งแบบในเครื่อง
  และแบบ Aura + ปุ่ม "ลองเชื่อมต่อใหม่") ไม่แสดงข้อมูลปลอมให้เข้าใจผิด
  ตรวจพฤติกรรมนี้ได้ด้วย `py -3.13 tools/test_needs_neo4j.py`
- ฐานข้อมูลว่างก็เปิดได้ไม่พัง: ทุกหน้าขึ้น 0 แล้วชี้ไปที่ปุ่ม **🔄 รีโหลดข้อมูลตัวอย่าง** ในหน้า Admin & Setup
- `graph_fallback.py` ยังอยู่ในโปรเจกต์ แต่ใช้ **เพื่อพิสูจน์ว่าสูตรให้คะแนนใน Cypher ถูก** เท่านั้น
  (`tools/consistency_test.py` เทียบ 2 ด้านทุกผู้ใช้) ไม่ได้ถูกใช้เป็นข้อมูลของแอปแล้ว

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

## 3) ต่อ Neo4j จริง (Neo4j Aura Free) ให้แอปบนคลาวด์ใช้ฐานข้อมูลกราฟ
คลาวด์เข้าถึง Neo4j ที่รันในเครื่องเราไม่ได้ จึงต้องใช้ **Aura Free** (ฟรี, ไม่ต้องใส่บัตรเครดิต)

1. สมัคร/เข้า https://console.neo4j.io → **New instance** → เลือก **Free**
   (region สิงคโปร์จะเร็วที่สุดสำหรับไทย) → กด **Create**
2. คัดลอกค่าจากหน้า instance (รหัสผ่านจะโชว์ครั้งเดียว — เก็บให้ดี)
   - URI: `neo4j+s://xxxxxxxx.databases.neo4j.io`
   - User: `neo4j` · Database: `neo4j` · Password: (คัดลอกไว้)
3. ใส่ค่าให้แอปบนคลาวด์: หน้าแอปใน share.streamlit.io → เมนู **⋮** → **Settings** → **Secrets**
   วางทับด้วย

   ```toml
   NEO4J_URI = "neo4j+s://xxxxxxxx.databases.neo4j.io"
   NEO4J_USER = "neo4j"
   NEO4J_PASSWORD = "รหัสของ instance"
   NEO4J_DATABASE = "neo4j"
   ```

   กด **Save** (แอปจะรีสตาร์ทเอง ~1 นาที) — **ห้าม commit รหัสลง repo เด็ดขาด**
4. โหลดข้อมูลเข้า Aura: เปิดแอป → หน้า **Admin & Setup** → กด **🔄 รีโหลดข้อมูลตัวอย่าง**
   (ใช้ `MERGE` ทั้งหมด กดซ้ำได้) → ตัวเลขทุกหน้าจะขึ้น 12 ผู้ใช้ / 23 รุ่น / 38 ความสนใจ + คะแนนดาว
   - หรือรันจากเครื่อง: `py -3.13 tools/load_neo4j.py "neo4j+s://..." neo4j <รหัส> neo4j`
5. ตรวจว่าต่อจริง: แถบข้างจะขึ้น `ฐานข้อมูล: Neo4j (neo4j+s://…)` — ถ้าต่อไม่ได้จะขึ้นหน้าวิธีตั้งค่าแทน

**ข้อควรรู้**
- Aura Free **หลับเมื่อไม่ใช้งาน 3 วัน** → เปิดแอปครั้งแรกอาจรอ ~20–30 วินาที
  (โค้ดตั้ง timeout 30 วิ + ลองซ้ำ 3 ครั้งให้แล้ว)
- Aura Free มีฐานข้อมูลเดียวชื่อ `neo4j` — ถ้าใส่ชื่ออื่น (เช่น `phones` ของเซิร์ฟเวอร์ในเครื่อง)
  โค้ดจะสลับไปใช้ฐานข้อมูลเริ่มต้นให้เอง แล้วขึ้นข้อความอธิบายในแถบข้าง
- ฐานข้อมูลว่างเปล่าก็เปิดแอปได้ไม่พัง: ทุกหน้าจะขึ้น 0 และมีข้อความชี้ไปที่ปุ่มโหลดข้อมูลใน Admin
- เข้าเครื่องตนเอง: Neo4j Desktop/Community + `NEO4J_DATABASE=phones` ใน `.streamlit/secrets.toml`
  (ไฟล์นี้อยู่ใน `.gitignore` แล้ว)

## 4) ลิงก์สำหรับนำเสนอ
- เดโมออนไลน์: ลิงก์ `*.streamlit.app` ของเรา
- ลิงก์รวมงานทุกชิ้น: https://nasak16.github.io/homework/
- โน๊ตบุ๊กอธิบายวิธีทำ: ปุ่ม Open in Colab ใน README
- ทดสอบว่าแอปบังคับใช้ Neo4j จริง: `py -3.13 tools/test_needs_neo4j.py` (ดูวิธีในหัวไฟล์)
- พิสูจน์ว่าสูตรใน Cypher ถูก: `py -3.13 tools/consistency_test.py <uri> neo4j <รหัส> phones`
