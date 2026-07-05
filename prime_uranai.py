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

# 🌐 【防壁1】通信をジェイのGitHub Pagesだけに限定
# ⚠️ [ジェイのGitHubユーザー名] を実際のユーザー名に書き換えておくれ！
ALLOWED_ORIGIN = "https://tanakaisao.github.io"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)

# 📥 フロント（HTML）から送られてくる誕生日データの受け皿
class BirthdayRequest(BaseModel):
    month: int
    day: int

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
# 🔮 部屋1：格式高い「古文調」占い
# =====================================================================
@app.post("/uranai")
async def get_fortune_kobun(req: BirthdayRequest, request: Request):
    check_robot(request)
    return execute_gemini_uranai(req, style="kobun")


# =====================================================================
# 🔮 部屋2：新設！親しみやすい「現代文」占い
# =====================================================================
@app.post("/uranai_gendai")
async def get_fortune_gendai(req: BirthdayRequest, request: Request):
    check_robot(request)
    return execute_gemini_uranai(req, style="gendai")


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


# =====================================================================
# 👑 Gemini突撃＆占い生成の共通メカニズム（裏方の仕事人）
# =====================================================================
def execute_gemini_uranai(req: BirthdayRequest, style: str):
    try:
        m_str = str(req.month)
        d_str = str(req.day)
        target_num = req.month * 100 + req.day
        
        factors = prime_factors(target_num)
        
        if len(factors) == 1:
            formula_str = f"{target_num} ＝ 【 素数 】"
            ai_hint = f"{target_num}は他のいかなる数にも割り切れない「素数」です。"
        else:
            formula_str = f"{target_num} ＝ {' × '.join(map(str, factors))}"
            ai_hint = f"{target_num}の素因数分解は {' × '.join(map(str, factors))} です。"
            
        # 🔑 Renderの「秘密の引き出し」から、ジェイの最強AQキーを自動取得！
        api_key = os.getenv("GEMINI_API_KEY")
        
        # 🎲 乱数の仕掛け（曜日と日にちの守護）
        today_num = int(datetime.date.today().strftime('%Y%m%d'))
        fortune_seed = today_num + target_num
        random.seed(fortune_seed)
        
        weekdays = ["日曜日", "月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日"]
        todays_guardian_weekday = random.choice(weekdays)
        todays_guardian_day = random.randint(1, 31)
        
        # 📜 スタイルによってプロンプト（AIへの命令書）を切り替える
        if style == "kobun":
            prompt = f"""
あなたは世界の理を数式から読み解く、深淵で知的な「素因数分解占い師」です。
ユーザーの誕生日から導かれた数字「{target_num}」と、その素因数分解の結果「{formula_str}」が持つ固有の波動を読み解き、その人物の運勢や本質、性格を格式高く、謎めいた表現（古文調の美しい日本語）で占ってください。

【占いの掟】
1. くだけた口調や俗世の固有名詞は一切使わないでください。神秘のベールに包まれた厳かな、しかしどこか美しく豊かな語彙で語りかけてください。
2. 数字の構成から得られるインスピレーションを言葉に宿らせてください。
3. 漢数字は一切使わないでください。数字を表現する場合は、必ず【半角の算用数字（2、5、43など）】を使用してください。
4. 文字数は250文字〜400文字程度とし、読む者を納得の深みへと誘う文章にしてください。
5. 文末には、星々の巡りが告げる今期の守護として、以下の「指定された曜日」と「指定された日にち」を厳かに宣告してください。

【今期お前に授ける守護の刻印（必ず文末に含めること）】
・守護の曜日：{todays_guardian_weekday}
・守護の日にち：{todays_guardian_day}日

対象データ：
誕生日：{m_str}月{d_str}日
数式データ：{ai_hint}
"""
        else:
            prompt = f"""
あなたは世界の理を数式から読み解く、知的で親しみやすい現代の「素因数分解占い師」です。
ユーザーの誕生日から導かれた数字「{target_num}」と, その素因数分解の結果「{formula_str}」が持つ意味を分かりやすく分析し、その人の運勢や本質、性格を、前向きで元気が出る現代の言葉（丁寧な標準語）で占ってください。

【占いの掟】
1. 古風な言い回しは使わず、現代人にスッと伝わる、爽やかで説得力のある優しい口調（「〜です」「〜ます」）で語りかけてください。
2. 数字の構成から得られるインスピレーションを言葉に宿らせてください。
   - 素数の場合：誰にも真似できない強い個性、ブレない信念を持つリーダー、未来を切り開くカリスマ性。
   - 2や5などの偶数や馴染み深い調和の数が多い場合：抜群のコミュニケーション能力、周囲を笑顔にする社交性、チームのバランスを取る天才。
   - 3や7、また大きな奇数（43など）が含まれる場合：独自のセンスを持つクリエイター、鋭い直感と知性、こだわりを形にする力。
3. 数字を表現する場合は、必ず【半角の算用数字（2、5、43など）】を使用してください。
4. 文字数は250文字〜400文字程度とし、読んだ人がワクワクして明日への活力になるような文章にしてください。
5. 文末には、ハッピーを呼び込む今期のラッキーアイテムとして、以下の「指定された曜日」と「指定された日にち」を軽やかに優しく伝えてください。

【今期あなたをハッピーにする守護のサイン（必ず文末に含めること）】
・ラッキーな曜日：{todays_guardian_weekday}
・ラッキーな日にち：{todays_guardian_day}日

対象データ：
誕生日：{m_str}月{d_str}日
数式データ：{ai_hint}
"""

        # 🚀 Gemini API へ通信
        api_url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        
        data = json.dumps(payload).encode("utf-8")
        req_obj = urllib.request.Request(api_url, data=data, headers=headers, method="POST")
        
        with urllib.request.urlopen(req_obj) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            ai_text = res_data["candidates"][0]["content"]["parts"][0]["text"]
            
            return {
                "formula": formula_str,
                "fortune": ai_text
            }

    # 🔬 【超絶強化】Googleからのエラーメッセージの「中身」を徹底的にほじくり返すべさ！
    except urllib.error.HTTPError as http_err:
        try:
            # Googleが返してきた詳細なエラー理由（JSONなど）を読み解く
            error_body = http_err.read().decode("utf-8")
            return {
                "formula": f"HTTPエラー {http_err.code}",
                "fortune": f"Googleからの詳細警告だべさ：\n{error_body}"
            }
        except Exception:
            return {
                "formula": f"HTTPエラー {http_err.code}",
                "fortune": f"通信エラーが発生したべさ。({str(http_err)})"
            }
            
    except Exception as e:
        return {
            "formula": "エラーだべさ",
            "fortune": f"サーバー内部で予期せぬ乱れが発生したべさ。（エラー: {str(e)}）"
        }
