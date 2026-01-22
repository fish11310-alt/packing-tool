import streamlit as st
import streamlit.components.v1 as components
import math

# 設定頁面配置
st.set_page_config(page_title="晟崴塑膠-智能裝箱估算系統", layout="wide")

# ==========================================
# 1. 側邊欄：統一輸入區
# ==========================================
with st.sidebar:
    st.header("⚙️ 參數設定")
    
    st.subheader("1. 紙箱尺寸 (內徑 mm)")
    col1, col2, col3 = st.columns(3)
    box_l = col1.number_input("長", value=500, step=10, key="box_l")
    box_w = col2.number_input("寬", value=400, step=10, key="box_w")
    box_h = col3.number_input("高", value=300, step=10, key="box_h")

    st.subheader("2. 成品尺寸 (mm)")
    p_col1, p_col2, p_col3 = st.columns(3)
    prod_l = p_col1.number_input("長", value=120, step=1, key="prod_l")
    prod_w = p_col2.number_input("寬", value=80, step=1, key="prod_w")
    prod_h = p_col3.number_input("高", value=50, step=1, key="prod_h")

    st.subheader("3. 成本與重量資訊")
    unit_weight = st.number_input("成品單重 (g)", value=85.5, step=0.1)
    unit_cost = st.number_input("成品單價 (NTD)", value=15.0, step=0.5)
    
    st.markdown("---")
    st.subheader("4. 擺放策略")
    orientation = st.radio(
        "選擇擺放基準面：",
        ('平放 (長x寬 接觸)', '側放 (長x高 接觸)', '直立 (寬x高 接觸)'),
        index=0
    )

# ==========================================
# 2. Python 後端計算邏輯 (恢復計算功能)
# ==========================================

# 定義不同擺放方式的邏輯
if '平放' in orientation:
    pL, pW, pH = prod_l, prod_w, prod_h
    orient_code = 'flat'
elif '側放' in orientation:
    pL, pW, pH = prod_l, prod_h, prod_w
    orient_code = 'side'
else: # 直立
    pL, pW, pH = prod_w, prod_h, prod_l
    orient_code = 'upright'

# 計算排列 (簡單矩陣，比較旋轉與否)
# 方案 A: 不旋轉
colsA = math.floor(box_l / pL)
rowsA = math.floor(box_w / pW)
countA = colsA * rowsA

# 方案 B: 旋轉 90 度
colsB = math.floor(box_l / pW)
rowsB = math.floor(box_w / pL)
countB = colsB * rowsB

# 取最佳解
if countB > countA:
    final_cols, final_rows = colsB, rowsB
    layer_count = countB
    rotated_visual = 'true' # 傳給 JS 用
    # 用於顯示的尺寸
    display_L, display_W = pW, pL
else:
    final_cols, final_rows = colsA, rowsA
    layer_count = countA
    rotated_visual = 'false'
    display_L, display_W = pL, pW

# 計算垂直層數與總數
layers = math.floor(box_h / pH)
total_count = layer_count * layers

# 計算商業數據
total_weight_kg = (total_count * unit_weight) / 1000
total_cost = total_count * unit_cost

# 計算空間利用率
prod_vol = prod_l * prod_w * prod_h * total_count
box_vol = box_l * box_w * box_h
utilization = (prod_vol / box_vol) * 100 if box_vol > 0 else 0


# ==========================================
# 3. 主畫面顯示
# ==========================================

st.title("📦 晟崴塑膠 - 智能裝箱估算系統")
st.markdown("此工具整合裝箱模擬與成本重量試算，調整左側參數即可即時更新。")

# 顯示關鍵指標 (Metrics)
m1, m2, m3, m4 = st.columns(4)
m1.metric("📦 每箱總數量", f"{total_count} pcs", delta="層數: " + str(layers))
m2.metric("⚖️ 每箱總重量", f"{total_weight_kg:.2f} kg", delta=f"單重: {unit_weight}g")
m3.metric("💰 每箱總成本", f"${total_cost:,.0f}", delta=f"單價: ${unit_cost}")
m4.metric("📊 空間利用率", f"{utilization:.1f}%", delta_color="normal" if utilization < 90 else "inverse")

st.markdown("---")

col_visual, col_details = st.columns([1.5, 1])

with col_details:
    st.subheader("📋 詳細數據")
    st.info(f"""
    **排列方式 ({orientation}):**
    * **單層排列:** {final_cols} (排) x {final_rows} (列)
    * **單層數量:** {layer_count} pcs
    * **堆疊層數:** {layers} 層
    
    **尺寸檢核:**
    * **單層高度:** {pH} mm
    * **總堆疊高:** {layers * pH} mm (剩餘空間: {box_h - (layers * pH)} mm)
    """)
    
    # 重量警示
    if total_weight_kg > 18:
        st.error(f"⚠️ **注意：** 整箱重量 ({total_weight_kg:.1f} kg) 已超過一般搬運建議 (18kg)，建議減少層數或更改包裝。")
    else:
        st.success("✅ 重量在安全搬運範圍內。")

with col_visual:
    st.subheader("📐 裝箱俯視圖 (第一層)")
    
    # ==========================================
    # 4. HTML/JS 視覺化組件 (自動接收 Python 變數)
    # ==========================================
    # 這裡我們使用 Python 的 f-string 將變數直接注入到 JavaScript 中
    html_code = f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ margin: 0; display: flex; justify-content: center; align-items: center; background: #fff; font-family: 'Segoe UI', sans-serif; }}
            .canvas-container {{ position: relative; border: 2px dashed #cbd5e1; padding: 20px; border-radius: 12px; }}
            .legend {{ margin-top: 10px; text-align: center; color: #64748b; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div>
            <div class="canvas-container">
                <canvas id="packingCanvas" width="400" height="350"></canvas>
            </div>
            <div class="legend">
                <span style="display:inline-block; width:10px; height:10px; background:#60a5fa; border:1px solid #1e40af; margin-right:5px;"></span>成品
                <span style="margin-left:15px; display:inline-block; width:10px; height:10px; border:2px solid #334155; margin-right:5px;"></span>紙箱邊界
            </div>
        </div>

        <script>
            // 從 Python 傳入的變數
            const boxL = {box_l};
            const boxW = {box_w};
            
            // 視覺呈現用的長寬 (已經由 Python 判斷過是否旋轉)
            const prodVisualL = {display_L};
            const prodVisualW = {display_W};
            
            const cols = {final_cols};
            const rows = {final_rows};

            function draw() {{
                const canvas = document.getElementById('packingCanvas');
                const ctx = canvas.getContext('2d');
                
                // 自動縮放邏輯
                const maxW = 380;
                const maxH = 330;
                const scale = Math.min((maxW) / boxL, (maxH) / boxW);
                
                const drawBoxL = boxL * scale;
                const drawBoxW = boxW * scale;
                const startX = (canvas.width - drawBoxL) / 2;
                const startY = (canvas.height - drawBoxW) / 2;

                // 清空
                ctx.clearRect(0, 0, canvas.width, canvas.height);

                // 畫紙箱
                ctx.strokeStyle = '#334155';
                ctx.lineWidth = 3;
                ctx.strokeRect(startX, startY, drawBoxL, drawBoxW);

                // 標示紙箱尺寸
                ctx.fillStyle = '#64748b';
                ctx.font = '14px Arial';
                ctx.textAlign = 'center';
                ctx.fillText(boxL + ' mm', canvas.width/2, startY - 8);
                ctx.textAlign = 'left';
                ctx.fillText(boxW + ' mm', startX + drawBoxL + 8, canvas.height/2);

                // 畫產品
                ctx.fillStyle = '#60a5fa';
                ctx.strokeStyle = '#1e40af';
                ctx.lineWidth = 1;

                const drawProdL = prodVisualL * scale;
                const drawProdW = prodVisualW * scale;

                for (let r = 0; r < rows; r++) {{
                    for (let c = 0; c < cols; c++) {{
                        const x = startX + (c * drawProdL);
                        const y = startY + (r * drawProdW);
                        // 留一點間隙
                        const pad = 1; 
                        ctx.fillRect(x + pad, y + pad, drawProdL - 2*pad, drawProdW - 2*pad);
                        ctx.strokeRect(x + pad, y + pad, drawProdL - 2*pad, drawProdW - 2*pad);
                    }}
                }}
            }}
            
            // 執行繪圖
            draw();
        </script>
    </body>
    </html>
    """
    
    # 渲染 HTML
    components.html(html_code, height=450)
