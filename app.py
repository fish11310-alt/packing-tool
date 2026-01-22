import streamlit as st
import math
import pandas as pd
import itertools

# ==========================================
# 1. 設定網頁標題與版面
# ==========================================
st.set_page_config(page_title="晟崴塑膠-裝箱計算機", page_icon="📦")
st.title("📦 晟崴塑膠 - 智能裝箱計算機")
st.markdown("### 輸入成品尺寸，自動計算最佳紙箱與成本")

# ==========================================
# 2. 側邊欄：參數設定 (讓畫面保持乾淨)
# ==========================================
st.sidebar.header("⚙️ 參數設定")

# 這裡是可以讓您隨時調整紙箱價格的地方
# 如果價格變動，直接修改這裡的數字即可
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

# 顯示目前的紙箱價格表在側邊欄供參考
if st.sidebar.checkbox("顯示目前紙箱單價表"):
    st.sidebar.json(carton_db)

# 設定扣除厚度
deduct_l = st.sidebar.number_input("長度扣除 (mm)", value=15)
deduct_w = st.sidebar.number_input("寬度扣除 (mm)", value=15)
deduct_h = st.sidebar.number_input("高度扣除 (mm)", value=20)
div_thick = st.sidebar.number_input("隔板厚度 (mm)", value=3)
side_lining = st.sidebar.checkbox("四周圍也要放隔板?", value=False)

# ==========================================
# 3. 主畫面：輸入區域
# ==========================================
col1, col2, col3 = st.columns(3)
with col1:
    p_l = st.number_input("成品長度 (mm)", value=38.0, step=0.1)
with col2:
    p_w = st.number_input("成品寬度 (mm)", value=28.0, step=0.1)
with col3:
    p_h = st.number_input("成品高度 (mm)", value=7.2, step=0.1)

# ==========================================
# 4. 計算邏輯 (按下按鈕才執行)
# ==========================================
if st.button("🚀 開始計算", use_container_width=True):
    results = []
    
    # 遍歷每一個紙箱
    for name, specs in carton_db.items():
        # 計算內徑
        inner_l = specs['L'] - deduct_l
        inner_w = specs['W'] - deduct_w
        inner_h = specs['H'] - deduct_h
        
        # 若有側面隔板，再扣除
        if side_lining:
            inner_l -= (div_thick * 2)
            inner_w -= (div_thick * 2)

        p_dims = [p_l, p_w, p_h]
        max_qty = 0
        min_cost_pcs = float('inf')
        best_details = ""
        best_total_cost = 0
        
        # 排列組合計算
        permutations = list(itertools.permutations(p_dims))
        unique_permutations = set(permutations)

        for p in unique_permutations:
            # p[0]=長邊擺放, p[1]=寬邊擺放, p[2]=垂直堆疊
            num_l = math.floor(inner_l / p[0])
            num_w = math.floor(inner_w / p[1])
            per_layer_qty = num_l * num_w
            
            if per_layer_qty == 0:
                continue

            # 高度計算 (含隔板)
            available_h_space = inner_h - div_thick
            unit_h_space = p[2] + div_thick
            
            if available_h_space < 0:
                num_layers = 0
            else:
                num_layers = math.floor(available_h_space / unit_h_space)
            
            total_qty = per_layer_qty * num_layers
            
            if total_qty > 0:
                div_count = num_layers + 1
                total_box_cost = specs['price'] + (div_count * specs['div_price'])
                cost_pcs = total_box_cost / total_qty
                
                if cost_pcs < min_cost_pcs:
                    min_cost_pcs = cost_pcs
                    max_qty = total_qty
                    best_total_cost = total_box_cost
                    best_details = f"{num_layers}層 (每層{per_layer_qty}) | 共{div_count}隔板"
        
        if max_qty > 0:
            results.append({
                '紙箱編號': name,
                '裝箱數': max_qty,
                '每PCS成本': round(min_cost_pcs, 4),
                '整箱總成本': round(best_total_cost, 1),
                '排列方式詳情': best_details
            })
    
    # ==========================================
    # 5. 顯示結果
    # ==========================================
    if results:
        df = pd.DataFrame(results)
        # 依照成本排序
        df = df.sort_values(by='每PCS成本')
        
        # 找出冠軍
        best_box = df.iloc[0]
        
        st.success(f"🏆 最佳選擇： **{best_box['紙箱編號']}** (每PCS成本 ${best_box['每PCS成本']})")
        
        # 顯示互動式表格
        st.dataframe(
            df,
            column_config={
                "每PCS成本": st.column_config.NumberColumn(format="$%.4f"),
                "整箱總成本": st.column_config.NumberColumn(format="$%.1f"),
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.error("⚠️ 計算失敗：產品尺寸過大，無法裝入任何現有紙箱。")
