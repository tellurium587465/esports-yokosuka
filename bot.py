"""
YeG VALORANT Bot
────────────────
・/panel   → ランク選択パネルをチャンネルに投稿
・ボタンで自己申告ランクを更新
・高校ロール＋入学年次ロールから学校・学年を自動取得
・データを data.json に保存 → 勢力図サイトから読み込み可能
"""

import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import re
import asyncio
import subprocess
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
TOKEN        = os.getenv("DISCORD_TOKEN")
MY_GITHUB_TOKEN = os.getenv("MY_GITHUB_TOKEN")   # GitHub PAT（repo権限）
MY_GITHUB_REPO  = os.getenv("MY_GITHUB_REPO")    # 例: YourOrg/yeg-website
DATA_FILE    = "data.json"

# ── VALORANT ランク定義 ──────────────────────────────────────
RANKS = [
    ("Iron",       "🪨", "#909090"),
    ("Bronze",     "🥉", "#a06030"),
    ("Silver",     "🥈", "#507a90"),
    ("Gold",       "🥇", "#c09010"),
    ("Platinum",   "🔵", "#0090b0"),
    ("Diamond",    "💎", "#7840c0"),
    ("Ascendant",  "🌿", "#008050"),
    ("Immortal",   "🔴", "#c02040"),
    ("Radiant",    "⭐", "#b08000"),
    ("未申告",     "❓", "#aaaaaa"),
]
RANK_NAMES = [r[0] for r in RANKS]

# ── 対象高校リスト ────────────────────────────────────────────
TARGET_SCHOOLS = [
    "追浜高校",
    "横須賀高校",
    "県立横須賀工業高校",
    "横須賀大津高校",
    "横須賀学院高校",
    "横須賀総合高校",
    "三浦学苑高校",
    "湘南学院高校",
    "横須賀南高校",
    "津久井浜高校",
    "海洋科学高校",
]

# ── ユーティリティ ────────────────────────────────────────────

def get_school(member: discord.Member) -> str | None:
    """メンバーのロールから高校名を返す"""
    for role in member.roles:
        for school in TARGET_SCHOOLS:
            if school in role.name:
                return school
    return None


def get_grade(member: discord.Member) -> int | None:
    """
    入学年次ロール（例: 2023入学）から現在の学年を計算。
    4月以降を新学年とする。
    """
    now = datetime.now()
    current_year = now.year if now.month >= 4 else now.year - 1

    for role in member.roles:
        m = re.search(r"(\d{4})入学", role.name)
        if m:
            entry_year = int(m.group(1))
            grade = current_year - entry_year + 1
            if 1 <= grade <= 3:
                return grade
    return None


def fetch_json_from_github(filename: str) -> dict | None:
    """GitHub API でファイルの内容を取得する（起動時のデータ復元用）"""
    if not MY_GITHUB_TOKEN or not MY_GITHUB_REPO:
        return None
    import urllib.request, base64
    url = f"https://api.github.com/repos/{MY_GITHUB_REPO}/contents/{filename}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"token {MY_GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    })
    try:
        with urllib.request.urlopen(req) as res:
            body = json.loads(res.read())
            content = base64.b64decode(body["content"]).decode("utf-8")
            return json.loads(content)
    except Exception as e:
        print(f"⚠️  GitHub から {filename} 取得失敗: {e}")
        return None


def load_data() -> dict:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    # ローカルになければ GitHub から復元（クラウド再起動対策）
    remote = fetch_json_from_github(DATA_FILE)
    if remote is not None:
        print(f"✅ GitHub から {DATA_FILE} を復元しました")
        save_data(remote)
        return remote
    return {}


def save_data(data: dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def build_summary() -> dict:
    """
    data.json の生データから勢力図用サマリーを生成。
    {
      "横須賀学院高校": {"y1": 3, "y2": 5, "y3": 2, "ranks": {"Gold": 4, ...}},
      ...
    }
    """
    raw = load_data()
    summary: dict[str, dict] = {}

    for uid, info in raw.items():
        school = info.get("school")
        grade  = info.get("grade")
        rank   = info.get("rank", "未申告")

        if not school or not grade:
            continue

        if school not in summary:
            summary[school] = {"y1": 0, "y2": 0, "y3": 0, "ranks": {}}

        key = f"y{grade}"
        summary[school][key] = summary[school].get(key, 0) + 1
        summary[school]["ranks"][rank] = summary[school]["ranks"].get(rank, 0) + 1

    return summary


# ── ランク選択 View ───────────────────────────────────────────

class RankSelectView(discord.ui.View):
    """永続 View: ボット再起動後もボタンが機能する"""

    def __init__(self):
        super().__init__(timeout=None)

        # ランクを3列で並べる（Radiant + 未申告 は最後）
        display_ranks = [r for r in RANKS if r[0] not in ("Radiant", "未申告")]
        for rank_name, emoji, _ in display_ranks:
            self.add_item(RankButton(rank_name, emoji))

        # Radiant と 未申告 は別行
        self.add_item(RankButton("Radiant", "⭐", style=discord.ButtonStyle.success))
        self.add_item(RankButton("未申告", "❓", style=discord.ButtonStyle.secondary))


class RankButton(discord.ui.Button):
    def __init__(self, rank_name: str, emoji: str,
                 style: discord.ButtonStyle = discord.ButtonStyle.primary):
        super().__init__(
            label=rank_name,
            emoji=emoji,
            style=style,
            custom_id=f"rank_{rank_name}",  # 永続化キー
        )
        self.rank_name = rank_name

    async def callback(self, interaction: discord.Interaction):
        member = interaction.user
        school = get_school(member)
        grade  = get_grade(member)

        # ── バリデーション ──
        if school is None:
            await interaction.response.send_message(
                "❌ **高校ロールが見つかりません。**\n"
                "サーバー管理者に高校ロール（例：`横須賀学院高校`）を付与してもらってください。",
                ephemeral=True,
            )
            return

        if grade is None:
            await interaction.response.send_message(
                "❌ **入学年次ロールが見つかりません。**\n"
                "サーバー管理者に入学年次ロール（例：`2023入学`）を付与してもらってください。",
                ephemeral=True,
            )
            return

        # ── データ更新 ──
        data = load_data()
        uid  = str(member.id)

        prev_rank = data.get(uid, {}).get("rank", "（未登録）")
        data[uid] = {
            "username": str(member),
            "display_name": member.display_name,
            "school": school,
            "grade": grade,
            "rank": self.rank_name,
            "updated_at": datetime.now().isoformat(),
        }
        save_data(data)

        # ── サマリー更新（勢力図向け） ──
        summary = build_summary()
        with open("summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        # ── GitHub Pages に自動 push ──
        asyncio.create_task(push_data_to_github(school, self.rank_name))

        # ── 返信 ──
        rank_info = next(r for r in RANKS if r[0] == self.rank_name)
        embed = discord.Embed(
            title=f"{rank_info[1]} ランクを申告しました",
            color=int(rank_info[2].replace("#", ""), 16),
        )
        embed.add_field(name="学校",   value=school,           inline=True)
        embed.add_field(name="学年",   value=f"{grade}年生",   inline=True)
        embed.add_field(name="ランク", value=self.rank_name,   inline=True)
        if prev_rank != self.rank_name:
            embed.set_footer(text=f"以前の申告: {prev_rank} → {self.rank_name}")

        await interaction.response.send_message(embed=embed, ephemeral=True)


# ── GitHub Pages 自動 push ───────────────────────────────────

async def push_data_to_github(school: str, rank: str):
    """
    data.json と summary.json を GitHub API 経由で push する。
    git コマンド不要・クラウド環境でも動作。
    MY_GITHUB_TOKEN と MY_GITHUB_REPO が設定されている場合のみ動作。
    """
    if not MY_GITHUB_TOKEN or not MY_GITHUB_REPO:
        print("⚠️  MY_GITHUB_TOKEN / MY_GITHUB_REPO が未設定のため push をスキップ")
        return

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _api_push, school, rank)
        print(f"✅ GitHub API push 完了: {school} / {rank}")
    except Exception as e:
        print(f"❌ GitHub API push エラー: {e}")


def _api_push(school: str, rank: str):
    """GitHub Contents API でファイルを更新（git コマンド不要）"""
    import urllib.request, base64

    headers = {
        "Authorization": f"token {MY_GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
    }
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    for filename in ("data.json", "summary.json"):
        if not os.path.exists(filename):
            continue

        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()

        encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        url = f"https://api.github.com/repos/{MY_GITHUB_REPO}/contents/{filename}"

        # 現在の SHA を取得（更新に必要）
        sha = None
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req) as res:
                sha = json.loads(res.read())["sha"]
        except Exception:
            pass  # 新規ファイルの場合は sha 不要

        payload = {
            "message": f"bot: update {filename} [{school} / {rank}] {timestamp}",
            "content": encoded,
        }
        if sha:
            payload["sha"] = sha

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="PUT")
        with urllib.request.urlopen(req) as res:
            print(f"  ✅ {filename} pushed (status {res.status})")


# ── Bot セットアップ ──────────────────────────────────────────

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    # 永続 View を登録（再起動後もボタンが機能）
    bot.add_view(RankSelectView())
    try:
        synced = await bot.tree.sync()
        print(f"✅ {bot.user} 起動完了 | スラッシュコマンド {len(synced)} 件同期")
    except Exception as e:
        print(f"⚠️ コマンド同期エラー: {e}")

    # 自動パネル投稿
    await auto_post_panel()


async def auto_post_panel():
    """
    起動時にパネルチャンネルを確認し、
    ・パネルが存在しない → 新規投稿
    ・パネルが存在する   → Viewを再アタッチ（ボタンを有効化）するだけ
    PANEL_CHANNEL_ID が未設定の場合はスキップ。
    """
    channel_id = os.getenv("PANEL_CHANNEL_ID")
    if not channel_id:
        print("ℹ️  PANEL_CHANNEL_ID 未設定のため自動投稿をスキップ")
        return

    channel = bot.get_channel(int(channel_id))
    if not channel:
        print(f"⚠️  チャンネル {channel_id} が見つかりません")
        return

    # チャンネルの直近100件からボット自身のパネルメッセージを探す
    panel_msg = None
    async for msg in channel.history(limit=100):
        if msg.author == bot.user and msg.embeds:
            if msg.embeds[0].title and "VALORANT" in msg.embeds[0].title:
                panel_msg = msg
                break

    embed = discord.Embed(
        title="🎮 VALORANT ランク申告",
        description=(
            "現在のランクを選択してください。\n"
            "いつでも押し直すことで更新できます。\n\n"
            "ランクは高校・学年ロールと紐づけて記録され、\n"
            "**横須賀市 高校 VALORANT 勢力図**に反映されます。"
        ),
        color=0x0057A8,
    )
    embed.set_footer(text="YeG — Yokosuka eGeneration")

    if panel_msg:
        # 既存メッセージのViewを更新（ボタンを再有効化）
        try:
            await panel_msg.edit(embed=embed, view=RankSelectView())
            print(f"✅ 既存パネルを更新: #{channel.name}")
        except Exception as e:
            print(f"⚠️  パネル更新エラー: {e}")
    else:
        # 新規投稿
        try:
            await channel.send(embed=embed, view=RankSelectView())
            print(f"✅ パネルを新規投稿: #{channel.name}")
        except Exception as e:
            print(f"⚠️  パネル投稿エラー: {e}")


# ── /panel コマンド ───────────────────────────────────────────

@bot.tree.command(name="panel", description="VALORANTランク申告パネルをこのチャンネルに投稿します（管理者専用）")
@app_commands.checks.has_permissions(manage_guild=True)
async def panel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎮 VALORANT ランク申告",
        description=(
            "現在のランクを選択してください。\n"
            "いつでも押し直すことで更新できます。\n\n"
            "ランクは高校・学年ロールと紐づけて記録され、\n"
            "**横須賀市 高校 VALORANT 勢力図**に反映されます。"
        ),
        color=0x0057A8,
    )
    embed.set_footer(text="YeG — Yokosuka eGeneration")

    await interaction.response.send_message(embed=embed, view=RankSelectView())


# ── /status コマンド ──────────────────────────────────────────

@bot.tree.command(name="status", description="現在の勢力サマリーを表示します")
async def status(interaction: discord.Interaction):
    summary = build_summary()
    if not summary:
        await interaction.response.send_message(
            "まだデータがありません。`/panel` でランク申告パネルを投稿してください。",
            ephemeral=True,
        )
        return

    # 合計人数順にソート
    sorted_schools = sorted(
        summary.items(),
        key=lambda x: x[1]["y1"] + x[1]["y2"] + x[1]["y3"],
        reverse=True,
    )

    embed = discord.Embed(
        title="📊 横須賀市 VALORANT 勢力図 — 現在のデータ",
        color=0x0057A8,
    )
    medals = ["🥇", "🥈", "🥉"]
    for i, (school, d) in enumerate(sorted_schools):
        total = d["y1"] + d["y2"] + d["y3"]
        medal = medals[i] if i < 3 else f"{i+1}."
        top_rank = max(d["ranks"], key=d["ranks"].get) if d["ranks"] else "未申告"
        embed.add_field(
            name=f"{medal} {school}",
            value=(
                f"合計 **{total}人** "
                f"（1年:{d['y1']} / 2年:{d['y2']} / 3年:{d['y3']}）\n"
                f"最多ランク: {top_rank}"
            ),
            inline=False,
        )

    embed.set_footer(text=f"最終更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ── /myrank コマンド ──────────────────────────────────────────

@bot.tree.command(name="myrank", description="自分の現在の申告ランクを確認します")
async def myrank(interaction: discord.Interaction):
    data = load_data()
    uid  = str(interaction.user.id)

    if uid not in data:
        await interaction.response.send_message(
            "まだランクを申告していません。パネルのボタンから申告してください。",
            ephemeral=True,
        )
        return

    d = data[uid]
    rank_info = next((r for r in RANKS if r[0] == d.get("rank")), RANKS[-1])
    embed = discord.Embed(
        title=f"{rank_info[1]} あなたの申告情報",
        color=int(rank_info[2].replace("#", ""), 16),
    )
    embed.add_field(name="学校",      value=d.get("school", "不明"),       inline=True)
    embed.add_field(name="学年",      value=f"{d.get('grade', '?')}年生",  inline=True)
    embed.add_field(name="ランク",    value=d.get("rank", "未申告"),        inline=True)
    updated = d.get("updated_at", "")[:10]
    embed.set_footer(text=f"最終更新: {updated}")

    await interaction.response.send_message(embed=embed, ephemeral=True)


# ── エラーハンドラ ────────────────────────────────────────────

@panel.error
async def panel_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            "❌ このコマンドはサーバー管理者のみ使用できます。",
            ephemeral=True,
        )


# ── 起動 ─────────────────────────────────────────────────────

if __name__ == "__main__":
    if not TOKEN:
        print("❌ .env に DISCORD_TOKEN が設定されていません")
    else:
        bot.run(TOKEN)
