import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import requests

# --- 1. 基础配置 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(current_dir, 'protein_vs_fat.csv')
st.set_page_config(page_title="AI Nutrition Pro", page_icon="🥗", layout="wide")

# --- 2. AI 点评逻辑 ---
def get_ai_advice(food_name, protein, fat):
    api_url = "https://api.deepseek.com/chat/completions"
    api_key = "sk-05cc5c6c897f42ca8c74bde673a157e1" 
    
    prompt = (f"你是一位专业且略带幽默的健身教练。请评价食物：{food_name}。"
              f"每100g含蛋白质{protein}g，脂肪{fat}g。"
              f"请用一句话给出你的专业评价，并告诉大家适不适合在减脂期吃。")
    
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.8
    }
    try:
        response = requests.post(api_url, json=data, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"AI 暂时不理你 (Error: {response.status_code})"
    except:
        return "AI 营养师去撸铁了，请稍后再试。"

# --- 3. 数据加载 ---
@st.cache_data
def load_data():
    return pd.read_csv(csv_path) if os.path.exists(csv_path) else pd.DataFrame()

# --- 4. 主界面逻辑 ---
df = load_data()
st.title("🥗 AI 智能营养实验室")

if not df.empty:
    search_term = st.sidebar.text_input("🔍 Search Food:", "Chicken")
    filtered_df = df[df['Food_Name'].str.contains(search_term, case=False)].copy()

    if not filtered_df.empty:
        top_food = filtered_df.iloc[0]
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader(f"📊 Indicators: {top_food['Food_Name'][:30]}")
            m1, m2 = st.columns(2)
            m1.metric("Protein (g)", top_food['Protein_Value'])
            m2.metric("Fat (g)", top_food['Fat_Value'])
            
            st.info("💡 **AI Coach Advice:**")
            advice = get_ai_advice(top_food['Food_Name'], top_food['Protein_Value'], top_food['Fat_Value'])
            st.write(advice)

        with col2:
            st.subheader("🔥 Energy Distribution")
            # 饼图绘制 (方案一：使用英文标签)
            fig, ax = plt.subplots(figsize=(6, 4))
            kcal_p = top_food['Protein_Value'] * 4
            kcal_f = top_food['Fat_Value'] * 9
            
            # 使用英文标签 labels，绝不会乱码
            ax.pie([kcal_p, kcal_f], 
                   labels=['Protein Kcal', 'Fat Kcal'], 
                   autopct='%1.1f%%', 
                   colors=['#2ecc71', '#ff7f0e'],
                   startangle=140)
            
            # 设置背景透明更符合 Streamlit 暗色模式
            fig.patch.set_alpha(0)
            st.pyplot(fig)
            st.caption("Legend: Green = Protein energy, Orange = Fat energy")

        st.divider()
        st.dataframe(filtered_df[['Food_Name', 'Protein_Value', 'Fat_Value']])
    else:
        st.warning("No matches found.")
