import os
import requests
from flask import Flask, request, abort, send_file
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, ImageMessage, TextSendMessage
from datetime import datetime

# ⚠️ ตั้งค่า LINE Bot - ต้องใส่ค่าที่ถูกต้อง!
# ไปที่ LINE Developers Console > Your Channel > Messaging API tab
CHANNEL_ACCESS_TOKEN = 'YBZrj8OI8Voke86NBdugTguwJLUH4TR43obwLJKwvO8OXz2uOeXxsy+0FrYH18h5b/a2M0dRyUwLqnmpcHFPzPOEpBpXHLRJl14B5YRHENvB4hmVTG3bc5cGrophZcxJ7HawTB+OtGKS+hBaJedZhwdB04t89/1O/w1cDnyilFU='
CHANNEL_SECRET = 'dde835e788a9d8176b0a76fd173c7cf2'
SAVE_DIRECTORY = './images'  # เปลี่ยนเป็น relative path สำหรับ Render

app = Flask(__name__)
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# สร้างโฟลเดอร์สำหรับเก็บรูป
if not os.path.exists(SAVE_DIRECTORY):
    os.makedirs(SAVE_DIRECTORY)

# ทดสอบว่า server ทำงาน
@app.route("/", methods=['GET'])
def home():
    return """
    <h1>LINE Bot is running!</h1>
    <p>Available endpoints:</p>
    <ul>
        <li><a href="/images">View all images</a></li>
        <li>/callback - Webhook endpoint for LINE</li>
    </ul>
    """

# เพิ่มหน้าแสดงรายการรูปภาพ
@app.route("/images")
def list_images():
    """แสดงรายการรูปภาพทั้งหมด"""
    try:
        files = os.listdir(SAVE_DIRECTORY)
        image_files = [f for f in files if f.endswith(('.jpg', '.jpeg', '.png', '.gif'))]
        
        if not image_files:
            return """
            <h1>ไม่มีรูปภาพ</h1>
            <p>ยังไม่มีรูปภาพถูกบันทึก</p>
            <a href="/">กลับหน้าหลัก</a>
            """
        
        # สร้าง HTML แบบสวยงาม
        html = """
        <html>
        <head>
            <title>รูปภาพทั้งหมด</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1 { color: #333; }
                .image-grid { 
                    display: grid; 
                    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); 
                    gap: 20px; 
                    margin-top: 20px;
                }
                .image-card {
                    border: 1px solid #ddd;
                    padding: 10px;
                    text-align: center;
                    background: #f9f9f9;
                    border-radius: 5px;
                }
                .image-card img { 
                    max-width: 100%; 
                    height: 150px; 
                    object-fit: cover;
                    border-radius: 3px;
                }
                .image-name { 
                    margin-top: 10px; 
                    font-size: 12px; 
                    word-break: break-all;
                }
                .stats { 
                    background: #e9ecef; 
                    padding: 10px; 
                    border-radius: 5px; 
                    margin-bottom: 20px;
                }
            </style>
        </head>
        <body>
            <h1>📸 รูปภาพทั้งหมด</h1>
            <div class="stats">
                <strong>จำนวนรูปทั้งหมด:</strong> {} รูป<br>
                <strong>อัพเดทล่าสุด:</strong> {}
            </div>
            <a href="/">← กลับหน้าหลัก</a>
            <div class="image-grid">
        """.format(
            len(image_files),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        # เรียงตามวันที่ล่าสุดก่อน
        for img in sorted(image_files, reverse=True):
            html += f"""
            <div class="image-card">
                <a href="/view/{img}" target="_blank">
                    <img src="/view/{img}" alt="{img}">
                </a>
                <div class="image-name">{img}</div>
                <a href="/view/{img}" download>📥 Download</a>
            </div>
            """
        
        html += """
            </div>
        </body>
        </html>
        """
        
        return html
    except Exception as e:
        return f"<h1>Error</h1><p>{e}</p>"

# เพิ่มหน้าแสดงรูปภาพ
@app.route("/view/<filename>")
def view_image(filename):
    """แสดงรูปภาพ"""
    try:
        # ป้องกันการเข้าถึงไฟล์นอก directory
        if '..' in filename or '/' in filename:
            return "Invalid filename", 400
            
        filepath = os.path.join(SAVE_DIRECTORY, filename)
        if os.path.exists(filepath):
            return send_file(filepath, mimetype='image/jpeg')
        else:
            return "File not found", 404
    except Exception as e:
        return f"Error: {e}", 500

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
        reply_text = f"""✅ บันทึกรูปภาพเรียบร้อยแล้ว!
📁 Filename: {filename}
🔗 ดูรูปได้ที่: https://line-image-bot.onrender.com/view/{filename}
📋 ดูทั้งหมด: https://line-image-bot.onrender.com/images"""
        
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )
        
    except Exception as e:
        print(f"Error: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='❌ เกิดข้อผิดพลาดในการบันทึกรูปภาพ')
        )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
