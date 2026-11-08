# -*- coding: utf-8 -*-
"""
Đếm số liệu quy mô từ 18 file CSV Synthea ĐẦY ĐỦ (việc S1.06; dùng lại được cho S1.04).
- Chỉ ĐỌC file, không sửa file gốc.
- Đọc theo khối (chunk) nên chạy được với file lớn như claims_transactions (~580MB).
- Kết quả: in ra màn hình + lưu 2 file CSV:
    so_lieu_tong_hop.csv  : các con số điền vào báo cáo / tab Số liệu chốt
    quy_mo_18_bang.csv    : số dòng, số cột, dung lượng từng file
Cách chạy: đặt file này CÙNG THƯ MỤC với 18 file CSV, rồi chạy:  python dem_so_lieu.py
"""
import os
import pandas as pd

THU_MUC = os.path.dirname(os.path.abspath(__file__))   # thư mục chứa 18 file CSV (= thư mục của script)
os.chdir(THU_MUC)   # file kết quả cũng được lưu vào thư mục này, dù chạy từ đâu
FILES = ["patients", "encounters", "claims", "claims_transactions", "conditions", "medications",
         "procedures", "observations", "immunizations", "allergies", "careplans", "devices",
         "imaging_studies", "supplies", "organizations", "providers", "payers", "payer_transitions"]
FACT_8 = ["encounters", "claims", "claims_transactions", "conditions", "medications",
          "procedures", "immunizations", "observations"]
DOC = dict(dtype=str, keep_default_na=False, encoding="utf-8-sig")  # đọc dạng chuỗi, bỏ ký tự BOM

def duong_dan(f):
    return os.path.join(THU_MUC, f + ".csv")

# ---------- 1) Quy mô từng file: số dòng, số cột, dung lượng ----------
quy_mo = []
for f in FILES:
    so_cot = len(pd.read_csv(duong_dan(f), nrows=0, **DOC).columns)
    so_dong = sum(len(k) for k in pd.read_csv(duong_dan(f), usecols=[0], chunksize=500_000, **DOC))
    mb = os.path.getsize(duong_dan(f)) / 1024 / 1024
    quy_mo.append({"bang": f, "so_dong": so_dong, "so_cot": so_cot, "dung_luong_MB": round(mb, 1)})
    print(f"{f:22s} {so_dong:>10,} dòng  {so_cot:>3} cột  {mb:>8.1f} MB")
qm = pd.DataFrame(quy_mo)
qm.to_csv("quy_mo_18_bang.csv", index=False, encoding="utf-8-sig")
dong = dict(zip(qm.bang, qm.so_dong))

# ---------- 2) Các con số cho báo cáo ----------
pat = pd.read_csv(duong_dan("patients"), usecols=["Id", "COUNTY", "CITY", "ZIP"], **DOC)
enc = pd.read_csv(duong_dan("encounters"), usecols=["START", "PATIENT", "ORGANIZATION", "PROVIDER", "ENCOUNTERCLASS"], **DOC)
org = pd.read_csv(duong_dan("organizations"), usecols=["Id"], **DOC)
pro = pd.read_csv(duong_dan("providers"), usecols=["Id", "SPECIALITY"], **DOC)
pay = pd.read_csv(duong_dan("payers"), usecols=["NAME"], **DOC)

zip5 = pat.ZIP.str[:5]
so_lieu = [
    ("Số file CSV nguồn", 18, "file", "Đếm file"),
    ("Tổng dung lượng dữ liệu nguồn", round(qm.dung_luong_MB.sum(), 1), "MB", "Tổng dung lượng 18 file"),
    ("Số bệnh nhân", len(pat), "người", "COUNT dòng patients.csv"),
    ("Số bệnh nhân có lượt khám 2023–2025", enc.PATIENT.nunique(), "người", "COUNT DISTINCT encounters.PATIENT"),
    ("Số lượt khám", len(enc), "lượt", "COUNT dòng encounters.csv"),
    ("Ngày lượt khám đầu tiên", enc.START.min()[:10], "", "MIN encounters.START"),
    ("Ngày lượt khám cuối cùng", enc.START.max()[:10], "", "MAX encounters.START"),
    ("Số hạt (county)", pat.COUNTY.nunique(), "hạt", "COUNT DISTINCT patients.COUNTY"),
    ("Số thành phố", pat.CITY.nunique(), "thành phố", "COUNT DISTINCT patients.CITY"),
    ("Số ZIP (5 số, bỏ 00000)", zip5[zip5 != "00000"].nunique(), "ZIP", "COUNT DISTINCT 5 số đầu patients.ZIP"),
    ("Số bệnh nhân có ZIP = 00000", int((zip5 == "00000").sum()), "người", "Lỗi dữ liệu, ghi vào EDA"),
    ("Số cơ sở y tế", len(org), "cơ sở", "COUNT dòng organizations.csv"),
    ("Số cơ sở có lượt khám", enc.ORGANIZATION.nunique(), "cơ sở", "COUNT DISTINCT encounters.ORGANIZATION"),
    ("Số bác sĩ", len(pro), "bác sĩ", "COUNT dòng providers.csv"),
    ("Số bác sĩ có lượt khám", enc.PROVIDER.nunique(), "bác sĩ", "COUNT DISTINCT encounters.PROVIDER"),
    ("Số chuyên khoa", pro.SPECIALITY.nunique(), "chuyên khoa", "COUNT DISTINCT providers.SPECIALITY"),
    ("Số loại lượt khám (encounter class)", enc.ENCOUNTERCLASS.nunique(), "loại", "COUNT DISTINCT encounters.ENCOUNTERCLASS"),
    ("Số hãng bảo hiểm (kể cả NO_INSURANCE)", len(pay), "hãng", "COUNT dòng payers.csv"),
    ("Số dòng claims_transactions", dong["claims_transactions"], "dòng", "COUNT dòng"),
    ("Số dòng 8 fact được chọn", sum(dong[f] for f in FACT_8), "dòng", " + ".join(f"{f} {dong[f]:,}" for f in FACT_8)),
]
kq = pd.DataFrame(so_lieu, columns=["so_lieu", "gia_tri", "don_vi", "nguon_cach_tinh"])
kq.to_csv("so_lieu_tong_hop.csv", index=False, encoding="utf-8-sig")
print("\n===== SỐ LIỆU TỔNG HỢP (copy phần này gửi lại) =====")
for r in kq.itertuples():
    gt = f"{r.gia_tri:,}" if isinstance(r.gia_tri, (int, float)) else r.gia_tri
    print(f"{r.so_lieu}: {gt} {r.don_vi}")
print("\nLoại lượt khám:", ", ".join(f"{k} {v:,}" for k, v in enc.ENCOUNTERCLASS.value_counts().items()))