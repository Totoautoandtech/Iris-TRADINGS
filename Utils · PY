import discord
from datetime import datetime, timezone


def format_price(price) -> str:
    if price is None:
        return "N/A"
    return f"{price:,.2f}".replace(",", " ").replace(".", ",")


def format_change(value) -> str:
    if value is None:
        return "N/A"
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.2f}"


def get_emoji(change_pct) -> str:
    if change_pct is None: return "⚪"
    if change_pct >= 3:    return "🚀"
    if change_pct >= 1:    return "📈"
    if change_pct > 0:     return "🟢"
    if change_pct == 0:    return "⚪"
    if change_pct > -1:    return "🔴"
    if change_pct > -3:    return "📉"
    return "💥"


def market_state_label(state: str) -> str:
    return {"REGULAR": "🟢 Ouvert", "PRE": "🟡 Pré-marché",
            "POST": "🟠 Post-marché", "CLOSED": "🔴 Fermé"}.get(state, "⚪ Inconnu")


def format_quote_line(q: dict) -> str:
    emoji = get_emoji(q.get("changePercent", 0))
    price = format_price(q.get("price"))
    chg   = format_change(q.get("changePercent", 0))
    sign  = "+" if q.get("changePercent", 0) >= 0 else ""
    name  = q.get("name", q["symbol"])
    if len(name) > 22:
        name = q["symbol"]
    cur = q.get("currency", "")
    return f"{emoji} **{q['symbol']}** — {price} {cur} `{sign}{chg}%` — {name}"


async def build_market_embed(mkt, settings: dict, user_id: int) -> discord.Embed:
    watchlist = settings.get("watchlist", [])
    quotes    = await mkt.get_multiple(watchlist)
    now_str   = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
    avg_chg   = sum(q.get("changePercent", 0) for q in quotes) / len(quotes) if quotes else 0
    color     = 0x00b894 if avg_chg > 0.5 else (0xff7675 if avg_chg < -0.5 else 0x6C5CE7)

    embed = discord.Embed(
        title="💜 Iris Trading — Tableau de Bord Live",
        description=f"📅 Mis à jour à **{now_str}** · Actualisation auto toutes les 30s",
        color=color,
        timestamp=datetime.now(timezone.utc),
    )

    if not quotes:
        embed.add_field(name="📭 Watchlist vide",
                        value="Tape `!iris settings add SYMBOLE` pour ajouter des actifs", inline=False)
        return embed

    indices = [q for q in quotes if q["symbol"].startswith("^")]
    crypto  = [q for q in quotes if "-USD" in q["symbol"] or "-EUR" in q["symbol"]]
    stocks  = [q for q in quotes if q not in indices and q not in crypto]

    if indices:
        embed.add_field(name="📊 Indices", value="\n".join(format_quote_line(q) for q in indices), inline=False)
    if stocks:
        embed.add_field(name="🏢 Actions", value="\n".join(format_quote_line(q) for q in stocks),  inline=False)
    if crypto:
        embed.add_field(name="₿ Crypto",  value="\n".join(format_quote_line(q) for q in crypto),  inline=False)

    states = list({q.get("marketState", "UNKNOWN") for q in quotes})
    embed.add_field(name="🕐 État des marchés",
                    value=" · ".join(market_state_label(s) for s in states), inline=False)
    embed.set_footer(text="Iris Trading · Yahoo Finance · Pollinations.ai · Ta watchlist personnelle")
    return embed
