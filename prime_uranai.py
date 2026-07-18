import json
import random
import datetime
import urllib.request
import urllib.error  # 🚨 エラーの詳細を解剖するための道具
import os  # 🔑 秘密の引き出し（環境変数）を使うための道具
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 🏢 サーバー（API）の本体を起動！
app = FastAPI()

# 🌐 【防壁1】通信をジェイのGitHub Pagesとローカルファイルに限定
ALLOWED_ORIGINS = [
    "https://tanakaisao.github.io",  # 正規のGitHub Pages
    "null"                           # パソコンの黒い画面（ローカルファイル）からの通信
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,   # 💡 上で作った2つの名簿を指定するべさ
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)

# 📥 フロント（HTML）から送られてくる誕生日データの受け皿（現代文・古文用）
class BirthdayRequest(BaseModel):
    month: int
    day: int

# 📥 【新設】今日の運勢用：実験用の「今日の日付」も一緒に受け取る器だべさ！
class TodayUranaiRequest(BaseModel):
    month: int       # 誕生月
    day: int         # 誕生日
    today_month: int # 【実験用】今日の月
    today_day: int   # 【実験用】今日の日


# 🧮 素因数分解の計算マシン
def prime_factors(n):
    factors = []
    d = 2
    temp = n
    while d * d <= temp:
        while (temp % d) == 0:
            factors.append(d)
            temp //= d
        d += 1
    if temp > 1:
        factors.append(temp)
    return factors


# =====================================================================
# 🔮 部屋1：格式高い「古文調」占い（完全無傷！）
# =====================================================================
@app.post("/uranai_kobun")
async def get_fortune_kobun(req: BirthdayRequest, request: Request):
    check_robot(request)
    return execute_gemini_uranai(req, style="kobun")


# =====================================================================
# 🔮 部屋2：新設！親しみやすい「現代文」占い（完全無傷！）
# =====================================================================
@app.post("/uranai_gendai")
async def get_fortune_gendai(req: BirthdayRequest, request: Request):
    check_robot(request)
    return execute_gemini_uranai(req, style="gendai")


# =====================================================================
# 🔮 部屋3：【新登場！】今日の素因数ジャンプ占い（ジェミニの真骨頂！）
# =====================================================================
@app.post("/uranai_today")
async def get_fortune_today(req: TodayUranaiRequest, request: Request):
    check_robot(request)  # 🛡️ ロボットチェックも共通でバチッと機能！
    
    try:
        # 1. 数字の仕込み
        b_num = req.month * 100 + req.day        # 誕生日の月日（例: 1015）
        t_num = req.today_month * 100 + req.today_day # 今日の月日（例: 718）
        total_num = b_num + t_num                # 合体数（例: 1733）
        
        # 2. ジェイのアイデア通り、2つの素因数分解を別々に実行！
        b_factors = prime_factors(b_num)
        total_factors = prime_factors(total_num)
        
        # 式の文字列を作っておくべさ
        b_formula = f"{b_num} ＝ 【 素数 】" if len(b_factors) == 1 else f"{b_num} ＝ {' × '.join(map(str, b_factors))}"
        total_formula = f"{total_num} ＝ 【 素数 】" if len(total_factors) == 1 else f"{total_num} ＝ {' × '.join(map(str, total_factors))}"
        
        # 🔑 Renderの環境変数からAPIキー取得
        api_key = os.getenv("GEMINI_API_KEY")
        
        # 📜 今日の運勢専用プロンプト（2つの素因数の物語を紡ぐ）
        prompt = f"""
あなたは数学の神秘とユーモアを愛する、親しみやすい凄腕の占い師（北海道弁混じり）だべさ。
以下の「2つの素因数分解データ」を深く読み解き、今日の運勢をドラマチックに占っておくれ。

【対象データ】
・占う人の誕生日：{req.month}月{req.day}日 (数式：{b_formula})
・占う日の日付：{req.today_month}月{req.today_day}日
・合体させた数字 ({b_num} ＋ {t_num} ＝ {total_num}) の数式：{total_formula}

【占いのストーリー設計ルール】
1. もし「誕生日」と「占う日の日付」が同じ（誕生日当日）なら、合計数は元の2倍になり、絶対に新たな素因数「2」が加わります。その時は「1年に1度、あなたのベースの素数に『2』の祝福が重なる奇跡の日だべさ！」と大絶賛して熱くお祝いしてください。
2. 普段の日であれば、誕生日の素因数（その人のDNA）と、今日の合計数の素因数を比べ、「同じ素数があって共鳴している」「今日は巨大な素数がドカンと現れたから大勝負の時だべさ」「2や3が細かく並んだからバランスが良いわ」など、数学的なシンクロニシティを楽しく前向きに解説してください。
3. 語尾は「〜だべさ」「〜だわ」「〜おくれ」「〜だもね」など、親しみやすい北海道のトーンにしてください。
4. 文字数は250文字〜400文字程度とし、読んだ人がワクワクして今日1日を元気に過ごせる文章にしてください。
"""

        # 🚀 Gemini API へ通信（新しめのモデル名「gemini-2.5-flash」をそのまま踏襲）
        api_url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        
        data = json.dumps(payload).encode("utf-8")
        req_obj = urllib.request.Request(api_url, data=data, headers=headers, method="POST")
        
        with urllib.request.urlopen(req_obj) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            ai_text = res_data["candidates"][0]["content"]["parts"][0]["text"]
            
            return {
                "formula": f"誕生日:{b_formula} / 今日との合体数:{total_formula}",
                "fortune": ai_text
            }

    except urllib.error.HTTPError as http_err:
        if http_err.code == 429:
            return {
                "formula": "本日分は終了だべさ",
                "fortune": "本日の占いは大盛況のため売り切れだべさ！無料枠の制限に達したから、また明日おいで！"
            }
        else:
            return {
                "formula": f"お休み中（コード: {http_err.code}）",
                "fortune": "ちょっとGoogleのAIが考え込んでるみたいだべさ。少し時間を空けて試してみておくれ。"
            }
            
    except Exception as e:
        return {
            "formula": "エラーだべさ",
            "fortune": "ちょっと調子が悪いみたいだべさ。時間を空けてもう一度ボタンを押してみておくれ。"
        }


# =====================================================================
# 🛡️ 【防壁2】怪しい自動プログラム（ロボット）を検知して叩き落とす関数
# =====================================================================
def check_robot(request: Request):
    headers = request.headers
    user_agent = headers.get("user-agent", "").lower()
    sec_fetch_site = headers.get("sec-fetch-site", "").lower()
    
    is_robot_agent = not user_agent or any(x in user_agent for x in ["python", "curl", "wget", "httpclient", "bot", "crawl"])
    if is_robot_agent or (sec_fetch_site and sec_fetch_site not in ["cross-site", "same-site"]):
        raise HTTPException(status_code=403, detail="Access denied for automated systems.")
