# 手搖飲店 簡易 ERP（Django + SQLite）

## 執行

```bash
pip install -r requirements.txt
python reset_db.py          # 建立資料庫 + 示範資料（會刪除舊的 db.sqlite3 與 erp/migrations/）
python manage.py runserver
```

開啟 http://127.0.0.1:8000/ 登入。

| 帳號 | 密碼 | 角色 | 可使用 |
|---|---|---|---|
| boss | boss123 | 店長 | 全部（點單、庫存叫貨、財會、人資） |
| staff | staff123 | 店員 | 點單、查看庫存 |
| acct | acct123 | 會計 | 點單、財會 |
| admin | admin123 | 超級管理員 | 全部 + /admin/ 後台（管理帳號與群組） |

## 專案結構

```
bubbletea_erp/
├── manage.py / reset_db.py
├── config/                 # settings（SQLite）、總路由
└── erp/                    # 唯一的 app，四大模組都在這裡
    ├── models.py           # 資料表
    ├── services.py         # 下單核心流程（扣庫存 + 寫財會）
    ├── permissions.py      # 角色權限（Django 群組）
    ├── views.py / urls.py  # 頁面邏輯與路由
    ├── templates/erp/      # 前端頁面
    └── management/commands/seed.py   # 示範資料
```

## 四大模組與資料表

| 模組 | 頁面 | 資料表 |
|---|---|---|
| 生產製造 | 庫存（低於安全庫存亮紅燈、一鍵叫貨） | Ingredient、Product、Recipe |
| 行銷 | POS 點單、熱銷排行 | Order、OrderItem |
| 財會 | 營收／進貨成本／毛利／淨利 | Transaction |
| 人資 | 員工工時、結算本月薪資 | Employee、Payroll |

## 模組連動

- **下單** → 依配方扣原物料庫存 → 財會寫入「銷售收入」（庫存不足整單不成立）
- **叫貨** → 補庫存 → 財會寫入「進貨成本」
- **結算薪資** → 產生薪資紀錄 → 財會寫入「薪資支出」
- 毛利 = 營收 − 進貨成本；淨利 = 毛利 − 薪資
