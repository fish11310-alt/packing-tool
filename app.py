import streamlit as st
import math
import pandas as pd
import itertools

# ==========================================
# 1. 網頁基礎設定
# ==========================================
st.set_page_config(page_title="晟崴塑膠-開發工具箱", page_icon="🛠️", layout="wide")

# ==========================================
# 2. 側邊欄：工具選擇菜單
# ==========================================
st.sidebar.title("🛠️ 晟崴開發工具箱")
tool_option = st.sidebar.selectbox(
    "請選擇功能：",
    ["📦 智能裝箱計算機", "⚖️ 塑膠成品重量估算", "📝 待辦事項/備忘錄"]
)
st.sidebar.markdown("---")

# ==========================================
# 3. 工具 A：智能裝箱計算機
# ==========================================
if tool_option == "📦 智能裝箱計算機":
    st.title("📦 智能裝箱計算機")
    st.markdown("針對成品尺寸與重量，自動計算最佳紙箱、成本與**整箱重量**。")
    st.markdown("---")

    # --- 參數設定區 ---
    st.sidebar.header("⚙️ 裝箱參數設定")
    carton_db = {
        'No.2-2': {'L': 570, 'W': 338, 'H': 320, 'price': 24.50, 'div_price': 2.30},
        'No.4':   {'L': 324, 'W': 228, 'H': 226, 'price': 13.80, 'div_price': 1.40},
        'No.8':   {'L': 450, 'W': 306, 'H': 424, 'price': 24.50, 'div_price': 2.00},
        'No.3':   {'L': 570, 'W': 340, 'H': 248, 'price': 21.80, 'div_price': 2.30},
        'No.9':   {'L': 650, 'W': 470, 'H': 460, 'price': 35.00, 'div_price': 3.30},
        'No.10':  {'L': 648, 'W': 468, 'H': 360, 'price': 32.50, 'div_price': 4.00},
        'No.14':  {'L': 392, 'W': 314, 'H': 412, 'price': 19.50, 'div_price': 1.80},
        'No.15':  {'L': 510, 'W': 500, 'H': 416, 'price': 38.00, 'div_price': 2.60},
        'No.15-1':{'L': 502, 'W': 492, 'H': 408, 'price': 31.50, 'div_price': 2.60},
        'No.16':  {'L': 534, 'W': 400, 'H': 340, 'price': 31.00, 'div_price': 3.40},
        'No.17':  {'L': 536, 'W': 400, 'H': 560, 'price': 36.50, 'div_price': 3.40},
    }
    
    deduct_l = st.sidebar.number_input("長度扣除 (mm)", value=15)
    deduct_w = st.sidebar.number_input("寬度扣除 (mm)", value=15)
    deduct_h = st.sidebar.number_input("高度扣除 (mm)", value=20)
    div_thick = st.sidebar.number_input("隔板厚度 (mm)", value=3)
    side_lining = st.sidebar.checkbox("四周圍也要放隔板?", value=False)

    # --- 輸入區 ---
    c1, c2, c3, c4 = st.columns(4)
    p_l = c1.number_input("成品長度 (mm)", value=38.0)
    p_w = c2.number_input("成品寬度 (mm)", value=28.0)
    p_h = c3.number_input("成品高度 (mm)", value=7.2)
    p_weight = c4.number_input("成品單重 (g)", value=5.0, help="請輸入單個成品的重量")

    # --- 計算按鈕 ---
    if st.button("🚀 開始計算", type="primary"):
        results = []
        for name, specs in carton_db.items():
            inner_l = specs['L'] - deduct_l
            inner_w = specs['W'] - deduct_w
            inner_h = specs['H'] - deduct_h
            if side_lining:
                inner_l -= (div_thick * 2)
                inner_w -= (div_thick * 2)

            p_dims = [p_l, p_w, p_h]
            max_qty, min_cost = 0, float('inf')
            best_detail, best_total = "", 0
            
            import itertools
            for p in set(itertools.permutations(p_dims)):
                nl = math.floor(inner_l/p[0])
                nw = math.floor(inner_w/p[1])
                per_layer = nl * nw
                if per_layer == 0: continue
                
                av_h = inner_h - div_thick
                u_h = p[2] + div_thick
                layers = math.floor(av_h/u_h) if av_h >= 0 else 0
                
                qty = per_layer * layers
                if qty > 0:
                    cost = (specs['price'] + (layers+1)*specs['div_price']) / qty
                    if cost < min_cost:
                        min_cost = cost
                        max_qty = qty
                        best_total = specs['price'] + (layers+1)*specs['div_price']
                        best_detail = f"{layers}層(每層{per_layer}) | 共{layers+1}隔板"
            
            if max_qty > 0:
                # 計算總重 (kg)
                total_weight_kg = (max_qty * p_weight) / 1000
                
                results.append({
                    '紙箱': name, 
                    '數量': max_qty, 
                    '單價': min_cost, 
                    '總成本': best_total, 
                    '整箱重(kg)': total_weight_kg,
                    '說明': best_detail
                })
        
        if results:
            df = pd.DataFrame(results).sort_values('單價')
            best = df.iloc[0]
            st.success(f"🏆 推薦：**{best['紙箱']}** | 成本 ${best['單價']:.4f}/pcs | 整箱約 **{best['整箱重(kg)']:.2f} kg**")
            
            st.dataframe(
                df.style.format({
                    '單價': '${:.4f}', 
                    '總成本': '${:.1f}',
                    '整箱重(kg)': '{:.2f} kg'
                }), 
                use_container_width=True
            )
        else:
            st.error("❌ 產品太大，無法裝入任何紙箱")

# ==========================================
# 4. 工具 B：塑膠成品重量估算
# ==========================================
elif tool_option == "⚖️ 塑膠成品重量估算":
    st.title("⚖️ 塑膠成品重量估算器")
    st.info("輸入體積或尺寸，快速估算成品的重量 (g)。")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("1. 選擇材質")
        materials = {
            "PP (聚丙烯)": 0.91, "ABS (丙烯腈)": 1.05, "PC (聚碳酸酯)": 1.20,
            "PA66 (尼龍)": 1.14, "PMMA (壓克力)": 1.19, "POM (塑鋼)": 1.41, "PVC (硬質)": 1.40
        }
        mat_name = st.selectbox("請選擇材質", list(materials.keys()))
        density = st.number_input("密度 (g/cm³)", value=materials[mat_name], format="%.3f")

    with col2:
        st.subheader("2. 輸入體積")
        calc_mode = st.radio("計算方式", ["直接輸入體積", "輸入長寬高(矩形)"])
        volume = 0.0
        if calc_mode == "直接輸入體積":
            volume = st.number_input("體積 (cm³ / cc)", value=10.0)
        else:
            l = st.number_input("長 (mm)", value=100.0)
            w = st.number_input("寬 (mm)", value=50.0)
            h = st.number_input("厚 (mm)", value=2.0)
            volume = (l * w * h) / 1000 

    st.markdown("---")
    # 這裡就是容易出錯的地方，請確保複製時這些縮排都有保留
    if st.button("計算重量"):
        weight = volume * density
        st.metric(label="預估重量", value=f"{weight:.2f} g")
        st.write(f"若模具為 1模4穴，單次射出量約為： **{weight*4:.2f} g**")

# ==========================================
# 5. 工具 C：簡單備忘錄
# ==========================================
elif tool_option == "📝 待辦事項/備忘錄":
    st.title("📝 開發部待辦事項")
    st.write("這是一個簡單的暫存區。")
    user_input = st.text_area("寫下今天的筆記...", height=150)
    if user_input:
        st.warning("⚠️ 注意：這裡的筆記重新整理網頁後會消失。")
