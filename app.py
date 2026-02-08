import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
import requests

# --- 1. 基础配置 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(current_dir, 'protein_vs_fat.csv')
st.set_page_config(page_title="AI 智能营养分析师", page_icon="🤖", layout="wide")


# --- 2. AI 逻辑 (严格对齐版) ---
def get_ai_advice(food_name, protein, fat):
    api_url = "https://api.deepseek.com/chat/completions"
    api_key = "sk-05cc5c6c897f42ca8c74bde673a157e1"  # 你的密钥已填入

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
        # 如果返回 401 说明密钥错了，如果 404 说明地址错了
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"AI 暂时不理你 (错误码: {response.status_code})"
    except Exception as e:
        return f"连接 AI 失败: {e}"


# --- 3. 图表中文显示终极补丁 ---
import matplotlib.font_manager as fm

# 解决负号显示
plt.rcParams['axes.unicode_minus'] = False 

def set_chinese_font():
    # 方案 A: 尝试 Linux 云端常用中文字体路径
    linux_fonts = [
        '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
        '/usr/share/fonts/truetype/arphic/uming.ttc'
    ]
    for font in linux_fonts:
        if os.path.exists(font):
            plt.rcParams['font.sans-serif'] = ['WenQuanYi Zen Hei']
            return fm.FontProperties(fname=font)
            
    # 方案 B: 尝试 Windows 本地路径
    win_font = r'C:\Windows\Fonts\msyh.ttc'
    if os.path.exists(win_font):
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
        return fm.FontProperties(fname=win_font)
    
    # 方案 C: 如果都找不到，使用默认并打印警告
    return fm.FontProperties()

prop = set_chinese_font()


@st.cache_data
def load_data():
    return pd.read_csv(csv_path) if os.path.exists(csv_path) else pd.DataFrame()


# --- 4. 主程序 (注意缩进) ---
try:
    df = load_data()
    if not df.empty:
        st.title("🤖 AI 智能营养实验室")
        search_term = st.sidebar.text_input("🔍 搜索食品关键词:", "Beef")
        filtered_df = df[df['Food_Name'].str.contains(search_term, case=False)].copy()

        if not filtered_df.empty:
            top_food = filtered_df.iloc[0]
            col1, col2 = st.columns([1, 1])

            with col1:
                st.subheader(f"📊 核心指标: {top_food['Food_Name'][:40]}")
                m1, m2 = st.columns(2)
                m1.metric("蛋白质 (g)", top_food['Protein_Value'])
                m2.metric("脂肪 (g)", top_food['Fat_Value'])

                st.info("💡 **AI 营养师点评：**")
                # 调用 AI 函数
                advice = get_ai_advice(top_food['Food_Name'], top_food['Protein_Value'], top_food['Fat_Value'])
                st.write(advice)

            with col2:
                st.subheader("🔥 能量占比分析")
                fig, ax = plt.subplots(figsize=(6, 4))
                kcal_p, kcal_f = top_food['Protein_Value'] * 4, top_food['Fat_Value'] * 9
                ax.pie([kcal_p, kcal_f], labels=['蛋白质热量', '脂肪热量'],
                       autopct='%1.1f%%', colors=['#2ecc71', '#ff7f0e'],
                       textprops={'fontproperties': prop}, startangle=140)
                st.pyplot(fig)

            st.divider()
            st.dataframe(filtered_df[['Food_Name', 'Protein_Value', 'Fat_Value']], use_container_width=True)
        else:
            st.warning("没找到相关食物。")
    else:
        st.error("无法加载 CSV 文件，请检查路径。")

except Exception as main_e:
    st.error(f"发生致命错误: {main_e}")


