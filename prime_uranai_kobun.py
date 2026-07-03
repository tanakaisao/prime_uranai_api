import json
import random
import datetime
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 🏢 サーバー（API）の本体を起動！
app = FastAPI()

# 🌐 インターネット上のどこからでもアクセスできるようにする魔法の設定（CORS設定）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ジェイのGitHubページからの通信を優しく受け入れるべさ
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📥 フロント（HTML）から送られてくる「誕生日データ」の受け皿を定義
class BirthdayRequest(BaseModel):
    month: int
    day: int

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

# 🔮 ここがメインの占いアタックポイント（/uranai というURLで通信を待つべさ）
@app.post("/uranai")
def get_fortune(req: BirthdayRequest):
    try:
        # 1. データの取り出しと計算
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
            
        # 🔑 サーバーの中だから、APIキーをそのまま1列で堂々と書いても「絶対に誰にも見えない」べさ！
        # これぞ完全なる安全地帯！
        api_key = "AIzaSyC8Q06Ooq44zh7qv5EJbCmyWvv-EEY3Y5U"
        
        # 🎲 乱数の仕掛け（これまでと全く同じロジックを継承）
        today_num = int(datetime.date.today().strftime('%Y%m%d'))
        fortune_seed = today_num + target_num
        random.seed(fortune_seed)
        
        weekdays = ["日曜日", "月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日"]
        todays_guardian_weekday = random.choice(weekdays)
        todays_guardian_day = random.randint(1, 31)
        
        # 🧠 ジェイ渾身の「深淵古文調プロンプト」
        prompt = f"""
あなたは世界の理を数式から読み解く、深淵で知的な「素因数分解占い師」です。
ユーザーの誕生日から導かれた数字「{target_num}」と、その素因数分解の結果「{formula_str}」が持つ固有の波動を読み解き、その人物の運勢や本質、性格を格式高く、謎めいた表現（古文調の美しい日本語）で占ってください。

【占いの掟】
1. くだけた口調や俗世の固有名詞は一切使わないでください。神秘のベールに包まれた厳かな、しかしどこか美しく豊かな語彙で語りかけてください。
2. 数字の構成から得られるインスピレーションを言葉に宿らせてください。
   - 素数の場合：他者の介入を拒む絶対的なアイデンティティ、孤高の天才、変革をもたらすカリスマ。
   - 2や5などの偶数や馴染み深い調和の数が多い場合：多面的な社交性、万物と融和する卓越したコミュニケーションの才、周囲を惹きつける中心人物。
   - 3や7、また大きな奇数（43など）が含まれる場合：鋭利な知性、密かなこだわりを持つクリエイターとしての資質、深層の美意識。
3. 漢数字（一、二、百など）は横書きで読みづらいため、一切使わないでください。数字を表現する場合は、必ず【半角の算用数字（2、5、43など）】を使用してください。
4. 文字数は250文字〜400文字程度とし、読む者を納得の深みへと誘う文章にしてください。
5. 文末には、星々の巡りが告げる今期の守護として、以下の「指定された曜日」と「指定された日にち」を厳かに宣告してください。これら以外の数字や素数を勝手に創作してはいけません。

【今期お前に授ける守護の刻印（必ず文末に含めること）】
・守護の曜日：{todays_guardian_weekday}
・守護の日にち：{todays_guardian_day}日

対象データ：
誕生日：{m_str}月{d_str}日
数式データ：{ai_hint}
"""

        # 🚀 Gemini API へ通信
        api_url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        
        response = requests.post(api_url, headers=headers, json=payload)
        
        if response.status_code == 200:
            res_data = response.json()
            ai_text = res_data["candidates"][0]["content"]["parts"][0]["text"]
            
            # 🎁 フロント（HTML）に返す「大成功セット」
            return {
                "formula": formula_str,
                "fortune": ai_text
            }
        else:
            raise HTTPException(status_code=response.status_code, detail="Geminiとの通信に失敗したべさ")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
