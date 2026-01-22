import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import math

# 設定頁面配置
st.set_page_config(page_title="晟崴塑膠-智能裝箱選型系統", layout="wide")

# ==========================================
# 0. 定義公司標準紙箱資料庫 (含價格資訊)
# ==========================================
# 資料來源：晟崴塑膠紙箱規格一覽表.pdf
# price: 紙箱單價, div_price: 隔板單價
STANDARD_BOXES_RAW = [
    {"name": "方北特專用箱", "L": 564, "W": 424, "H": 362, "price": 39.0, "div_price": 46.0},
    {"name": "NO.2-2 紙箱", "L": 570, "W": 338, "H": 320, "price": 24.5, "div_price": 2.3},
    {"name": "NO.3 紙箱",   "L": 570, "W": 340, "H": 248, "price": 21.8, "div_price": 0.0}, # 報價單未見專用隔板，設為0或需確認
    {"name": "NO.4 紙箱",   "L": 324, "W": 228, "H": 226, "price": 13.8, "div_price": 1.4},
    {"name": "NO.8 紙箱",   "L": 450, "W": 306, "H": 424, "price": 24.5, "div_price": 2.0},
    {"name": "NO.9 紙箱",   "L": 650, "W": 470, "H": 460, "price": 35.0, "div_price": 3.3},
    {"name": "NO.10 紙箱",  "L": 648, "W": 468, "H": 360, "price": 32.5, "div_price": 4.0},
    {"name": "NO.14 紙箱",  "L": 392, "W": 314, "H": 412, "price": 19.5, "div_price": 1.8},
    {"name": "NO.15-1 紙箱","L": 502, "W": 492, "H": 408, "price": 31.5, "div_price": 2.6}, # 參考NO.15隔板價格
    {"name": "NO.16 紙箱",  "L": 534, "W": 400, "H": 340, "price": 31.0, "div_price": 3.4},
    {"name": "NO.17 紙箱",  "L": 536, "W": 400, "H": 560, "price": 36.5, "div_price": 3.4},
]

# ==========================================
# 1. 核心計算函數 (純計算邏輯)
# ==========================================
def calculate_single_orientation(box_in_l, box_in_w, box_in_h, pL, pW, pH, divider_thickness, strategy_name):
    """
    計算特定擺放方向的裝箱數
    """
    if pL > box_in_l or pW > box_in_w or pH > box_in_h:
        return None

    # 方案 A: 不旋轉
    colsA = math.floor(box_in_l / pL)
    rowsA = math.floor(box_in_w / pW)
    countA = colsA * rowsA

    # 方案 B: 旋轉 90 度
    colsB = math.floor(box_in_l / pW)
    rowsB = math.floor(box_in_w / pL)
    countB = colsB * rowsB

    # 取單層最佳解
    if countB > countA:
        layer_count = countB
        cols, rows = colsB, rowsB
        vis_L, vis_W = pW, pL
        rotated = True
    else:
        layer_count = countA
        cols, rows = colsA, rowsA
        vis_L, vis_W = pL, pW
        rotated = False
    
    # 計算垂直層數 (考慮隔板)
    if divider_thickness > 0:
        layers = math.floor( (box_in_h + divider_thickness) / (pH + divider_thickness) )
    else:
        layers = math.floor(box_in_h / pH)
        
    layers = max(1, layers)
    total_stack_h = (layers * pH) + ((layers - 1) * divider_thickness)
    
    if total_stack_h > box_in_h:
        layers -= 1
    
    if layers < 1: return None

    total_count = layer_count * layers
    
    return {
        "count": total_count,
        "layers": layers,
        "layer_count": layer_count,
        "cols": cols,
        "rows": rows,
        "vis_L": vis_L,
        "vis_W": vis_W,
        "pH": pH,
        "total_stack_h": total_stack_h,
        "strategy": strategy_name
    }

def find_best_box_option(box_data, prod_l, prod_w, prod_h, box_thick, div_thick):
    """
    為列表頁找出某個紙箱的「最佳」建議
    """
    # 計算內徑
    in_L, in_W, in_H = box_data['L']-box_thick, box_data['W']-box_thick, box_data['H']-box_thick
    if in_L<=0 or in_W<=0 or in_H<=0: return None

    strategies = [
        ('平放 (LxW)', prod_l, prod_w, prod_h, 'flat'),
        ('側放 (LxH)', prod_l, prod_h, prod_w, 'side'),
        ('直立 (WxH)', prod_w, prod_h, prod_l, 'upright')
    ]

    best_res = None
    max_count = -1

    for label, pL, pW, pH, code in strategies:
        res = calculate_single_orientation(in_L, in_W, in_H, pL, pW, pH, div_thick, label)
        if res and res['count'] > max_count:
            max_count = res['count']
            best_res = res
            best_res['code'] = code # 記錄代碼以便預設選中

    return best_res

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

    st.header("2. 包材設定")
    box_thickness = st.number_input("5層箱扣除 (mm)", value=10)
    divider_thickness = st.number_input("隔板厚度 (mm)", value=3)

    st.header("3. 產品重/價")
    unit_weight = st.number_input("產品單重 (g)", value=85.5, step=0.1)
    # unit_cost 暫時移除，因使用者更關注包裝成本
    
    st.info("💡 已載入紙箱與隔板的採購單價，將自動計算分攤成本。")

# ==========================================
# 3. 主畫面邏輯
# ==========================================
st.title("📦 晟崴塑膠 - 智能裝箱選型系統")

# --- 步驟 A: 預計算列表數據 ---
table_data = []
valid_boxes = {} # 儲存有效紙箱資料供後續使用

for box in STANDARD_BOXES_RAW:
    best = find_best_box_option(box, prod_l, prod_w, prod_h, box_thickness, divider_thickness)
    
    if best:
        # 計算包裝成本
        # 公式：(紙箱價 + (層數-1)*隔板價) / 總數量
        div_count = max(0, best['layers'] - 1)
        total_pkg_cost = box['price'] + (div_count * box['div_price'])
        cost_per_pcs = total_pkg_cost / best['count'] if best['count'] > 0 else 0
        
        display_name = f"{box['name']} ({box['L']}x{box['W']}x{box['H']})"
        
        table_data.append({
            "紙箱規格": display_name,
            "建議每箱數量": best['count'],
            "單pcs包材費": cost_per_pcs, # 排序用數值
            "單pcs包材費(顯示)": f"${cost_per_pcs:.2f}",
            "建議擺放": best['strategy'],
            "總重量 (kg)": round((best['count'] * unit_weight) / 1000, 2),
            "raw_box": box,
            "best_code": best['code'] # 用於預設選項
        })
        valid_boxes[display_name] = box

if not table_data:
    st.error("❌ 無法裝入任何現有紙箱，請檢查尺寸設定。")
    st.stop()

df = pd.DataFrame(table_data)
# 預設排序：單pcs包材費由低到高 (最省錢優先)，或者數量由多到少
# 這裡採用：數量由多到少
df = df.sort_values(by="建議每箱數量", ascending=False).reset_index(drop=True)

# --- 步驟 B: 顯示列表 ---
st.subheader("📋 裝箱試算列表")
st.caption("點選紙箱以進入「詳細設定模式」，可自由調整擺放方式。")

event = st.dataframe(
    df,
    use_container_width=True,
    hide_index=True,
    column_order=["紙箱規格", "建議每箱數量", "單pcs包材費(顯示)", "總重量 (kg)", "建議擺放"],
    selection_mode="single-row",
    on_select="rerun"
)

# --- 步驟 C: 詳細互動模式 ---
if len(event.selection.rows) > 0:
    idx = event.selection.rows[0]
    selected_row = df.iloc[idx]
    box_data = selected_row["raw_box"]
    default_orient = selected_row["best_code"]
    
    st.markdown("---")
    st.header(f"🔍 詳細設定：{box_data['name']}")
    
    # 建立 3 欄佈局：控制、數據、圖面
    col_ctrl, col_data, col_vis = st.columns([1, 1.2, 1.5])
    
    with col_ctrl:
        st.subheader("1. 選擇擺放方式")
        # 使用 radio 讓使用者切換，並預設選中系統建議的
        orient_map = {'flat': 0, 'side': 1, 'upright': 2}
        orient_options = ['平放 (LxW)', '側放 (LxH)', '直立 (WxH)']
        
        selected_label = st.radio(
            "請選擇裝箱方向：",
            orient_options,
            index=orient_map.get(default_orient, 0)
        )
        
        # 根據選擇重新計算
        in_L, in_W, in_H = box_data['L']-box_thickness, box_data['W']-box_thickness, box_data['H']-box_thickness
        
        if '平放' in selected_label:
            calc_res = calculate_single_orientation(in_L, in_W, in_H, prod_l, prod_w, prod_h, divider_thickness, '平放')
        elif '側放' in selected_label:
            calc_res = calculate_single_orientation(in_L, in_W, in_H, prod_l, prod_h, prod_w, divider_thickness, '側放')
        else:
            calc_res = calculate_single_orientation(in_L, in_W, in_H, prod_w, prod_h, prod_l, divider_thickness, '直立')

    # 檢查是否裝得下
    if calc_res is None:
        with col_data:
            st.error("⚠️ 此擺放方式無法裝入箱內 (尺寸過大)。")
    else:
        # 計算詳細成本
        div_count = max(0, calc_res['layers'] - 1)
        total_div_cost = div_count * box_data['div_price']
        total_pkg_cost = box_data['price'] + total_div_cost
        cost_per_pcs = total_pkg_cost / calc_res['count']
        total_weight = (calc_res['count'] * unit_weight) / 1000
        
        with col_data:
            st.subheader("2. 成本與數據")
            st.metric("📦 每箱數量", f"{calc_res['count']} pcs", delta=f"{calc_res['layers']} 層")
            
            # 這是用戶最想要的「單pcs包裝成本」
            st.metric("💰 單pcs包裝成本", f"${cost_per_pcs:.3f}", 
                     delta=f"總包材費: ${total_pkg_cost:.1f}", delta_color="inverse")
            
            st.metric("⚖️ 整箱總重", f"{total_weight:.2f} kg",
                     delta="⚠️ 超重" if total_weight > 18 else "OK",
                     delta_color="inverse" if total_weight > 18 else "normal")
            
            st.caption(f"""
            **計價公式:**
            ( 紙箱${box_data['price']} + 隔板${box_data['div_price']} x {div_count}片 ) ÷ {calc_res['count']}
            """)

        with col_vis:
            st.subheader("3. 裝箱示意圖")
            
            # Canvas 繪圖代碼
            html_code = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ margin: 0; display: flex; justify-content: center; align-items: center; background: #fff; font-family: sans-serif; }}
                    .container {{ position: relative; border: 2px dashed #cbd5e1; padding: 20px; border-radius: 12px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <canvas id="canvas" width="350" height="300"></canvas>
                </div>
                <script>
                    const boxL = {in_L};
                    const boxW = {in_W};
                    const prodL = {calc_res['vis_L']};
                    const prodW = {calc_res['vis_W']};
                    const cols = {calc_res['cols']};
                    const rows = {calc_res['rows']};

                    const canvas = document.getElementById('canvas');
                    const ctx = canvas.getContext('2d');
                    
                    const scale = Math.min(330 / boxL, 280 / boxW);
                    const drawBoxL = boxL * scale;
                    const drawBoxW = boxW * scale;
                    const startX = (canvas.width - drawBoxL) / 2;
                    const startY = (canvas.height - drawBoxW) / 2;

                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                    
                    // 紙箱
                    ctx.strokeStyle = '#334155';
                    ctx.lineWidth = 3;
                    ctx.strokeRect(startX, startY, drawBoxL, drawBoxW);
                    
                    // 尺寸文字
                    ctx.fillStyle = '#64748b';
                    ctx.font = '12px Arial';
                    ctx.fillText('內長 '+boxL, startX, startY - 5);
                    ctx.fillText('內寬 '+boxW, startX - 50, startY + 20);

                    // 產品
                    ctx.fillStyle = '#60a5fa';
                    ctx.strokeStyle = '#1e40af';
                    ctx.lineWidth = 1;
                    
                    const pDrawL = prodL * scale;
                    const pDrawW = prodW * scale;

                    for (let r = 0; r < rows; r++) {{
                        for (let c = 0; c < cols; c++) {{
                            const x = startX + c * pDrawL;
                            const y = startY + r * pDrawW;
                            ctx.fillRect(x+1, y+1, pDrawL-2, pDrawW-2);
                            ctx.strokeRect(x+1, y+1, pDrawL-2, pDrawW-2);
                        }}
                    }}
                </script>
            </body>
            </html>
            """
            components.html(html_code, height=350)
else:
    st.info("👆 請先從上方列表中點選一個紙箱。")
