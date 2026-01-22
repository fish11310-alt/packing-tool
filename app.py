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
    unit_weight = st.number_input("單重 (g)", value=85.5,
