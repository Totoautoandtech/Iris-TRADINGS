import asyncio
import aiohttp
import time

YF_CHART   = "https://query1.finance.yahoo.com/v8/finance/chart"
YF_SUMMARY = "https://query1.finance.yahoo.com/v10/finance/quoteSummary"
HEADERS    = {"User-Agent": "Mozilla/5.0 (compatible; IrisTradingBot/1.0)"}
CACHE_TTL  = 30  # secondes

PRELOAD_SYMBOLS = ["^FCHI", "^GSPC", "^IXIC", "BTC-USD", "ETH-USD", "AAPL", "MSFT", "NVDA"]


class MarketData:
    def __init__(self):
        self._cache:   dict = {}
        self._session: aiohttp.ClientSession | None = None
        self._running  = False

    def start(self):
        self._running = True
        asyncio.create_task(self._preload_loop())
        print("📊 MarketData: démarré")

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(headers=HEADERS)
        return self._session

    async def _preload_loop(self):
        while self._running:
            for sym in PRELOAD_SYMBOLS:
                await self.get_quote(sym, force=True)
                await asyncio.sleep(0.4)
            await asyncio.sleep(30)

    async def get_quote(self, symbol: str, force: bool = False) -> dict | None:
        key    = symbol.upper()
        cached = self._cache.get(key)
        if not force and cached and time.time() - cached["ts"] < CACHE_TTL:
            return cached["data"]
        try:
            session = await self._get_session()
            url     = f"{YF_CHART}/{key}?interval=1d&range=1d"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status != 200:
                    return cached["data"] if cached else None
                raw = await resp.json()

            result = (raw.get("chart") or {}).get("result") or []
            if not result:
                return None
            meta  = result[0]["meta"]
            prev  = meta.get("previousClose") or meta.get("chartPreviousClose") or meta.get("regularMarketPrice")
            price = meta.get("regularMarketPrice", 0)
            chg   = price - prev if prev else 0
            chgp  = (chg / prev * 100) if prev else 0

            data = {
                "symbol":        meta.get("symbol", key),
                "name":          meta.get("longName") or meta.get("shortName") or key,
                "price":         price,
                "previousClose": prev,
                "change":        chg,
                "changePercent": chgp,
                "volume":        meta.get("regularMarketVolume", 0),
                "currency":      meta.get("currency", ""),
                "marketState":   meta.get("marketState", "UNKNOWN"),
                "open":          meta.get("regularMarketOpen"),
                "dayHigh":       meta.get("regularMarketDayHigh"),
                "dayLow":        meta.get("regularMarketDayLow"),
            }
            self._cache[key] = {"data": data, "ts": time.time()}
            return data

        except Exception as e:
            print(f"MarketData erreur {symbol}: {e}")
            return cached["data"] if cached else None

    async def get_detailed_quote(self, symbol: str) -> dict | None:
        base = await self.get_quote(symbol)
        if not base:
            return None
        try:
            session = await self._get_session()
            url     = f"{YF_SUMMARY}/{symbol}?modules=summaryDetail,price"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status != 200:
                    return base
                raw = await resp.json()

            result_list = ((raw.get("quoteSummary") or {}).get("result")) or []
            if not result_list:
                return base
            detail  = result_list[0]
            price   = detail.get("price", {})
            summary = detail.get("summaryDetail", {})
            return {
                **base,
                "marketCap": (price.get("marketCap") or {}).get("raw"),
                "high52w":   (summary.get("fiftyTwoWeekHigh") or {}).get("raw"),
                "low52w":    (summary.get("fiftyTwoWeekLow") or {}).get("raw"),
                "pe":        (summary.get("trailingPE") or {}).get("raw"),
            }
        except Exception:
            return base

    async def get_multiple(self, symbols: list) -> list:
        results = await asyncio.gather(*[self.get_quote(s) for s in symbols])
        return [r for r in results if r]

    async def is_valid(self, symbol: str) -> bool:
        q = await self.get_quote(symbol, force=True)
        return q is not None and q.get("price", 0) > 0
