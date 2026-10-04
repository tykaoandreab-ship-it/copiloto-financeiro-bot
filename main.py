import os
import threading
from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import yfinance as yf

# 1. Servidor Web Mínimo para satisfazer a porta HTTP do Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Copiloto Financeiro IA está online!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# 2. Configurações do Bot
TOKEN = os.environ.get("TELEGRAM_TOKEN")  # Ou cola o teu token entre aspas se não usares variável de ambiente
CUPOM_NOMAD = "J3FMR8ZMBL"
LINK_NOMAD = f"https://nomad.onelink.me/923531008?af_c_id={CUPOM_NOMAD}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "👋 **Olá! Sou o Copiloto Financeiro IA.**\n\n"
        "Posso analisar ações e FIIs da B3 em tempo real.\n"
        "Exemplo: envia `/analisar PETR4` ou `/analisar VALE3`."
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def analisar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso correto: `/analisar TICKER` (ex: `/analisar PETR4`)", parse_mode="Markdown")
        return

    ticker = context.args[0].upper()
    if not ticker.endswith(".SA"):
        ticker_search = f"{ticker}.SA"
    else:
        ticker_search = ticker

    await update.message.reply_text(f"🔍 A procurar dados de {ticker} na B3...")

    try:
        stock = yf.Ticker(ticker_search)
        info = stock.info

        preco = info.get("currentPrice") or info.get("regularMarketPrice") or 0.0
        dy = (info.get("dividendYield") or 0.0) * 100
        pl = info.get("trailingPE") or 0.0
        pvp = info.get("priceToBook") or 0.0
        roe = (info.get("returnOnEquity") or 0.0) * 100

        resposta = (
            f"📊 **ANÁLISE FUNDAMENTALISTA: {ticker}**\n\n"
            f"💵 **Preço Atual:** R$ {preco:.2f}\n"
            f"💰 **Dividend Yield (12M):** {dy:.2f}%\n"
            f"📈 **P/L (Preço/Lucro):** {pl:.2f}\n"
            f"🏛 **P/VP (Preço/Valor Patrimonial):** {pvp:.2f}\n"
            f"🎯 **ROE (Retorno s/ Património):** {roe:.2f}%\n\n"
            f"💡 *Dados em tempo real via Yahoo Finance.*"
        )

        keyboard = [[
            InlineKeyboardButton(
                f"📲 Investir em Dólar via Nomad (Cupom {CUPOM_NOMAD})",
                url=LINK_NOMAD
            )
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(resposta, parse_mode="Markdown", reply_markup=reply_markup)

    except Exception as e:
        await update.message.reply_text(f"❌ Erro ao procurar dados de {ticker}. Verifica se o código está correto.")

def main():
    # Inicia o servidor Flask numa thread separada
    threading.Thread(target=run_flask, daemon=True).start()

    # Inicia o Bot do Telegram
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("analisar", analisar))

    print("Bot a rodar...")
    application.run_polling()

if __name__ == "__main__":
    main()
    
