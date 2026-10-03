import telebot
from telebot import types
import yfinance as yf
import sqlite3
import time
from datetime import date

TOKEN = "8643839927:AAEInmNYsKyfhnknXqyus1DSfqcLVI7OMmw"
bot = telebot.TeleBot(TOKEN)

LINK_AFILIADO_FINANCAS = "https://www.xpinc.com.br" 

conn = sqlite3.connect('bot_financas_vip.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS utilizadores (
        user_id INTEGER PRIMARY KEY,
        is_vip INTEGER DEFAULT 0,
        consultas_hoje INTEGER DEFAULT 0,
        ultima_consulta TEXT
    )
''')
conn.commit()

bot.remove_webhook()
time.sleep(1)

def get_user(user_id):
    cursor.execute('SELECT is_vip, consultas_hoje, ultima_consulta FROM utilizadores WHERE user_id = ?', (user_id,))
    return cursor.fetchone()

def checar_limite_e_incrementar(user_id):
    user = get_user(user_id)
    hoje = str(date.today())

    if not user:
        cursor.execute('INSERT INTO utilizadores (user_id, is_vip, consultas_hoje, ultima_consulta) VALUES (?, 0, 1, ?)', (user_id, hoje))
        conn.commit()
        return True, 2

    is_vip, consultas, ultima_data = user

    if is_vip == 1:
        return True, "VIP"

    if ultima_data != hoje:
        cursor.execute('UPDATE utilizadores SET consultas_hoje = 1, ultima_consulta = ? WHERE user_id = ?', (hoje, user_id))
        conn.commit()
        return True, 2

    if consultas < 3:
        cursor.execute('UPDATE utilizadores SET consultas_hoje = ? WHERE user_id = ?', (consultas + 1, user_id))
        conn.commit()
        return True, 3 - (consultas + 1)
    else:
        return False, 0

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_corretora = types.InlineKeyboardButton("🏦 Abrir Conta em Corretora Zero Taxa", url=LINK_AFILIADO_FINANCAS)
    markup.add(btn_corretora)
    
    msg = (
        "📈 *Copiloto Financeiro IA - Análise de Ativos B3*\n\n"
        "Consulta em tempo real de Ações e Fundos Imobiliários.\n\n"
        "🎁 *Plano Free:* 3 Análises gratuitas por dia.\n"
        "⭐ *Plano VIP:* Consultas ilimitadas.\n\n"
        "📌 *Como Usar:*\n"
        "Envia `/analisar [CÓDIGO]`\n\n"
        "Exemplos:\n"
        "• `/analisar PETR4`\n"
        "• `/analisar VALE3`\n"
        "• `/analisar HGLG11`\n"
    )
    bot.reply_to(message, msg, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(commands=['analisar'])
def analisar_ativo(message):
    user_id = message.chat.id
    permitido, restantes = checar_limite_e_incrementar(user_id)

    if not permitido:
        markup = types.InlineKeyboardMarkup()
        btn_vip = types.InlineKeyboardButton("⭐ Assinar Plano VIP (Ilimitado)", url="https://t.me/teu_usuario")
        markup.add(btn_vip)
        bot.reply_to(
            message, 
            "🛑 *Limite Diário de 3 Consultas Atingido!*\n\nVolta amanhã para mais análises ou assina o Plano VIP para acesso ilimitado.", 
            parse_mode="Markdown",
            reply_markup=markup
        )
        return

    try:
        partes = message.text.split()
        if len(partes) < 2:
            bot.reply_to(message, "⚠️️ Indica o código do ativo. Exemplo: `/analisar PETR4`", parse_mode="Markdown")
            return

        ticker_raw = partes[1].upper().strip()
        ticker_b3 = f"{ticker_raw}.SA"
        
        bot.send_message(message.chat.id, f"🔍 A procurar dados de *{ticker_raw}* na B3...", parse_mode="Markdown")
        
        stock = yf.Ticker(ticker_b3)
        info = stock.info

        preco = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose') or 0.0
        
        dy_raw = info.get('dividendYield') or 0.0
        dy = dy_raw * 100 if dy_raw < 1.0 else dy_raw

        pl = info.get('trailingPE') or 0.0
        pvp = info.get('priceToBook') or 0.0
        
        roe_raw = info.get('returnOnEquity') or 0.0
        roe = roe_raw * 100 if roe_raw < 1.0 else roe_raw
        
        nome = info.get('longName') or info.get('shortName') or ticker_raw

        if preco == 0.0:
            bot.reply_to(message, f"❌ Não foram encontrados dados para o ativo *{ticker_raw}*. Confirma o código.", parse_mode="Markdown")
            return

        markup = types.InlineKeyboardMarkup()
        btn_investir = types.InlineKeyboardButton(f"📲 Investir em {ticker_raw} via Corretora", url=LINK_AFILIADO_FINANCAS)
        markup.add(btn_investir)

        relatorio = (
            f"📊 *ANÁLISE FUNDAMENTALISTA: {ticker_raw}*\n"
            f"🏢 *{nome}*\n\n"
            f"💵 *Preço Atual:* R$ {preco:.2f}\n"
            f"💰 *Dividend Yield (12M):* {dy:.2f}%\n"
            f"📈 *P/L (Preço/Lucro):* {pl:.2f}\n"
            f"🏛️ *P/VP (Preço/Valor Patrimonial):* {pvp:.2f}\n"
            f"🎯 *ROE (Retorno s/ Patrimônio):* {roe:.2f}%\n\n"
            f"🎯 *Consultas Restantes Hoje:* {restantes}\n"
            f"💡 _Dados em tempo real via Yahoo Finance._"
        )

        bot.reply_to(message, relatorio, parse_mode="Markdown", reply_markup=markup)

    except Exception as e:
        bot.reply_to(message, f"⚠️ Tenta novamente em instantes ({str(e)})")

print("🚀 Bot Financeiro Monetizado Online!")
bot.polling(non_stop=True, skip_pending=True)
      
