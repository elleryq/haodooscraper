# 匯入 OpenShift 時期的舊資料

本專案原本部署在 OpenShift v2（gear + `mysql-5.5` cartridge），每天由
`.openshift/cron/daily/scraper` 跑爬蟲。`data/` 是當年匯出的備份（不進 git，見 `.gitignore`）。

## data/ 內容

| 檔案 | 內容 | 可否匯入 DB |
|---|---|---|
| `haodooscraper.tar.gz`（106 MB） | 整個 OpenShift gear 的備份（`.env`、log、部署目錄、MySQL datadir、dump） | 可，取其中的 dump |
| `haodoo.7z.001`–`.007`（3.3 GB，2018-03） | 實際下載的電子書檔，3,585 本：epub 3585、updb 3585、mobi 2201、pdb 1087 | 否，是書檔本身 |
| `haodoo_books.json`（1.3 MB） | `get_haodoo_books.py` 的下載清單，10,537 個連結 / 3,615 個書名，欄位只有 `link`、`title`、`volumetype` | 不能直接匯入（缺作者、頁面） |

### tarball 裡和資料庫有關的東西

- `app-root/data/mysql_dump_snapshot.gz`：OpenShift snapshot 時產生的 `mysqldump`，
  MySQL 5.5.52，時間 2017-10-05，解壓後 1.8 MB。**這是匯入的來源。**
- `mysql/data/ibdata1`（338 MB）＋ `haodooscraper/*.frm`：InnoDB 原始 datadir。理論上可用
  `mysql:5.5` 映像掛起來讀，但和 dump 是同一時間點的資料，不需要。
- `app-root/logs/cron_daily.log`：最後一次爬蟲 2017-10-02 完成，`status=0`，資料是完整的。

> ⚠️ tarball 含 `OPENSHIFT_SECRET_TOKEN`、SSH key、DB 帳密與 log，不要提交或公開。

## dump 分析

dump 含兩個資料庫：

1. `haodooscraper`（第 1–117 行）：三張表，schema 與目前 `haodooscraper/model.py` 一致。
2. `mysql` 系統庫（第 118 行起）：MySQL 5.5 的 `user`、`db` 等權限表與密碼雜湊。
   **不可匯入** MySQL 8，會弄壞權限表。

| 資料表 | 筆數 | 與 `model.py` 比對 |
|---|---|---|
| `bookpages` | 3,293 | 相同 |
| `bookvolumes` | 3,519 | 相同（dump 中 `pageurl` 為 `NOT NULL`，model 未指定，不影響） |
| `volumeexts` | 10,183 | 相同，FK `volumeid` → `bookvolumes._id` |

- 編碼 `utf8`（MySQL 8 稱 utf8mb3）、`utf8_general_ci`，沒有 4-byte 字元，直接匯入即可。
- dump 開頭 `SET FOREIGN_KEY_CHECKS=0`，含 `DROP TABLE IF EXISTS`，即使 web 先以
  `create_all` 建了空表也能覆蓋。
- 每張表只有一行 `INSERT`，最大約 1 MB，遠小於 MySQL 8 預設的 `max_allowed_packet`（64 MB）。

## 裁切後的 dump

`docker/initdb/01-haodooscraper.sql.gz` 是從 tarball 的 dump 取出的版本：保留第 1–117 行
（header 與 `haodooscraper`），加上原檔結尾還原 `SET` 的幾行（第 852 行起），去掉 `mysql` 系統庫。

重新產生的方式：

```bash
mkdir -p /tmp/oshift
tar xzf data/haodooscraper.tar.gz -C /tmp/oshift --wildcards '*/app-root/data/mysql_dump_snapshot.gz'
F=$(ls /tmp/oshift/*/app-root/data/mysql_dump_snapshot.gz)
N=$(zcat "$F" | grep -n 'SET TIME_ZONE=@OLD_TIME_ZONE' | cut -d: -f1)   # 852
{ zcat "$F" | sed -n '1,117p'; zcat "$F" | sed -n "${N},\$p"; } | gzip -9 > docker/initdb/01-haodooscraper.sql.gz
```

## 用 Docker 啟動

```bash
docker compose up -d --build          # db (MySQL 8.4) + web，第一次啟動會自動匯入 dump
open http://127.0.0.1:8000/           # 搜尋頁；API 在 /api/
docker compose run --rm scraper       # 手動重新爬蟲：會先清空所有資料表！
docker compose down -v                # 連同資料 volume 一起刪除；下次 up 會重新匯入
```

- `docker-entrypoint-initdb.d` 只在 `db-data` volume 第一次初始化時執行。要重新匯入，得先 `down -v`。
- 資料庫網址必須以 `/` 結尾（`mysql://haodoo:haodoo@db:3306/`），因為 `model.py` 會直接接上
  `haodooscraper?charset=utf8`。
- `scraper` 放在 `scrape` profile，`up` 不會啟動它。haodoo.net 現在的結構不一定還能爬，
  一旦執行就會清掉匯入的資料。
- 密碼可用環境變數 `MYSQL_ROOT_PASSWORD`、`MYSQL_PASSWORD` 覆寫（預設 `rootpass` / `haodoo`）。
  MySQL 只綁在 `127.0.0.1:3306`。

驗證匯入結果：

```bash
docker compose exec db mysql --default-character-set=utf8mb4 -uhaodoo -phaodoo haodooscraper \
  -e "select count(*) from bookpages; select count(*) from bookvolumes; select count(*) from volumeexts;"
# 3293 / 3519 / 10183
```

## 可選的後續工作

- 把三張表從 utf8mb3 轉成 utf8mb4（`ALTER TABLE ... CONVERT TO CHARACTER SET utf8mb4`），
  連線字串的 `charset=utf8` 也要一起改。
- 用 `haodoo_books.json`（2018 年，較新）補上 dump 沒有的書（約 100 本）：從 `link` 的
  `P=D438.updb` 可解析出 volume id `D438`（mobi 為 `DV438`），但缺作者與頁面資訊。
