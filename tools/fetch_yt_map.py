# =====================================================================
#  陪你讀聖經 第一遍 → YouTube videoId 對照表產生器  (Google Colab 用)
#  作法：用 playlistItems 抓「整個播放清單」，1 unit / 50 部影片，
#       而非 search（100 units/次），省 quota 也更準。
#
#  用法：
#   1. 貼到 Colab 一個 cell，填入 API_KEY，先跑「STEP 1」列出所有播放清單
#   2. 從印出的清單找到「陪你讀聖經 第一遍」那個 playlistId，填到 SERIES1_PLAYLIST_ID
#   3. 跑「STEP 2」，會輸出 yt_map.json（章節→videoId）並印出覆蓋率
#   4. 把 yt_map.json 丟回給 Claude，或存到 repo 的 data/ 夾
# =====================================================================
import re, json, urllib.request, urllib.parse

API_KEY              = "填入你的_YOUTUBE_DATA_API_KEY"
CHANNEL_HANDLE       = "@jam2939"

# 第一遍 = 標題剛好以《陪你讀聖經》結尾的播放清單（排除 2/3 遍、特別篇、週末親近神…）
SERIES1_SUFFIX       = "《陪你讀聖經》"

API = "https://www.googleapis.com/youtube/v3/"

def get(endpoint, **params):
    params["key"] = API_KEY
    url = API + endpoint + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url) as r:
        return json.load(r)

def resolve_channel_id(handle):
    # handle 形如 @jam2939
    d = get("channels", part="id,contentDetails", forHandle=handle.lstrip("@"))
    if not d.get("items"):
        d = get("search", part="snippet", q=handle, type="channel", maxResults=1)
        return d["items"][0]["snippet"]["channelId"]
    return d["items"][0]["id"]

# ---------- STEP 1：列出頻道所有播放清單 ----------
def list_playlists():
    cid = resolve_channel_id(CHANNEL_HANDLE)
    print("channelId =", cid, "\n")
    token, n = None, 0
    while True:
        d = get("playlists", part="snippet,contentDetails",
                channelId=cid, maxResults=50, pageToken=token or "")
        for it in d["items"]:
            n += 1
            print(f'{it["contentDetails"]["itemCount"]:>4}部  {it["id"]}  {it["snippet"]["title"]}')
        token = d.get("nextPageToken")
        if not token:
            break
    print(f"\n共 {n} 個播放清單。找到「陪你讀聖經 第一遍」的 id 後，填到 SERIES1_PLAYLIST_ID，再跑 STEP 2。")

# ---------- 章節標題解析 ----------
# 標題格式例：「歷代志下8章/陪你讀聖經《其實你知道，這樣可能不太好》」
#            「詩篇119篇/陪你讀聖經...」、「腓利門書/陪你讀聖經...」
def parse_chapter_key(title):
    ref = title.split("/")[0].strip()           # 取「/陪你讀聖經」前面
    ref = re.sub(r"\s+", "", ref).replace("第", "")  # 去空白、去「第」
    m = re.match(r"^([^\d（(]+?)(\d+)?(?:[章篇])?(?:[（(].*)?$", ref)
    if not m:
        return None
    book, num = m.group(1), m.group(2)
    return f"{book}{num}" if num else book      # 例：歷代志下8 / 詩篇119 / 腓利門書

# ---------- STEP 2：自動抓「所有第一遍」播放清單 → 對照表 ----------
def series1_playlists():
    cid = resolve_channel_id(CHANNEL_HANDLE)
    out, token = [], None
    while True:
        d = get("playlists", part="snippet,contentDetails",
                channelId=cid, maxResults=50, pageToken=token or "")
        for it in d["items"]:
            t = it["snippet"]["title"]
            if t.endswith(SERIES1_SUFFIX):          # 剛好結尾《陪你讀聖經》
                out.append((it["id"], t))
        token = d.get("nextPageToken")
        if not token:
            break
    return out

def items_of(pid):
    token = None
    while True:
        d = get("playlistItems", part="snippet,contentDetails",
                playlistId=pid, maxResults=50, pageToken=token or "")
        for it in d["items"]:
            yield it["snippet"]["title"], it["contentDetails"]["videoId"]
        token = d.get("nextPageToken")
        if not token:
            break

def build_map():
    pls = series1_playlists()
    print(f"找到 {len(pls)} 個第一遍播放清單，開始抓取…")
    ymap, dup = {}, []
    for pid, ptitle in pls:
        for title, vid in items_of(pid):
            if title in ("Private video", "Deleted video"):
                continue
            key = parse_chapter_key(title)
            if not key:
                continue
            if key in ymap and ymap[key] != vid:
                dup.append((key, title))            # 同章多部，保留第一個
            else:
                ymap.setdefault(key, vid)
    json.dump(ymap, open("yt_map.json", "w"), ensure_ascii=False, indent=0)
    print(f"完成：{len(ymap)} 章 → yt_map.json")
    if dup:
        print(f"（{len(dup)} 章重複，已取第一個）")

    # 覆蓋率檢查：目前網站需要的 靈修章節（5-6月）
    need = ["雅各書4","雅各書5"] + [f"歷代志上{i}" for i in range(1,30)] \
                                 + [f"歷代志下{i}" for i in range(1,31)]
    miss = [k for k in need if k not in ymap]
    print(f"靈修(5-6月) 覆蓋：{len(need)-len(miss)}/{len(need)}")
    if miss:
        print("  缺：", miss)

# =====================================================================
# 執行：直接跑 build_map() 即可（會自動找出所有第一遍播放清單）。
#       想先看頻道所有清單，可改成跑 list_playlists()
# =====================================================================
build_map()
# list_playlists()
