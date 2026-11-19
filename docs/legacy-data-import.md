# 匯入 OpenShift 時期的舊資料

本專案原本部署在 OpenShift v2（gear + `mysql-5.5` cartridge），每天由
`.openshift/cron/daily/scraper` 跑爬蟲。`data/` 是當年匯出的備份（不進 git，見 `.gitignore`）。

## data/ 內容

| 檔案 | 內容 | 可否匯入 DB |
|---|---|---|
| `haodooscraper.tar.gz`（106 MB） | 整個 OpenShift gear 的備份（`.env`、log、部署目錄、MySQL datadir、dump） | 可，取其中的 dump |
| `haodoo.7z.001`–`.007`（3.3 GB，2018-03） | 實際下載的電子書檔，3,585 本：epub 3585、updb 3585、mobi 2201、pdb 1087。**已損壞**，見下文 | 否，是書檔本身 |
| `haodoo_books.json`（1.3 MB） | `get_haodoo_books.py` 的下載清單，10,537 個連結 / 3,615 個書名，欄位只有 `link`、`title`、`volumetype` | 已用來補書，見「用 haodoo_books.json 補書」 |

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
docker compose up -d --build          # db (MySQL 8.4) + web，第一次啟動會自動匯入 01、02
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
# 3414 / 3641 / 10568（只有 01 的話是 3293 / 3519 / 10183）
```

## 用 haodoo_books.json 補書

`haodoo_books.json`（2018-03）比 dump（2017-10）新。`docker/initdb/02-haodoo-books-2018.sql`
會在 01 之後執行，補上 dump 沒有的資料：

| | 筆數 |
|---|---|
| 新頁面 `bookpages` | 121 |
| 新書 `bookvolumes` | 122（都是 `17xx` 系列，2017-10 之後上架） |
| 新下載連結 `volumeexts` | 385 = 新書的 366 + 既有書後來補上的 19 個 mobi |

匯入後總數為 3414 / 3641 / 10568。json 的其餘 10,152 個連結和 dump 完全一致，同一 volume 的書名也都相符。

### 欄位如何推導

json 只有下載連結，其他欄位由連結推出。推導規則都先對 dump 裡既有的 3,519 筆驗證過：

- **volume id**：`P=<字首>[V]<編號>.<副檔名>`，mobi 會在字首後多一個 `V`。
  例：`D438.epub`、`DV438.mobi` → `D438`。
- **bookid**：去掉字首；多冊套書結尾的小寫字母也去掉，對應同一頁。
  例：`D17XZa` → `17XZ`、`H17T8a`/`H17T8b` → `17T8`。
- **pageurl**：字首 `I`、`HQ*` 是 `?M=Share&P=`，`A`–`H` 是 `?M=book&P=`
  （本次新增的全是 `A`–`H`）。
- **author**：json 沒有作者，存空字串（存 NULL 的話頁面會顯示 `None`）。新頁面的 `title` 也留空，
  dump 裡多數頁面一樣是空的。

本來打算從 7z 裡 epub 的 metadata 取作者，但壓縮檔已損壞：三個 solid block 都在中途出現
`Data Error`（block 2 從第一個檔案就壞），`7z t` 結果是 10,462 個檔案只有 1,207 個能解出來，
新書的 epub 一本都拿不到。若有其他完好的備份，可以再補作者。

### 重新產生

```bash
docker compose down -v && docker compose up -d db        # 只匯入 01（先暫時移開 02）
OPENSHIFT_MYSQL_DB_URL=mysql://haodoo:haodoo@127.0.0.1:3306/ \
  uv run python scripts/haodoo_books_to_sql.py data/haodoo_books.json \
  > docker/initdb/02-haodoo-books-2018.sql
```

腳本只輸出 DB 裡還沒有的資料，對已補齊的 DB 執行會得到 0 筆。產生的 SQL 用 volume id
（不是 `_id`）找對應的書，所以只要 DB 有 2017 的 dump 就能套用，但同一份 SQL 不能重複執行。

## 可選的後續工作

- 把三張表從 utf8mb3 轉成 utf8mb4（`ALTER TABLE ... CONVERT TO CHARACTER SET utf8mb4`），
  連線字串的 `charset=utf8` 也要一起改。
- 找到完好的書檔備份後，從 epub 的 `dc:creator` 補上 122 本新書的作者。
