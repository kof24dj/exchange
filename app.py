from flask import Flask, jsonify
from flask_cors import CORS
import yfinance as yf
from datetime import datetime
import pandas as pd
import requests

app = Flask(__name__)
CORS(app)

CURRENCY_TICKS = {
    "USD": "TWD=X",
    "JPY": "JPYTWD=X",
    "EUR": "EURTWD=X",
    "VND_USD": "VND=X"
}

def fetch_all_rates_5y():
    """從 Yahoo 財經獲取 5 年的歷史數據"""
    raw_dfs = {}
    for key, ticker in CURRENCY_TICKS.items():
        try:
            print(f"📡 正在從 Yahoo 財經獲取 {key} 的 5 年歷史數據...")
            ticker_data = yf.Ticker(ticker)
            df = ticker_data.history(period="5y")
            if not df.empty:
                df.index = df.index.strftime("%Y-%m-%d")
                raw_dfs[key] = df["Close"]
        except Exception as e:
            print(f"❌ {key} 5年數據抓取失敗: {e}")

    final_rates = {"USD": [], "JPY": [], "EUR": [], "VND": []}

    for code in ["USD", "JPY", "EUR"]:
        if code in raw_dfs:
            for date, price in raw_dfs[code].items():
                final_rates[code].append({"date": date, "rate": float(price)})
            print(f"✅ {code} 5年數據同步成功！共 {len(final_rates[code])} 筆資料")

    if "USD" in raw_dfs and "VND_USD" in raw_dfs:
        print("🧮 正在進行越南盾【1台幣換多少越南盾】歷史匯率交叉換算...")
        common_dates = raw_dfs["USD"].index.intersection(raw_dfs["VND_USD"].index)
        for date in common_dates:
            usd_twd = raw_dfs["USD"].loc[date]
            usd_vnd = raw_dfs["VND_USD"].loc[date]
            if usd_twd > 0:
                twd_vnd = float(usd_vnd / usd_twd)
                final_rates["VND"].append({"date": date, "rate": twd_vnd})
        final_rates["VND"].sort(key=lambda x: x["date"])
        print(f"✅ VND 5年交叉換算成功！共 {len(final_rates['VND'])} 筆歷史資料")
    else:
        print("❌ 缺乏基礎數據，無法換算越南盾")

    return final_rates

@app.route("/api/rates", methods=["GET"])
def get_rates():
    all_rates = fetch_all_rates_5y()
    return jsonify(all_rates)

if __name__ == "__main__":
    print("正在啟動【Yahoo財經 越南盾習慣優化版】匯率 API 伺服器...")
    app.run(debug=True, port=5000)
