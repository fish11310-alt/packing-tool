import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import math

# 設定頁面配置
st.set_page_config(page_title="晟崴塑膠-智能裝箱選型系統", layout="wide")

# ==========================================
# 0. 定義公司標準紙箱資料庫 (依據報價單建立)
# ==========================================
# 注意：這裡輸入的是 PDF 上的「外徑」尺寸，計算時會自動扣除厚度
STANDARD_BOXES_RAW = [
    {"name": "方北特專用箱", "L": 564, "W": 424, "H": 362},
    {"name": "NO.2-2 紙箱", "L": 570, "W": 338, "H": 320},
    {"name": "NO.3 紙箱",   "L": 570, "W": 340, "H": 248},
    {"name": "NO.4 紙箱",   "L": 324, "W": 228, "H": 226},
    {"name": "NO.8 紙箱",   "L": 450, "W": 306, "H": 424},
    {"name": "NO.9 紙箱",   "L": 650, "W": 470, "H": 460},
    {"name": "NO.10 紙箱",  "L": 648, "W": 468, "H": 360},
    {"name": "NO.14 紙箱",  "L": 392, "W": 314, "H": 412},
    {"name": "NO.15-1 紙箱","L": 502, "W": 492, "H": 408},
    {"name": "NO.16 紙箱",  "L": 534, "W": 400, "H": 340},
    {"name": "NO.17 紙箱",  "L": 536, "W": 400, "H": 560},
]

# ==========================================
# 1. 核心計算函數
# ==========================================
def calculate_packing(box_ext_l, box_ext_w, box_ext_h, prod_l, prod_w, prod_h, box_thickness, divider_thickness):
    """
    計算單一紙箱在三種擺放方式下的最佳解
    """
    # 1. 轉換為內徑 (扣除五層箱厚度)
    box_l = box_ext_l - box_thickness
    box_w = box_ext_w - box_thickness
    box_h = box_ext_h - box_thickness # 高度也要扣，避免蓋不起來
    
    # 若扣除後尺寸不合理，回傳 0
    if box_l <= 0 or box_w <= 0 or box_h <= 0:
        return 0, {}

    best_count = -1
    best_info = {}
    
    # 定義三種擺放策略
    strategies = [
        ('平放 (LxW)', prod_l, prod_w, prod_h, 'flat'),
        ('側放 (LxH)', prod_l, prod_h, prod_w, 'side'),
        ('直立 (WxH)', prod_w, prod_h, prod_l, 'upright')
    ]

    for label, pL, pW, pH, code in strategies:
        # 檢查單一產品是否塞得進內徑
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
            vis_L, vis_W = pW, pL 
        else:
            layer_count = countA
            cols, rows = colsA, rowsA
            vis_L, vis_W = pL, pW 
        
        # --- 關鍵修正：計算垂直層數 (考慮隔板) ---
        # 公式： 層數 * 產品高 + (層數 - 1) * 隔板厚 <= 紙箱內高
        # 移項推導 => 層數 * (產品高 + 隔板厚) <= 紙箱內高 + 隔板厚
        if divider_thickness > 0:
            layers = math.floor( (box_h + divider_thickness) / (pH + divider_thickness) )
        else:
            layers = math.floor(box_h / pH)
            
        # 確保至少能放一層 (如果一層都放不下前面檢查應該擋掉了，但保險起見)
        layers = max(1, layers)
        
        # 再次檢查高度是否真的足夠 (雙重確認)
        total_stack_height = (layers * pH) + ((layers - 1) * divider_thickness)
        if total_stack_height > box_h:
            layers -= 1 # 減一層
        
        if layers < 1: continue

        total = layer_count * layers
        
        # 記錄最佳解
        if total > best_count:
            best_count = total
            best_info = {
                'count': total,
                'layers': layers,
                'layer_count': layer_count,
                'orientation_label': label,
                'cols': cols,
                'rows': rows,
                'vis_L': vis_L,
                'vis_W': vis_W,
                'pH': pH,
                'total_stack_h': (layers * pH) + (max(0, layers-1) * divider_thickness),
                'box_in_h': box_h # 紀錄內徑高供參考
            }
            
    return best_count, best_info

# ==========================================
# 2. 側邊欄：輸入區
# ==========================================
with st.sidebar:
    st.title("⚙️ 參數設定")
    
    st.header("1. 產品規格")
    p_col1, p_col2, p_col3 = st.columns(3)
    prod_l = p_col1.number_input("長", value=120, step=1)
    prod_w = p_col2.number_input("寬", value=80, step=1)
    prod_h = p_col3.number_input("高", value=50, step=1)

    st.header("2. 包材係數")
    box_thickness = st.number_input("5層箱扣除厚度 (mm)", value=10, step=1, help="計算內徑時，長寬高會各扣除此數值。")
    divider_thickness = st.number_input("層間隔板厚度 (mm)", value=3, step=1, help="每層產品中間會加上此厚度的隔板。")

    st.header("3. 成本與重量")
    unit_weight = st.number_input("單重 (g)", value=85.5, step=0.1)
    unit_cost = st.number_input("單價 ($)", value=15.0, step=0.5)
    
    st.info("💡 系統已載入 11 款標準紙箱 (含方北特、NO.2-17系列)，並依據外徑自動計算內徑。")

# ==========================================
# 3. 主畫面
# ==========================================
st.title("📦 晟崴塑膠 - 智能裝箱選型系統")
st.caption(f"目前設定：紙箱壁厚扣除 {box_thickness}mm | 層間隔板 {divider_thickness}mm")

# --- 步驟 A: 批次計算 ---
results = []
for box in STANDARD_BOXES_RAW:
    count, info = calculate_packing(box['L'], box['W'], box['H'], prod_l, prod_w, prod_h, box_thickness, divider_thickness)
    
    if count > 0:
        total_weight = (count * unit_weight) / 1000
        total_cost = count * unit_cost
        
        # 顯示名稱包含規格，方便核對
        display_name = f"{box['name']} ({box['L']}x{box['W']}x{box['H']})"
        
        # 空間利用率 (以內徑體積計算)
        box_in_vol = (box['L']-box_thickness) * (box['W']-box_thickness) * (box['H']-box_thickness)
        prod_vol = prod_l * prod_w * prod_h * count
        utilization = (prod_vol / box_in_vol) * 100 if box_in_vol > 0 else 0
        
        results.append({
            "紙箱規格": display_name,
            "每箱數量": count,
            "最佳擺放": info['orientation_label'],
            "總重量 (kg)": round(total_weight, 2),
            "利用率 (%)": round(utilization, 1),
            "總成本 ($)": total_cost,
            "_raw": box, "_info": info # 隱藏欄位
        })

if not results:
    st.error("❌ 產品尺寸過大，現有紙箱扣除壁厚後皆無法裝入。")
    st.stop()

# 轉為 DataFrame 並排序
df = pd.DataFrame(results)
df = df.sort_values(by="每箱數量", ascending=False).reset_index(drop=True)

# --- 步驟 B: 互動表格 ---
st.subheader("📋 裝箱試算列表 (由多到少排序)")
st.caption("點選表格任一行以查看堆疊詳情：")

event = st.dataframe(
    df,
    use_container_width=True,
    hide_index=True,
    column_order=["紙箱規格", "每箱數量", "總重量 (kg)", "利用率 (%)", "最佳擺放"],
    selection_mode="single-row",
    on_select="rerun"
)

# --- 步驟 C: 詳細圖解 ---
if len(event.selection.rows) > 0:
    idx = event.selection.rows[0]
    selected_data = df.iloc[idx]
    info = selected_data["_info"]
    raw_box = selected_data["_raw"]
    
    st.markdown("---")
    st.header(f"🔍 分析結果：{raw_box['name']}")
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📦 每箱數量", f"{selected_data['每箱數量']} pcs", delta=f"{info['layers']} 層")
    m2.metric("⚖️ 總重量", f"{selected_data['總重量 (kg)']} kg", 
              delta="⚠️ 超重" if selected_data['總重量 (kg)'] > 18 else "OK",
              delta_color="inverse" if selected_data['總重量 (kg)'] > 18 else "normal")
    m3.metric("💰 總成本", f"${selected_data['總成本 ($)']:,.0f}")
    m4.metric("📊 空間利用率", f"{selected_data['利用率 (%)']}%")

    col_visual, col_text = st.columns([1.5, 1])
    
    with col_text:
        st.success(f"✅ 建議擺放：**{info['orientation_label']}**")
        
        # 計算剩餘空間
        remain_h = info['box_in_h'] - info['total_stack_h']
        
        st.info(f"""
        **規格檢核:**
        * 紙箱外徑: {raw_box['L']} x {raw_box['W']} x {raw_box['H']}
        * **有效內徑:** {raw_box['L']-box_thickness} x {raw_box['W']-box_thickness} x {raw_box['H']-box_thickness} (已扣{box_thickness}mm)
        
        **堆疊細節 (含隔板):**
        * 單層數量: {info['cols']} x {info['rows']} = {info['layer_count']} pcs
        * 堆疊層數: {info['layers']} 層
        * 隔板數量: {max(0, info['layers']-1)} 片 (每片{divider_thickness}mm)
        * **總堆疊高:** {info['total_stack_h']} mm
        * **頂部剩餘:** {remain_h} mm
        """)

    with col_visual:
        st.subheader("📐 裝箱俯視示意圖")
        # 注入變數到 HTML
        html_code = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ margin: 0; display: flex; justify-content: center; align-items: center; background: #fff; font-family: sans-serif; }}
                .container {{ position: relative; border: 2px dashed #cbd5e1; padding: 20px; border-radius: 12px; }}
                .legend {{ margin-top: 10px; text-align: center; color: #64748b; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div>
                <div class="container">
                    <canvas id="packingCanvas" width="400" height="350"></canvas>
                </div>
                <div class="legend">藍色：成品 | 灰色框：紙箱內徑</div>
            </div>
            <script>
                const boxL = {raw_box['L'] - box_thickness};
                const boxW = {raw_box['W'] - box_thickness};
                const prodL = {info['vis_L']};
                const prodW = {info['vis_W']};
                const cols = {info['cols']};
                const rows = {info['rows']};

                const canvas = document.getElementById('packingCanvas');
                const ctx = canvas.getContext('2d');
                
                // 自動縮放
                const scale = Math.min(380 / boxL, 330 / boxW);
                const drawBoxL = boxL * scale;
                const drawBoxW = boxW * scale;
                const startX = (canvas.width - drawBoxL) / 2;
                const startY = (canvas.height - drawBoxW) / 2;

                // 畫紙箱
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.strokeStyle = '#334155';
                ctx.lineWidth = 3;
                ctx.strokeRect(startX, startY, drawBoxL, drawBoxW);

                // 標示內徑尺寸
                ctx.fillStyle = '#64748b';
                ctx.font = '14px Arial';
                ctx.textAlign = 'center';
                ctx.fillText(boxL, canvas.width/2, startY - 8);
                ctx.textAlign = 'left';
                ctx.fillText(boxW, startX + drawBoxL + 8, canvas.height/2);

                // 畫產品
                ctx.fillStyle = '#60a5fa';
                ctx.strokeStyle = '#1e40af';
                ctx.lineWidth = 1;

                const drawProdL = prodL * scale;
                const drawProdW = prodW * scale;

                for (let r = 0; r < rows; r++) {{
                    for (let c = 0; c < cols; c++) {{
                        const x = startX + (c * drawProdL);
                        const y = startY + (r * drawProdW);
                        ctx.fillRect(x+1, y+1, drawProdL-2, drawProdW-2);
                        ctx.strokeRect(x+1, y+1, drawProdL-2, drawProdW-2);
                    }}
                }}
            </script>
        </body>
        </html>
        """
        components.html(html_code, height=450)
else:
    st.info("👆 請在上方列表中點選一個紙箱方案，以查看詳細圖解。")
