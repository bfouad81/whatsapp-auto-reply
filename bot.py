from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, time
import time as time_module
from langdetect import detect
import json
import os

# مواعيد العمل
WORKING_HOURS_AR = """⏰ مواعيد العمل:
- من الساعة 8 صباحاً
- إلى الساعة 12 ظهراً
- أيام السبت - الخميس
- يوم الجمعة: مغلق"""

WORKING_HOURS_EN = """⏰ Working Hours:
- From 8:00 AM
- To 12:00 PM
- Saturday - Thursday
- Friday: Closed"""

# الرسائل الرد التلقائي
AUTO_REPLY_AR = f"""مرحباً، شكراً على رسالتك 👋

أنا خارج أوقات العمل حالياً.

{WORKING_HOURS_AR}

📝 طلبك تم تسجيله وسيتم مراجعته في أوقات العمل.

شكراً لتفهمك 🙏"""

AUTO_REPLY_EN = f"""Hello, thank you for your message 👋

I'm currently outside working hours.

{WORKING_HOURS_EN}

📝 Your request has been noted and will be reviewed during business hours.

Thank you for understanding 🙏"""

# كلمات عاجلة
URGENT_KEYWORDS_AR = ['عاجل', 'طارئ', 'فوري', 'ضروري', 'سريع', 'مهم جداً']
URGENT_KEYWORDS_EN = ['urgent', 'emergency', 'asap', 'critical', 'important', 'rush']

class WhatsAppBot:
    def __init__(self):
        self.driver = None
        self.pending_messages = []
        self.load_pending_messages()
        
    def load_pending_messages(self):
        """تحميل الرسائل المعلقة"""
        if os.path.exists("pending.json"):
            with open("pending.json", "r", encoding="utf-8") as f:
                self.pending_messages = json.load(f)
    
    def save_pending_messages(self):
        """حفظ الرسائل المعلقة"""
        with open("pending.json", "w", encoding="utf-8") as f:
            json.dump(self.pending_messages, f, ensure_ascii=False, indent=2)
    
    def setup_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        
        self.driver = webdriver.Chrome(options=options)
    
    def is_working_hours(self):
        """هل الآن ساعات العمل (8 صباح - 12 ظهر)؟"""
        current_time = datetime.now().time()
        current_day = datetime.now().weekday()
        
        if current_day == 4:  # الجمعة
            return False
        
        return time(8, 0) <= current_time < time(12, 0)
    
    def detect_language(self, text):
        """كشف لغة الرسالة"""
        try:
            lang = detect(text)
            return 'ar' if lang == 'ar' else 'en'
        except:
            return 'en'
    
    def is_urgent(self, text, language):
        """هل الرسالة عاجلة؟"""
        text_lower = text.lower()
        
        if language == 'ar':
            return any(keyword in text_lower for keyword in URGENT_KEYWORDS_AR)
        else:
            return any(keyword in text_lower for keyword in URGENT_KEYWORDS_EN)
    
    def start(self):
        self.setup_driver()
        
        try:
            print("🤖 نظام إدارة الرسائل مفعل...")
            print("📅 ساعات العمل: 8 صباح - 12 ظهر")
            print("⏳ افتح WhatsApp Web وسكن QR Code")
            
            self.driver.get("https://web.whatsapp.com")
            time_module.sleep(40)
            
            print("✅ متصل! النظام يعمل...")
            
            while True:
                try:
                    self.check_and_reply()
                    
                    # إذا دخل وقت العمل، اعرض الرسائل المعلقة
                    if self.is_working_hours() and self.pending_messages:
                        print("\n📬 تذكرة: لديك رسائل في قائمة الانتظار!")
                        self.show_pending_summary()
                    
                    time_module.sleep(30)
                    
                except Exception as e:
                    print(f"⚠️ خطأ: {e}")
                    time_module.sleep(60)
                    
        except KeyboardInterrupt:
            print("\n❌ تم الإيقاف")
        finally:
            if self.driver:
                self.driver.quit()
    
    def check_and_reply(self):
        """البحث عن الرسائل الجديدة"""
        try:
            unread_chats = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class, 'unread')]"
            )
            
            for chat in unread_chats[:3]:
                try:
                    sender = chat.find_element(By.CLASS_NAME, "qlcra4g0").text
                    
                    chat.click()
                    time_module.sleep(1)
                    
                    # احصل على آخر رسالة
                    messages = self.driver.find_elements(
                        By.XPATH,
                        "//div[contains(@class, 'message-in')]"
                    )
                    
                    if messages:
                        last_msg = messages[-1].text
                        lang = self.detect_language(last_msg)
                        is_urgent = self.is_urgent(last_msg, lang)
                        
                        # ===== التحقق من وقت العمل =====
                        if self.is_working_hours():
                            # ✅ ساعات عمل - لا ترسل شيء (سيرد المستخدم يدويا)
                            print(f"✅ رسالة من {sender} (ساعات عمل - لا رد آلي)")
                        else:
                            # ❌ خارج ساعات عمل
                            
                            # إذا عاجلة، ارسل * أولا
                            if is_urgent:
                                print(f"🔴 رسالة عاجلة من {sender}!")
                                self.send_message("*")
                                time_module.sleep(1)
                            else:
                                print(f"📨 رسالة عادية من {sender} (خارج الدوام)")
                            
                            # ارسل رسالة التوضيح
                            reply = AUTO_REPLY_AR if lang == 'ar' else AUTO_REPLY_EN
                            self.send_message(reply)
                            
                            # احفظ الرسالة
                            self.pending_messages.append({
                                'sender': sender,
                                'message': last_msg,
                                'language': lang,
                                'urgent': is_urgent,
                                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            })
                            self.save_pending_messages()
                            print(f"💾 تم حفظ الرسالة")
                        
                        time_module.sleep(2)
                        
                except Exception as e:
                    print(f"❌ خطأ: {e}")
                    continue
                    
        except Exception as e:
            print(f"⚠️ خطأ عام: {e}")
    
    def show_pending_summary(self):
        """عرض ملخص الرسائل المعلقة"""
        print(f"\n{'='*60}")
        print(f"📋 ملخص الرسائل المنتظرة (عدد: {len(self.pending_messages)})")
        print(f"{'='*60}")
        
        urgent_count = sum(1 for msg in self.pending_messages if msg['urgent'])
        
        for i, msg in enumerate(self.pending_messages, 1):
            tag = "🔴 عاجل" if msg['urgent'] else "📝"
            print(f"{i}. {tag} | من: {msg['sender']} | الوقت: {msg['timestamp']}")
            print(f"   الرسالة: {msg['message'][:60]}...")
        
        print(f"\n📊 الملخص: {len(self.pending_messages)} رسالة ({urgent_count} عاجلة)")
        print(f"{'='*60}\n")
        
        # حذف الرسائل بعد عرضها
        self.pending_messages = []
        self.save_pending_messages()
    
    def send_message(self, message):
        """إرسال رسالة"""
        try:
            msg_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    "//div[@contenteditable='true'][@data-tab='10']"
                ))
            )
            
            msg_input.click()
            msg_input.send_keys(message)
            time_module.sleep(1)
            
            send_btn = self.driver.find_element(
                By.XPATH,
                "//button[@aria-label='Send']"
            )
            send_btn.click()
            
        except Exception as e:
            print(f"❌ خطأ في الإرسال: {e}")

if __name__ == "__main__":
    bot = WhatsAppBot()
    bot.start()
