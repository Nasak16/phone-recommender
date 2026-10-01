# ตั้ง Neo4j ในเครื่องสำหรับทดสอบ (Windows, ไม่ต้องใช้ Docker / ไม่ต้องสิทธิ์ admin)

ใช้ไฟล์ที่ **Neo4j Desktop 2** แคชไว้แล้วในเครื่อง (`~/.Neo4jDesktop2/Cache/dbmss`) จึงไม่ต้องโหลดใหม่

```bash
NX="$TMPDIR/nx"; rm -rf "$NX"; mkdir -p "$NX"
cp -r "$USERPROFILE/.Neo4jDesktop2/Cache/dbmss/neo4j-enterprise-2026.08.1/." "$NX/"

export JAVA_HOME='C:\Users\USER\.Neo4jDesktop2\Cache\runtime\zulu21.50.19-ca-jre21.0.11-win_x64'
export PATH="/c/Users/USER/.Neo4jDesktop2/Cache/runtime/zulu21.50.19-ca-jre21.0.11-win_x64/bin:$PATH"
export NEO4J_ACCEPT_LICENSE_AGREEMENT=yes

cd "$NX/bin" && ./neo4j-admin.bat dbms set-initial-password phonerec007
./neo4j.bat console      # รอข้อความ "Started." ในไฟล์ logs/neo4j.log
```

## แยกฐานข้อมูลไว้ต่างหาก (ไม่ทับข้อมูลโปรเจกต์อื่น)
```bash
./cypher-shell.bat -a bolt://127.0.0.1:7687 -u neo4j -p phonerec007 \
  "CREATE DATABASE phones IF NOT EXISTS"
```

## โหลดข้อมูลและตรวจสอบ
```bash
py -3.13 tools/load_neo4j.py bolt://127.0.0.1:7687 neo4j phonerec007 phones
py -3.13 tools/consistency_test.py bolt://127.0.0.1:7687 neo4j phonerec007 phones
```

## รันแอป
```bash
py -3.13 -m streamlit run app.py     # ตั้งค่าให้ใช้พอร์ต 8779
```
ถ้าเชื่อมต่อ Neo4j ไม่ได้ แอปจะสลับไปใช้ backend สำรองในหน่วยความจำอัตโนมัติ

## หมายเหตุที่เจอจริง
- **Neo4j 2026.x ต้องใช้ Java 21** (Java 8 ของเครื่องจะได้ UnsupportedClassVersionError)
- รันสคริปต์ซ้ำได้ — `tools/load_neo4j.py` ล้างข้อมูลเดิมก่อนโหลดทุกครั้ง
- ถ้าใช้ **Aura** ให้ตั้ง `NEO4J_URI=neo4j+s://<id>.databases.neo4j.io` และ `NEO4J_DATABASE=neo4j`
