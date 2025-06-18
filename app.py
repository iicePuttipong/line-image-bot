import os
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, ImageMessage, TextSendMessage
from datetime import datetime

# ⚠️ ตั้งค่า LINE Bot - ต้องใส่ค่าที่ถูกต้อง!
# ไปที่ LINE Developers Console > Your Channel > Messaging API tab
CHANNEL_ACCESS_TOKEN = 'YBZrj8OI8Voke86NBdugTguwJLUH4TR43obwLJKwvO8OXz2uOeXxsy+0FrYH18h5b/a2M0dRyUwLqnmpcHFPzPOEpBpXHLRJl14B5YRHENvB4hmVTG3bc5cGrophZcxJ7HawTB+OtGKS+hBaJedZhwdB04t89/1O/w1cDnyilFU='  # ⚠️ ต้องเป็น Token ยาวๆ ไม่ใช่ Channel ID!
CHANNEL_SECRET = 'dde835e788a9d8176b0a76fd173c7cf2'  # ✅ นี่ถูกแล้ว (Channel Secret)
SAVE_DIRECTORY = r'D:/Users/80009678/Desktop/LineImageChatbot'  # ✅ Path ถูกแล้ว

# ตัวอย่าง Access Token ที่ถูกต้องจะมีลักษณะแบบนี้:
# 'abcDEF123456789+/=...' (ยาวประมาณ 170+ ตัวอักษร)

app = Flask(__name__)
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# สร้างโฟลเดอร์สำหรับเก็บรูป
if not os.path.exists(SAVE_DIRECTORY):
    os.makedirs(SAVE_DIRECTORY)

# ทดสอบว่า server ทำงาน
@app.route("/", methods=['GET'])
def home():
    return "LINE Bot is running! Use /callback for webhook."

# Webhook endpoint
@app.route("/callback", methods=['POST'])
def callback():
    # รับ signature จาก LINE
    signature = request.headers['X-Line-Signature']
    
    # รับ body จาก request
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Check your channel secret.")
        abort(400)
    
    return 'OK'

@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    """ฟังก์ชันจัดการเมื่อมีคนส่งรูปภาพ"""
    
    print(f"Received image from user: {event.source.user_id}")
    
    # ดึง message_id
    message_id = event.message.id
    
    try:
        # ดึงข้อมูลรูปภาพ
        message_content = line_bot_api.get_message_content(message_id)
        
        # สร้างชื่อไฟล์ด้วย timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"image_{timestamp}_{message_id}.jpg"
        filepath = os.path.join(SAVE_DIRECTORY, filename)
        
        # บันทึกรูปภาพ
        with open(filepath, 'wb') as f:
            for chunk in message_content.iter_content():
                f.write(chunk)
        
        print(f"บันทึกรูปภาพ: {filepath}")
        
        # ตอบกลับผู้ใช้
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f'✅ บันทึกรูปภาพเรียบร้อยแล้ว!\nFilename: {filename}')
        )
        
    except Exception as e:
        print(f"Error: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='❌ เกิดข้อผิดพลาดในการบันทึกรูปภาพ')
        )

# ฟังก์ชันสำหรับตรวจสอบการตั้งค่า
def check_configuration():
    """ตรวจสอบว่าตั้งค่าถูกต้อง"""
    print("=== ตรวจสอบการตั้งค่า ===")
    
    # ตรวจสอบ Token
    if len(CHANNEL_ACCESS_TOKEN) < 100:
        print("❌ CHANNEL_ACCESS_TOKEN ไม่ถูกต้อง! ต้องเป็น Token ยาวๆ จาก LINE Developers Console")
        print("   ไปที่: Messaging API tab > Channel access token > Issue")
        return False
    
    # ตรวจสอบ Secret
    if len(CHANNEL_SECRET) != 32:
        print("❌ CHANNEL_SECRET ไม่ถูกต้อง! ต้องมีความยาว 32 ตัวอักษร")
        print("   ไปที่: Basic settings tab > Channel secret")
        return False
    
    # ตรวจสอบ Directory
    if not os.path.exists(SAVE_DIRECTORY):
        print(f"📁 สร้างโฟลเดอร์: {SAVE_DIRECTORY}")
        os.makedirs(SAVE_DIRECTORY)
    
    print("✅ การตั้งค่าถูกต้อง!")
    return True

if __name__ == "__main__":
    # ตรวจสอบการตั้งค่าก่อนรัน
    if check_configuration():
        print("\n🚀 Starting LINE Bot...")
        print("📌 Webhook URL: http://localhost:5000/callback")
        print("💡 ใช้ ngrok เพื่อทำให้ LINE เข้าถึงได้: ngrok http 5000")
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        print("\n❌ กรุณาแก้ไขการตั้งค่าก่อนรัน Bot")