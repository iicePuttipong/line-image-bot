import os
import requests
from flask import Flask, request, abort, send_file
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, ImageMessage, TextSendMessage
from datetime import datetime

# ตั้งค่า LINE Bot
CHANNEL_ACCESS_TOKEN = 'YBZrj8OI8Voke86NBdugTguwJLUH4TR43obwLJKwvO8OXz2uOeXxsy+0FrYH18h5b/a2M0dRyUwLqnmpcHFPzPOEpBpXHLRJl14B5YRHENvB4hmVTG3bc5cGrophZcxJ7HawTB+OtGKS+hBaJedZhwdB04t89/1O/w1cDnyilFU='
CHANNEL_SECRET = 'dde835e788a9d8176b0a76fd173c7cf2'
SAVE_DIRECTORY = './images'

app = Flask(__name__)
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# สร้างโฟลเดอร์สำหรับเก็บรูป
if not os.path.exists(SAVE_DIRECTORY):
    os.makedirs(SAVE_DIRECTORY)

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

@app.route("/images")
def list_images():
    """แสดงรายการรูปภาพทั้งหมด"""
    try:
        files = os.listdir(SAVE_DIRECTORY)
        image_files = [f for f in files if f.endswith(('.jpg', '.jpeg', '.png', '.gif'))]
        
        if not image_files:
            return "<h1>No Images</h1><p>No images have been saved yet.</p><a href='/'>Back to Home</a>"
        
        # สร้าง HTML แบบง่าย (ไม่มี CSS ซับซ้อน)
        html = "<html><head><title>All Images</title></head><body>"
        html += "<h1>All Images (" + str(len(image_files)) + " files)</h1>"
        html += "<a href='/'>Back to Home</a><br><br>"
        html += "<table border='1' cellpadding='10'>"
        html += "<tr><th>Preview</th><th>Filename</th><th>Actions</th></tr>"
        
        for img in sorted(image_files, reverse=True):
            html += "<tr>"
            html += "<td><img src='/view/" + img + "' width='200'></td>"
            html += "<td>" + img + "</td>"
            html += "<td><a href='/view/" + img + "' target='_blank'>View</a> | "
            html += "<a href='/view/" + img + "' download>Download</a></td>"
            html += "</tr>"
        
        html += "</table></body></html>"
        return html
        
    except Exception as e:
        return f"<h1>Error</h1><p>{str(e)}</p>"

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
        return f"Error: {str(e)}", 500

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
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
        
        print(f"Saved image: {filepath}")
        
        # ไม่ต้องตอบกลับ - comment หรือลบส่วนนี้ออก
        # line_bot_api.reply_message(
        #     event.reply_token,
        #     TextSendMessage(text=reply_text)
        # )
        
    except Exception as e:
        print(f"Error: {str(e)}")
        # ไม่ต้องตอบกลับเมื่อ error
        # line_bot_api.reply_message(
        #     event.reply_token,
        #     TextSendMessage(text='❌ Error saving image')
        # )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
