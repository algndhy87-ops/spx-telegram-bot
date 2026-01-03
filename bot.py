from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from PIL import Image, ImageDraw

TOKEN = "8504745697:AAGMg6pK0tmySvZ589xESqQBhPCarOFfcP4"

trades = []

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📊 SPX Contracts Bot\n\n"
        "/trade - Add trade\n"
        "/report - Daily report"
    )

# /trade
async def trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["step"] = 1
    await update.message.reply_text("Type: CALL or PUT")

# handle steps
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get("step", 0)
    text = update.message.text

    try:
        if step == 1:
            context.user_data["type"] = text.upper()
            context.user_data["step"] = 2
            await update.message.reply_text("Entry price:")

        elif step == 2:
            context.user_data["entry"] = float(text)
            context.user_data["step"] = 3
            await update.message.reply_text("High price:")

        elif step == 3:
            context.user_data["high"] = float(text)
            context.user_data["step"] = 4
            await update.message.reply_text("Contracts:")

        elif step == 4:
            contracts = int(text)
            entry = context.user_data["entry"]
            high = context.user_data["high"]

            pnl = (high - entry) * contracts * 100
            status = "WIN" if pnl >= 100 else "LOSS"

            trades.append({
                "type": context.user_data["type"],
                "pnl": pnl,
                "status": status
            })

            context.user_data.clear()
            await update.message.reply_text(
                f"✅ Trade saved\nPnL: {pnl:.2f}$ ({status})"
            )
    except:
        await update.message.reply_text("❌ Invalid input, try again")

# generate report image
def generate_report():
    img = Image.new("RGB", (900, 600), "#0b3d2e")
    d = ImageDraw.Draw(img)

    wins = sum(1 for t in trades if t["status"] == "WIN")
    losses = sum(1 for t in trades if t["status"] == "LOSS")
    total = len(trades)
    profit = sum(t["pnl"] for t in trades if t["pnl"] > 0)
    loss = sum(t["pnl"] for t in trades if t["pnl"] < 0)
    net = profit + loss
    winrate = (wins / total * 100) if total else 0

    d.text((20, 20), "تقرير صفقات بوت عقود SPX", fill="gold")
    d.text((20, 70), f"Total Trades: {total}", fill="white")
    d.text((20, 100), f"Wins: {wins}", fill="white")
    d.text((20, 130), f"Losses: {losses}", fill="white")
    d.text((20, 160), f"Win Rate: {winrate:.1f}%", fill="white")
    d.text((20, 200), f"Total Profit: {profit:.2f}$", fill="lightgreen")
    d.text((20, 230), f"Total Loss: {loss:.2f}$", fill="red")
    d.text((20, 260), f"Net P/L: {net:.2f}$", fill="gold")

    img.save("report.png")
    return "report.png"

# /report
async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not trades:
        await update.message.reply_text("No trades today")
        return

    img = generate_report()
    await update.message.reply_photo(photo=open(img, "rb"))

# main
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("trade", trade))
app.add_handler(CommandHandler("report", report))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

app.run_polling()
