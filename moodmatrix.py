import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import pandas as pd
import io
import requests
import json
from prophet import Prophet
import uuid
import random

# إعداد الصفحة
st.set_page_config(
    page_title="MoodMatrix™ - Design Your Vibe",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS مستوحى من الخيال العلمي
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Exo+2:wght@400;700;900&display=swap');
    * {font-family: 'Exo 2', sans-serif;}
    .main {background: linear-gradient(135deg, #0F172A, #1E3A8A); color: #DBEAFE; padding: 40px; border-radius: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.8);}
    h1, h2, h3 {background: linear-gradient(90deg, #3B82F6, #A5B4FC); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 900; letter-spacing: -1px; text-shadow: 0 2px 15px rgba(59,130,246,0.6);}
    .stButton>button {background: linear-gradient(90deg, #3B82F6, #A5B4FC); color: #FFFFFF; border-radius: 50px; font-weight: 700; padding: 15px 35px; font-size: 18px; transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); border: none; box-shadow: 0 8px 20px rgba(59,130,246,0.5); text-transform: uppercase;}
    .stButton>button:hover {transform: translateY(-5px) scale(1.05); box-shadow: 0 12px 30px rgba(165,180,252,0.7);}
    .stTextInput>div>div>input {background: rgba(255,255,255,0.1); border: 2px solid #3B82F6; border-radius: 15px; color: #A5B4FC; font-weight: bold; padding: 15px; font-size: 18px; box-shadow: 0 5px 15px rgba(59,130,246,0.3); transition: all 0.3s ease;}
    .stTextInput>div>div>input:focus {border-color: #A5B4FC; box-shadow: 0 5px 20px rgba(165,180,252,0.5);}
    .stSelectbox>label, .stRadio>label {color: #A5B4FC; font-size: 22px; font-weight: 700; text-shadow: 1px 1px 5px rgba(0,0,0,0.5);}
    .stSelectbox>div>div>button {background: rgba(255,255,255,0.1); border: 2px solid #3B82F6; border-radius: 15px; color: #DBEAFE; padding: 15px; font-size: 18px;}
    .stRadio>div {background: rgba(255,255,255,0.05); border-radius: 20px; padding: 20px; box-shadow: 0 5px 20px rgba(0,0,0,0.5);}
    .stMarkdown {color: #BFDBFE; font-size: 18px; line-height: 1.6;}
    .share-btn {background: linear-gradient(90deg, #10B981, #6EE7B7); color: #FFFFFF; border-radius: 50px; padding: 12px 25px; text-decoration: none; transition: all 0.3s ease; box-shadow: 0 5px 15px rgba(16,185,129,0.4); font-size: 16px;}
    .share-btn:hover {transform: translateY(-3px); box-shadow: 0 10px 25px rgba(110,231,183,0.6);}
    .animate-in {animation: fadeInUp 1s forwards; opacity: 0;}
    @keyframes fadeInUp {from {opacity: 0; transform: translateY(20px);} to {opacity: 1; transform: translateY(0);}}
    </style>
""", unsafe_allow_html=True)

# تعريف الحالة الافتراضية
if "language" not in st.session_state:
    st.session_state["language"] = "English"
if "payment_verified" not in st.session_state:
    st.session_state["payment_verified"] = False
if "payment_initiated" not in st.session_state:
    st.session_state["payment_initiated"] = False
if "mood_data" not in st.session_state:
    st.session_state["mood_data"] = None

# NewsAPI Key (مجاني، احصل عليه من newsapi.org)
NEWS_API_KEY = "YOUR_NEWS_API_KEY_HERE"  # سجل في newsapi.org للحصول على مفتاح مجاني

# بيانات PayPal Sandbox
PAYPAL_CLIENT_ID = "AQd5IZObL6YTejqYpN0LxADLMtqbeal1ahbgNNrDfFLcKzMl6goF9BihgMw2tYnb4suhUfprhI-Z8eoC"
PAYPAL_SECRET = "EPk46EBw3Xm2W-R0Uua8sLsoDLJytgSXqIzYLbbXCk_zSOkdzFx8jEbKbKxhjf07cnJId8gt6INzm6_V"
PAYPAL_API = "https://api-m.sandbox.paypal.com"

# دالة لجلب الأخبار من NewsAPI
def fetch_news_mood(mood_words):
    try:
        mood_query = " ".join(mood_words)
        url = f"http://newsapi.org/v2/everything?q={mood_query}&apiKey={NEWS_API_KEY}&pageSize=10"
        response = requests.get(url)
        response.raise_for_status()
        articles = response.json().get("articles", [])
        positive, negative = 0, 0
        for article in articles:
            title = article["title"].lower()
            if "good" in title or "happy" in title or "success" in title:
                positive += 1
            elif "bad" in title or "sad" in title or "fail" in title:
                negative += 1
        total = positive + negative or 1
        return {"positive": int(positive * 100 / total), "negative": int(negative * 100 / total)}
    except Exception as e:
        st.error(f"Failed to fetch news mood: {e}")
        return {"positive": 60, "negative": 40}

# العنوان والترحيب
st.markdown("""
    <h1 style='font-size: 60px; text-align: center; animation: fadeInUp 1s forwards;'>MoodMatrix™</h1>
    <p style='font-size: 24px; text-align: center; animation: fadeInUp 1s forwards; animation-delay: 0.2s;'>
        Design Your Daily Vibe!<br>
        <em>By Anas Hani Zewail • Contact: +201024743503</em>
    </p>
""", unsafe_allow_html=True)

# واجهة المستخدم
st.markdown("<h2 style='text-align: center;'>Scan Your Mood</h2>", unsafe_allow_html=True)
mood_words = st.text_input("Enter 3 Mood Words (e.g., happy calm excited):", "happy calm excited", help="Separate with spaces!")
language = st.selectbox("Select Language:", ["English", "Arabic"])
st.session_state["language"] = language
plan = st.radio("Choose Your Mood Plan:", ["Mood Peek (Free)", "Mood Starter ($3)", "Mood Booster ($7)", "Mood Master ($12)", "Mood Elite ($20/month)"])
st.markdown("""
    <p style='text-align: center;'>
        <strong>Mood Peek (Free):</strong> Quick Mood Scan<br>
        <strong>Mood Starter ($3):</strong> Mood Meter + Basic Report<br>
        <strong>Mood Booster ($7):</strong> Mood Playlist + Full Report<br>
        <strong>Mood Master ($12):</strong> Mood Forecast + Tips<br>
        <strong>Mood Elite ($20/month):</strong> Daily Updates + Alerts
    </p>
""", unsafe_allow_html=True)

# دوال PayPal
def get_paypal_access_token():
    try:
        url = f"{PAYPAL_API}/v1/oauth2/token"
        headers = {"Accept": "application/json", "Accept-Language": "en_US"}
        data = {"grant_type": "client_credentials"}
        response = requests.post(url, headers=headers, auth=(PAYPAL_CLIENT_ID, PAYPAL_SECRET), data=data)
        response.raise_for_status()
        return response.json()["access_token"]
    except Exception as e:
        st.error(f"Failed to connect to PayPal: {e}")
        return None

def create_payment(access_token, amount, description):
    try:
        url = f"{PAYPAL_API}/v1/payments/payment"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {access_token}"}
        payment_data = {
            "intent": "sale",
            "payer": {"payment_method": "paypal"},
            "transactions": [{"amount": {"total": amount, "currency": "USD"}, "description": description}],
            "redirect_urls": {
                "return_url": "https://smartpulse-nwrkb9xdsnebmnhczyt76s.streamlit.app/?success=true",
                "cancel_url": "https://smartpulse-nwrkb9xdsnebmnhczyt76s.streamlit.app/?cancel=true"
            }
        }
        response = requests.post(url, headers=headers, json=payment_data)
        response.raise_for_status()
        for link in response.json()["links"]:
            if link["rel"] == "approval_url":
                return link["href"]
        st.error("Failed to extract payment URL.")
        return None
    except Exception as e:
        st.error(f"Failed to create payment request: {e}")
        return None

# دوال التحليل
def generate_mood_meter(mood_words, language, mood_data):
    try:
        labels = ["Positive", "Negative"] if language == "English" else ["إيجابي", "سلبي"]
        sizes = [mood_data["positive"], mood_data["negative"]]
        colors = ["#3B82F6", "#EF4444"]
        plt.figure(figsize=(8, 6))
        wedges, texts, autotexts = plt.pie(sizes, labels=labels, colors=colors, autopct="%1.1f%%", startangle=90, shadow=True, textprops={'fontsize': 14, 'color': 'white'})
        for w in wedges:
            w.set_edgecolor('#A5B4FC')
            w.set_linewidth(2)
        plt.title(f"{mood_words} Mood Meter", fontsize=18, color="white", pad=20)
        plt.gca().set_facecolor('#0F172A')
        plt.gcf().set_facecolor('#0F172A')
        
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches="tight")
        img_buffer.seek(0)
        plt.close()
        return img_buffer
    except Exception as e:
        st.error(f"Failed to generate mood meter: {e}")
        return None

def generate_mood_forecast(mood_words, language):
    try:
        days = pd.date_range(start="2025-03-03", periods=7).strftime('%Y-%m-%d').tolist()
        trend = [random.randint(40, 80) for _ in range(7)]
        df = pd.DataFrame({'ds': days, 'y': trend})
        df['ds'] = pd.to_datetime(df['ds'])
        model = Prophet(daily_seasonality=True)
        model.fit(df)
        future = model.make_future_dataframe(periods=7)
        forecast = model.predict(future)
        plt.figure(figsize=(10, 6))
        plt.plot(df['ds'], df['y'], label="Current Mood" if language == "English" else "المزاج الحالي", color="#3B82F6", linewidth=2.5)
        plt.plot(forecast['ds'], forecast['yhat'], label="Forecast" if language == "English" else "التوقعات", color="#A5B4FC", linewidth=2.5)
        plt.fill_between(forecast['ds'], forecast['yhat_lower'], forecast['yhat_upper'], color="#A5B4FC", alpha=0.3)
        plt.title(f"{mood_words} 7-Day Mood Forecast", fontsize=18, color="white", pad=20)
        plt.gca().set_facecolor('#0F172A')
        plt.gcf().set_facecolor('#0F172A')
        plt.legend(fontsize=12, facecolor="#0F172A", edgecolor="white", labelcolor="white")
        plt.xticks(color="white", fontsize=10)
        plt.yticks(color="white", fontsize=10)
        
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches="tight")
        img_buffer.seek(0)
        plt.close()
        return img_buffer, "Mood trending up! Keep the vibe alive."
    except Exception as e:
        st.error(f"Failed to generate forecast: {e}")
        return None, None

def generate_report(mood_words, language, mood_data, mood_meter_buffer, forecast_buffer=None, plan="Mood Starter"):
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        style = styles["Normal"]
        style.fontSize = 12
        style.textColor = colors.black
        style.fontName = "Helvetica"

        report = f"MoodMatrix Report: {mood_words}\n"
        report += "=" * 50 + "\n"
        report += f"Plan: {plan}\n"
        report += f"Positive Mood: {mood_data['positive']}%\n"
        report += f"Negative Mood: {mood_data['negative']}%\n"
        if language == "Arabic":
            report = arabic_reshaper.reshape(report)
            report = get_display(report)

        content = [Paragraph(report, style)]
        content.append(Image(mood_meter_buffer, width=400, height=300))
        
        if forecast_buffer and plan in ["Mood Booster ($7)", "Mood Master ($12)", "Mood Elite ($20/month)"]:
            content.append(Image(forecast_buffer, width=400, height=300))
            content.append(Spacer(1, 20))
        
        if plan in ["Mood Master ($12)", "Mood Elite ($20/month)"]:
            content.append(Paragraph("Mood Tip: Try upbeat music like 'Happy' by Pharrell Williams.", style))
        
        doc.build(content)
        buffer.seek(0)
        return buffer.getvalue()
    except Exception as e:
        st.error(f"Failed to generate report: {e}")
        return None

# تشغيل التطبيق
if st.button("Design My Mood!", key="design_mood"):
    with st.spinner("Scanning Your Mood..."):
        mood_words_list = mood_words.split()
        if len(mood_words_list) < 3:
            st.error("Please enter 3 mood words!")
        else:
            mood_data = fetch_news_mood(mood_words_list)
            mood_meter_buffer = generate_mood_meter(mood_words, language, mood_data)
            if mood_meter_buffer:
                st.session_state["mood_data"] = {"mood_meter": mood_meter_buffer.getvalue()}
                st.image(mood_meter_buffer, caption="Mood Meter")
                
                share_url = "https://moodmatrix-<your-id>.streamlit.app/"  # استبدل بـ رابطك الفعلي
                telegram_group = "https://t.me/+K7W_PUVdbGk4MDRk"
                
                st.markdown("<h3 style='text-align: center;'>Share Your Mood!</h3>", unsafe_allow_html=True)
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown(f'<a href="https://api.whatsapp.com/send?text=Check%20my%20mood%20on%20MoodMatrix:%20{share_url}" target="_blank" class="share-btn">WhatsApp</a>', unsafe_allow_html=True)
                with col2:
                    st.markdown(f'<a href="https://t.me/share/url?url={share_url}&text=MoodMatrix%20is%20cosmic!" target="_blank" class="share-btn">Telegram</a>', unsafe_allow_html=True)
                with col3:
                    st.markdown(f'<a href="https://www.facebook.com/sharer/sharer.php?u={share_url}" target="_blank" class="share-btn">Messenger</a>', unsafe_allow_html=True)
                with col4:
                    st.markdown(f'<a href="https://discord.com/channels/@me?message=Explore%20MoodMatrix:%20{share_url}" target="_blank" class="share-btn">Discord</a>', unsafe_allow_html=True)
                
                st.markdown(f"<p style='text-align: center;'>Join our Telegram: <a href='{telegram_group}' target='_blank'>Click Here</a> - Share with 3 friends for a FREE report!</p>", unsafe_allow_html=True)
                
                if plan == "Mood Peek (Free)":
                    st.info("Unlock your full mood matrix with a paid plan!")
                else:
                    if not st.session_state["payment_verified"] and not st.session_state["payment_initiated"]:
                        access_token = get_paypal_access_token()
                        if access_token:
                            amount = {"Mood Starter ($3)": "3.00", "Mood Booster ($7)": "7.00", "Mood Master ($12)": "12.00", "Mood Elite ($20/month)": "20.00"}[plan]
                            approval_url = create_payment(access_token, amount, f"MoodMatrix {plan}")
                            if approval_url:
                                st.session_state["payment_url"] = approval_url
                                st.session_state["payment_initiated"] = True
                                unique_id = uuid.uuid4()
                                st.markdown(f"""
                                    <a href="{approval_url}" target="_blank" id="paypal_auto_link_{unique_id}" style="display:none;">PayPal</a>
                                    <script>
                                        setTimeout(function() {{
                                            document.getElementById("paypal_auto_link_{unique_id}").click();
                                        }}, 100);
                                    </script>
                                """, unsafe_allow_html=True)
                                st.info(f"Mood payment opened for {plan}. Complete it to design your vibe!")
                    elif st.session_state["payment_verified"]:
                        forecast_buffer, reco = generate_mood_forecast(mood_words, language) if plan in ["Mood Booster ($7)", "Mood Master ($12)", "Mood Elite ($20/month)"] else (None, None)
                        if forecast_buffer:
                            st.session_state["mood_data"]["forecast_buffer"] = forecast_buffer.getvalue()
                            st.image(forecast_buffer, caption="7-Day Mood Forecast")
                            st.write(reco)
                        
                        mood_meter_buffer = io.BytesIO(st.session_state["mood_data"]["mood_meter"])
                        forecast_buffer = io.BytesIO(st.session_state["mood_data"]["forecast_buffer"]) if "forecast_buffer" in st.session_state["mood_data"] else None
                        pdf_data = generate_report(mood_words, language, mood_data, mood_meter_buffer, forecast_buffer, plan)
                        if pdf_data:
                            st.download_button(
                                label=f"Download Your {plan.split(' (')[0]} Mood Report",
                                data=pdf_data,
                                file_name=f"{mood_words}_moodmatrix_report.pdf",
                                mime="application/pdf",
                                key="download_report"
                            )
                            st.success(f"{plan.split(' (')[0]} Mood Designed! Share to spread the vibe!")
