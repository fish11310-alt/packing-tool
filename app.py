import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import math

# 設定頁面配置
st.set_page_config(page_title="晟崴塑膠-智能裝箱選型系統", layout="wide")

# ==========================================
# 0. 定義公司標準紙箱資料庫 (可在此擴充)
# ==========================================
STANDARD_BOXES = [
    {"name": "標準A規箱 (大)", "L": 580, "W": 480, "H": 400},
    {"name": "標準B規箱 (中)", "L": 500, "W": 400, "H": 300},
    {"name": "標準C規箱 (小)", "L": 400, "W": 300, "H": 250},
    {"name": "長型特規箱", "L": 600, "W": 300, "H": 300},
    {"name": "扁平特規箱", "L": 500, "W": 500, "H": 200},
]

# ==========================================
# 1. 核心計算函數 (封裝邏輯以重複使用)
# ==========================================
def calculate_packing(box_l, box_w, box_h, prod_l, prod_w, prod_h):
    """
    計算單一紙箱在三種擺放方式下的最佳解
    回傳：(總數量, 最佳擺放方式描述, 變數字典)
    """
    best_count = -1
    best_info = {}
    
    # 定義三種擺放策略
    strategies = [
        ('平放 (LxW)', prod_l, prod_w, prod_h, 'flat'),
        ('側放 (LxH)', prod_l, prod_h, prod_w, 'side'),
        ('直立 (WxH)', prod_w, prod_h, prod_l, 'upright')
    ]

    for label, pL, pW, pH, code in strategies:
        # 檢查尺寸是否塞得進去
        if pL > box_l or pW > box_w or pH > box_h:
            continue

        # 方案 A: 不旋轉
        colsA = math.floor(box_l / pL)
        rowsA = math.floor(box_w / pW)
        countA = colsA * rowsA

        # 方案 B: 旋轉 90 度
        colsB = math.floor(box_l / pW)
        rowsB = math.floor(box_w / pL)
        countB = colsB * rowsB

        # 取該層最佳解
        if countB > countA:
            layer_count = countB
            cols, rows = colsB, rowsB
            vis_L, vis_W = pW, pL # 視覺用的長寬
        else:
            layer_count = countA
            cols, rows = colsA, rowsA
            vis_L, vis_W = pL, pW # 視覺用的長寬
        
        # 計算垂直層數
        layers = math.floor(box_h / pH)
        total = layer_count * layers
        
        # 記錄最佳解
        if total > best_count:
            best_count = total
            best_info = {
                'count': total,
                'layers': layers,
                'layer_count': layer_count,
                'orientation_label': label,
                'orientation_code': code,
                'cols': cols,
                'rows': rows,
                'vis_L': vis_L,
                'vis_W': vis_W,
                'pH': pH
            }
            
    return best_count, best_info

# ==========================================
# 2. 側邊欄：只輸入產品資訊
# ==========================================
with st.sidebar:
    st.header("1. 產品規格輸入")
    
    st.subheader("成品尺寸 (mm)")
    p_col1, p_col2, p_col3 = st.columns(3)
    prod_l = p_col1.number_input("長", value=120, step=1)
    prod_w = p_col2.number_input("寬", value=80, step=1)
    prod_h = p_col3.number_input("高", value=50, step=1)

    st.subheader("成本與重量")
    unit_weight = st.number_input("單重 (g)", value=85.5, step=0.1)
    unit_cost = st.number_input("單價 ($)", value=15.0, step=0.5)
    
    st.info("💡 提示：系統會自動測試所有紙箱，並找出每個紙箱「裝最多」的擺放方式。")

# ==========================================
# 3. 主畫面：列表與詳情
# ==========================================
st.title("📦 晟崴塑膠 - 智能裝箱選型系統")

# --- 步驟 A: 批次計算所有紙箱 ---
results = []
for box in STANDARD_BOXES:
    count, info = calculate_packing(box['L'], box['W'], box['H'], prod_l, prod_w, prod_h)
    
    if count > 0:
        # 計算附屬數據
        total_weight = (count * unit_weight) / 1000
        total_cost = count * unit_cost
        box_vol = box['L'] * box['W'] * box['H']
        prod_vol = prod_l * prod_w * prod_h * count
        utilization = (prod_vol / box_vol) * 100 if box_vol > 0 else 0
        
        results.append({
            "紙箱名稱": box['name'],
            "每箱數量 (pcs)": count,
            "最佳擺放": info['orientation_label'],
            "總重量 (kg)": round(total_weight, 2),
            "空間利用率 (%)": round(utilization, 1),
            "總成本 ($)": total_cost,
            # 隱藏欄位 (用於後續繪圖)
            "_L": box['L'], "_W": box['W'], "_H": box['H'], "_info": info
        })

if not results:
    st.error("❌ 產品尺寸過大，無法裝入任何現有標準紙箱，請檢查尺寸。")
    st.stop()

# 轉為 DataFrame 並排序 (數量由多到少)
df = pd.DataFrame(results)
df = df.sort_values(by="每箱數量 (pcs)", ascending=False).reset_index(drop=True)

# --- 步驟 B: 顯示互動表格 ---
st.subheader("📋 標準紙箱裝箱試算列表")
st.caption("請點選下方表格中的一行，以查看詳細排列圖：")

# 使用 dataframe 的選取功能 (on_select)
event = st.dataframe(
    df,
    use_container_width=True,
    hide_index=True,
    column_order=["紙箱名稱", "每箱數量 (pcs)", "總重量 (kg)", "空間利用率 (%)", "最佳擺放"],
    selection_mode="single-row",
    on_select="rerun"  # 點選後重新執行以顯示詳情
)

# --- 步驟 C: 根據選取顯示詳情 ---
# 取得選取的列索引
selected_rows = event.selection.rows

if len(selected_rows) > 0:
    idx = selected_rows[0]
    selected_data = df.iloc[idx]
    
    # 提取繪圖所需數據
    box_name = selected_data["紙箱名稱"]
    box_l = selected_data["_L"]
    box_w = selected_data["_W"]
    info = selected_data["_info"]
    
    st.markdown("---")
    st.header(f"🔍 詳細分析：{box_name}")
    
    # 顯示 Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📦 每箱數量", f"{selected_data['每箱數量 (pcs)']} pcs", delta=f"{info['layers']} 層")
    m2.metric("⚖️ 總重量", f"{selected_data['總重量 (kg)']} kg", 
              delta="⚠️ 超重" if selected_data['總重量 (kg)'] > 18 else "OK",
              delta_color="inverse" if selected_data['總重量 (kg)'] > 18 else "normal")
    m3.metric("💰 總成本", f"${selected_data['總成本 ($)']:,.0f}")
    m4.metric("📊 利用率", f"{selected_data['空間利用率 (%)']}%")

    col_visual, col_text = st.columns([1.5, 1])
    
    with col_text:
        st.success(f"✅ 系統建議最佳擺放：**{info['orientation_label']}**")
        st.info(f"""
        **紙箱規格:** {box_l} x {box_w} x {selected_data['_H']} mm
        
        **堆疊細節:**
        * 單層排列: {info['cols']} (排) x {info['rows']} (列)
        * 單層數量: {info['layer_count']} pcs
        * 堆疊層數: {info['layers']} 層
        * 堆疊高度: {info['layers'] * info['pH']} mm (剩餘 {selected_data['_H'] - (info['layers'] * info['pH'])} mm)
        """)

    with col_visual:
        st.subheader("📐 裝箱俯視示意圖")
        
        # 注入變數到 HTML
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
                const boxL = {box_l};
                const boxW = {box_w};
                const prodVisualL = {info['vis_L']};
                const prodVisualW = {info['vis_W']};
                const cols = {info['cols']};
                const rows = {info['rows']};

                function draw() {{
                    const canvas = document.getElementById('packingCanvas');
                    const ctx = canvas.getContext('2d');
                    
                    const maxW = 380;
                    const maxH = 330;
                    const scale = Math.min((maxW) / boxL, (maxH) / boxW);
                    
                    const drawBoxL = boxL * scale;
                    const drawBoxW = boxW * scale;
                    const startX = (canvas.width - drawBoxL) / 2;
                    const startY = (canvas.height - drawBoxW) / 2;

                    ctx.clearRect(0, 0, canvas.width, canvas.height);

                    // 畫紙箱
                    ctx.strokeStyle = '#334155';
                    ctx.lineWidth = 3;
                    ctx.strokeRect(startX, startY, drawBoxL, drawBoxW);

                    // 標示尺寸
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
                            const pad = 1; 
                            ctx.fillRect(x + pad, y + pad, drawProdL - 2*pad, drawProdW - 2*pad);
                            ctx.strokeRect(x + pad, y + pad, drawProdL - 2*pad, drawProdW - 2*pad);
                        }}
                    }}
                }}
                draw();
            </script>
        </body>
        </html>
        """
        components.html(html_code, height=450)

else:
    # 若尚未選取任何列
    st.info("👆 請在上方列表中點選一個紙箱方案，即可在此處查看詳細圖解與分析。")
