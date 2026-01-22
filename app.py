<style>
    /* 容器：限制影響範圍，只在 .sp-tool 內生效 */
    .sp-tool {
        font-family: 'Segoe UI', sans-serif;
        background-color: #fff; /* 工具箱背景若是深色，可改這裡 */
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        display: flex;
        flex-wrap: wrap;
        gap: 30px;
        max-width: 900px;
        margin: 0 auto; /* 居中 */
    }

    .sp-tool * {
        box-sizing: border-box;
    }

    /* 左側控制區 */
    .sp-controls {
        flex: 1;
        min-width: 280px;
    }

    /* 右側視覺區 */
    .sp-visualizer {
        flex: 1;
        min-width: 280px;
        display: flex;
        flex-direction: column;
        align-items: center;
        background: #f8fafc;
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #f1f5f9;
    }

    .sp-tool h3 {
        margin-top: 0;
        color: #1e293b;
        font-size: 1.1rem;
        border-bottom: 2px solid #2563eb;
        padding-bottom: 8px;
        display: inline-block;
        margin-bottom: 15px;
    }
    
    .sp-input-group { margin-bottom: 15px; }
    .sp-label { display: block; margin-bottom: 5px; font-weight: 600; color: #475569; font-size: 0.9rem;}
    
    .sp-input-row { display: flex; gap: 8px; }
    
    .sp-input {
        width: 100%;
        padding: 8px 10px;
        border: 1px solid #cbd5e1;
        border-radius: 4px;
        font-size: 1rem;
        transition: border 0.2s;
    }
    .sp-input:focus { border-color: #2563eb; outline: none; }

    /* 按鈕群組 */
    .sp-btn-group {
        display: flex;
        gap: 8px;
        margin: 15px 0;
    }

    .sp-btn {
        flex: 1;
        padding: 10px;
        border: 1px solid #2563eb;
        background: white;
        color: #2563eb;
        border-radius: 6px;
        cursor: pointer;
        font-weight: 600;
        font-size: 0.9rem;
        transition: all 0.2s;
    }

    .sp-btn:hover { background: #eff6ff; }
    .sp-btn.active {
        background: #2563eb;
        color: white;
        box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2);
    }

    /* 數據統計區 */
    .sp-stats {
        margin-top: 15px;
        padding: 15px;
        background: #eff6ff;
        border-radius: 6px;
        border: 1px solid #dbeafe;
    }
    .sp-stat-item {
        display: flex;
        justify-content: space-between;
        margin-bottom: 8px;
        font-size: 0.9rem;
        color: #334155;
    }
    .sp-stat-item.total {
        font-size: 1.1rem;
        font-weight: bold;
        color: #2563eb;
        border-top: 1px solid #bfdbfe;
        padding-top: 10px;
        margin-top: 10px;
    }

    /* Canvas 容器 */
    .sp-canvas-wrapper {
        position: relative;
        margin-top: 10px;
        border: 2px dashed #cbd5e1;
        padding: 10px;
        border-radius: 8px;
        background: #fff;
        display: flex;
        justify-content: center;
        box-shadow: inset 0 0 10px rgba(0,0,0,0.02);
    }

    .sp-legend {
        font-size: 0.8rem;
        color: #64748b;
        margin-top: 10px;
        text-align: center;
    }
</style>

<div class="sp-tool" id="shengwei-packing-calculator">
    
    <div class="sp-controls">
        <h3>📦 智能裝箱參數設定</h3>
        
        <div class="sp-input-group">
            <label class="sp-label">紙箱內徑 (mm)</label>
            <div class="sp-input-row">
                <input type="number" class="sp-input sp-calc-trigger" id="sw-boxL" placeholder="長" value="500">
                <input type="number" class="sp-input sp-calc-trigger" id="sw-boxW" placeholder="寬" value="400">
                <input type="number" class="sp-input sp-calc-trigger" id="sw-boxH" placeholder="高" value="300">
            </div>
        </div>

        <div class="sp-input-group">
            <label class="sp-label">成品尺寸 (mm)</label>
            <div class="sp-input-row">
                <input type="number" class="sp-input sp-calc-trigger" id="sw-prodL" placeholder="長" value="120">
                <input type="number" class="sp-input sp-calc-trigger" id="sw-prodW" placeholder="寬" value="80">
                <input type="number" class="sp-input sp-calc-trigger" id="sw-prodH" placeholder="高" value="50">
            </div>
        </div>

        <label class="sp-label">選擇擺放基準面 (自動旋轉)</label>
        <div class="sp-btn-group">
            <button class="sp-btn active" onclick="SW_PackTool.setOrientation('flat', this)">
                平放<br><span style="font-size:0.8em; opacity:0.8">(L x W)</span>
            </button>
            <button class="sp-btn" onclick="SW_PackTool.setOrientation('side', this)">
                側放<br><span style="font-size:0.8em; opacity:0.8">(L x H)</span>
            </button>
            <button class="sp-btn" onclick="SW_PackTool.setOrientation('upright', this)">
                直立<br><span style="font-size:0.8em; opacity:0.8">(W x H)</span>
            </button>
        </div>

        <div class="sp-stats">
            <div class="sp-stat-item"><span>單層排列 (排 x 列):</span> <span id="sw-layer-layout">-</span></div>
            <div class="sp-stat-item"><span>每層數量:</span> <span id="sw-per-layer">-</span></div>
            <div class="sp-stat-item"><span>可堆疊層數:</span> <span id="sw-layers">-</span></div>
            <div class="sp-stat-item"><span>空間利用率:</span> <span id="sw-utilization">-</span></div>
            <div class="sp-stat-item total"><span>每箱總數量:</span> <span id="sw-total-count">-</span></div>
        </div>
    </div>

    <div class="sp-visualizer">
        <h3>📐 裝箱俯視圖 (第一層)</h3>
        <div class="sp-canvas-wrapper">
            <canvas id="sw-packingCanvas" width="280" height="280"></canvas>
        </div>
        <div class="sp-legend">
            灰色框線：紙箱內徑 / 藍色區塊：成品<br>
            視角：Top View (由上往下看)
        </div>
    </div>
</div>

<script>
    // 使用 Namespace 封裝，避免汙染全域變數
    const SW_PackTool = {
        orientation: 'flat', // 預設擺放方向

        init: function() {
            // 綁定所有輸入框的監聽事件
            const inputs = document.querySelectorAll('.sp-calc-trigger');
            inputs.forEach(input => {
                input.addEventListener('input', () => this.calculate());
            });
            
            // 初始執行一次
            setTimeout(() => this.calculate(), 300);
        },

        setOrientation: function(type, btnElement) {
            this.orientation = type;
            
            // 更新按鈕樣式
            document.querySelectorAll('.sp-btn').forEach(b => b.classList.remove('active'));
            btnElement.classList.add('active');
            
            this.calculate();
        },

        calculate: function() {
            // 1. 獲取數值 (使用 ID 選擇器)
            const boxL = parseFloat(document.getElementById('sw-boxL').value) || 0;
            const boxW = parseFloat(document.getElementById('sw-boxW').value) || 0;
            const boxH = parseFloat(document.getElementById('sw-boxH').value) || 0;
            
            const rawProdL = parseFloat(document.getElementById('sw-prodL').value) || 0;
            const rawProdW = parseFloat(document.getElementById('sw-prodW').value) || 0;
            const rawProdH = parseFloat(document.getElementById('sw-prodH').value) || 0;

            if (boxL === 0 || rawProdL === 0) return;

            // 2. 轉換擺放邏輯
            let pL, pW, pH;
            switch (this.orientation) {
                case 'flat':    pL = rawProdL; pW = rawProdW; pH = rawProdH; break;
                case 'side':    pL = rawProdL; pW = rawProdH; pH = rawProdW; break;
                case 'upright': pL = rawProdW; pW = rawProdH; pH = rawProdL; break;
            }

            // 3. 計算排列 (比較兩種旋轉方案)
            // 方案 A: 不旋轉
            const colsA = Math.floor(boxL / pL);
            const rowsA = Math.floor(boxW / pW);
            const countA = colsA * rowsA;

            // 方案 B: 旋轉 90 度
            const colsB = Math.floor(boxL / pW);
            const rowsB = Math.floor(boxW / pL);
            const countB = colsB * rowsB;

            let bestL, bestW, countLayer, cols, rows;
            
            // 選數量多的，若數量一樣優先選不旋轉的
            if (countB > countA) {
                bestL = pW; bestW = pL;
                cols = colsB; rows = rowsB;
                countLayer = countB;
            } else {
                bestL = pL; bestW = pW;
                cols = colsA; rows = rowsA;
                countLayer = countA;
            }

            // 4. 計算層數與總數
            const layers = Math.floor(boxH / pH);
            const totalCount = countLayer * layers;

            // 5. 計算空間利用率
            const productVol = rawProdL * rawProdW * rawProdH * totalCount;
            const boxVol = boxL * boxW * boxH;
            const utilization = ((productVol / boxVol) * 100).toFixed(1);

            // 6. 更新 UI 數據
            document.getElementById('sw-layer-layout').textContent = `${cols} x ${rows}`;
            document.getElementById('sw-per-layer').textContent = countLayer;
            document.getElementById('sw-layers').textContent = layers;
            document.getElementById('sw-utilization').textContent = `${utilization}%`;
            document.getElementById('sw-total-count').textContent = totalCount;

            // 7. 繪圖
            this.draw(boxL, boxW, bestL, bestW, cols, rows);
        },

        draw: function(boxL, boxW, pL, pW, cols, rows) {
            const canvas = document.getElementById('sw-packingCanvas');
            const ctx = canvas.getContext('2d');
            
            // 自動縮放
            const maxCanvasSize = 280;
            const scale = Math.min((maxCanvasSize - 20) / boxL, (maxCanvasSize - 20) / boxW);
            
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            const drawBoxL = boxL * scale;
            const drawBoxW = boxW * scale;
            const startX = (canvas.width - drawBoxL) / 2;
            const startY = (canvas.height - drawBoxW) / 2;

            // 畫紙箱
            ctx.strokeStyle = '#334155';
            ctx.lineWidth = 2;
            ctx.strokeRect(startX, startY, drawBoxL, drawBoxW);
            
            // 標示尺寸
            ctx.fillStyle = '#64748b';
            ctx.font = '12px Arial';
            ctx.textAlign = 'center';
            ctx.fillText(boxL, canvas.width/2, startY - 6); 
            ctx.textAlign = 'left';
            ctx.fillText(boxW, startX + drawBoxL + 6, canvas.height/2); 

            // 畫產品
            ctx.fillStyle = '#60a5fa'; // 晟崴標準藍色調?
            ctx.strokeStyle = '#1e40af'; 
            ctx.lineWidth = 1;

            const drawProdL = pL * scale;
            const drawProdW = pW * scale;

            for (let r = 0; r < rows; r++) {
                for (let c = 0; c < cols; c++) {
                    const x = startX + (c * drawProdL);
                    const y = startY + (r * drawProdW);
                    // 間隙 padding
                    const pad = 1; 
                    ctx.fillRect(x + pad, y + pad, drawProdL - 2*pad, drawProdW - 2*pad);
                    ctx.strokeRect(x + pad, y + pad, drawProdL - 2*pad, drawProdW - 2*pad);
                }
            }
        }
    };

    // 啟動工具
    SW_PackTool.init();
</script>
