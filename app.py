import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import requests
from fpdf import FPDF


# --- 1. 核心：AI 营养分析逻辑 ---
def get_ai_advice(food_name, protein, fat, region):
    api_url = "https://api.deepseek.com/chat/completions"

    # 安全读取 Secrets 里的 Key
    try:
        api_key = st.secrets["DEEPSEEK_API_KEY"]
    except:
        return "Please configure DEEPSEEK_API_KEY in Streamlit Secrets."

    # 妈妈建议的：地域 + 产地 + 习惯提示词
    prompt = f"""
    你是一位精通中国饮食文化的营养专家。
    当前食物：{food_name}（蛋白质：{protein}g，脂肪：{fat}g）。
    当前用户地域习惯：{region}。
    请提供：
    1. 该食物在中国的主要产地或地标。
    2. 针对{region}人群的健康食用建议。
    3. 一句专业的营养评价。
    注意：请用简洁的中文回答，不超过150字。
    """

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    try:
        response = requests.post(api_url, json=data, headers=headers, timeout=15)
        return response.json()['choices'][0]['message']['content']
    except:
        return "AI coach is busy now. Please try again later."


# --- 2. 导出 PDF 逻辑 ---
def create_pdf_report(name, p, f, advice):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Nutrition Analysis Report", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Food: {name}", ln=True)
    pdf.cell(200, 10, txt=f"Protein: {p}g", ln=True)
    pdf.cell(200, 10, txt=f"Fat: {f}g", ln=True)
    pdf.ln(5)
    pdf.multi_cell(0, 10, txt=f"Advice: {advice.encode('latin-1', 'ignore').decode('latin-1')}")
    return pdf.output(dest='S').encode('latin-1')


# --- 3. 页面布局 ---
st.set_page_config(page_title="AI Nutrition Lab", layout="wide")
st.title("🥗 AI 智能营养实验室")

# 侧边栏：地域选择
st.sidebar.header("Settings")
region = st.sidebar.selectbox(
    "📍 选择饮食地域习惯：",
    ["川渝地区 (Heavy Spice)", "北方地区 (High Salt/Carb)", "广东地区 (Light/Herbal)", "江浙沪 (Sweet/Fresh)"]
)

# 加载数据 (假设你的 CSV 还在)
csv_path = os.path.join(os.path.dirname(__file__), 'protein_vs_fat.csv')
if os.path.exists(csv_path):
    df = pd.read_csv(csv_path)
    search_term = st.text_input("🔍 搜索食物名称 (如 Chicken):", "Chicken")

    filtered_df = df[df['Food_Name'].str.contains(search_term, case=False)]

    if not filtered_df.empty:
        top_food = filtered_df.iloc[0]

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📊 Data & AI Advice")
            st.metric("Protein", f"{top_food['Protein_Value']}g")
            st.metric("Fat", f"{top_food['Fat_Value']}g")

            # 获取 AI 建议
            with st.spinner('AI is thinking...'):
                advice = get_ai_advice(top_food['Food_Name'], top_food['Protein_Value'], top_food['Fat_Value'], region)
            st.success(advice)

            # PDF 下载按钮
            report_data = create_pdf_report(top_food['Food_Name'], top_food['Protein_Value'], top_food['Fat_Value'],
                                            advice)
            st.download_button("📥 Download PDF Report", report_data, f"{top_food['Food_Name']}_report.pdf",
                               "application/pdf")

        with col2:
            st.subheader("🔥 Energy Chart")
            fig, ax = plt.subplots()
            ax.pie([top_food['Protein_Value'] * 4, top_food['Fat_Value'] * 9], labels=['Protein', 'Fat'],
                   autopct='%1.1f%%', colors=['#2ecc71', '#ff7f0e'])
            st.pyplot(fig)
else:
    st.error("CSV file not found! Please check your GitHub repository.")
