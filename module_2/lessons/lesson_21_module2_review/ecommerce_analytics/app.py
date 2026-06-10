import streamlit as st

st.set_page_config(
    page_title="ShopHub",
    page_icon="🛒",
    layout="wide"
)

st.title("🛒 ShopHub")

st.markdown("""
## Два підходи:

### 🛒 Каталог
- простий підхід
- функції
- фільтри
- товари

---

### 📊 Аналітика
- класи
- analyzer.py
- метрики
- аналітика

⬅️ Обери сторінку зліва
""")
