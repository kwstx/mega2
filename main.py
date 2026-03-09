from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from parser import BillParser
from scheduler import SmartScheduler
from schemas import DeviceConfig, SchedulingConstraints, ScheduleUpdateRequest
from predictor import PricePredictor
import uvicorn
import pandas as pd

app = FastAPI(title="Utility Bill Parser Service")
parser = BillParser()
predictor = PricePredictor()

# In-memory state (Production would use a database)
current_device = DeviceConfig(id="EV-001", name="Home EV", energy_needed_kwh=40.0)
current_constraints = SchedulingConstraints(ready_by_time="07:00")
manual_override_active = False

@app.get("/", response_class=HTMLResponse)
async def main():
    content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Lumina | Smart Energy</title>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap" rel="stylesheet">
        <style>
            :root {
                --primary: #6366f1;
                --primary-hover: #4f46e5;
                --bg: #0f172a;
                --card: #1e293b;
                --text: #f8fafc;
                --text-muted: #94a3b8;
                --accent: #22d3ee;
            }
            body { 
                font-family: 'Outfit', sans-serif; 
                background: var(--bg); 
                color: var(--text); 
                display: flex; 
                justify-content: center; 
                align-items: center; 
                min-height: 100vh; 
                margin: 0;
                background-image: radial-gradient(circle at top right, #1e1b4b, transparent), 
                                  radial-gradient(circle at bottom left, #1e1b4b, transparent);
            }
            .container { 
                background: var(--card); 
                padding: 3rem; 
                border-radius: 24px; 
                box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5); 
                width: 100%;
                max-width: 500px; 
                border: 1px solid rgba(255,255,255,0.1);
                backdrop-filter: blur(10px);
                text-align: center;
            }
            h1 { 
                font-weight: 600; 
                font-size: 2.5rem;
                margin-bottom: 0.5rem;
                background: linear-gradient(to right, #fff, var(--accent));
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            p.subtitle { 
                color: var(--text-muted); 
                margin-bottom: 2rem;
                font-size: 1rem;
            }
            .nav-buttons {
                display: flex;
                gap: 1rem;
                justify-content: center;
                margin-bottom: 2rem;
            }
            .nav-link {
                color: var(--text-muted);
                text-decoration: none;
                font-weight: 600;
                padding: 0.5rem 1rem;
                border-radius: 8px;
                transition: all 0.3s;
            }
            .nav-link:hover, .nav-link.active {
                color: var(--accent);
                background: rgba(34, 211, 238, 0.1);
            }
            .upload-area { 
                border: 2px dashed rgba(255,255,255,0.1);
                padding: 2rem;
                border-radius: 16px;
                text-align: center;
                transition: all 0.3s ease;
                background: rgba(255,255,255,0.02);
                cursor: pointer;
            }
            .upload-area:hover {
                border-color: var(--primary);
                background: rgba(99, 102, 241, 0.05);
            }
            input[type="file"] { display: none; }
            .upload-icon {
                font-size: 3rem;
                margin-bottom: 1rem;
                display: block;
            }
            button { 
                background: var(--primary); 
                color: white; 
                border: none; 
                padding: 1rem 2rem; 
                border-radius: 12px; 
                cursor: pointer; 
                font-size: 1rem; 
                font-weight: 600;
                transition: all 0.3s; 
                width: 100%;
                margin-top: 1.5rem;
                box-shadow: 0 10px 15px -3px rgba(99, 102, 241, 0.3);
                display: flex;
                justify-content: center;
                align-items: center;
                gap: 0.5rem;
            }
            button:hover { 
                background: var(--primary-hover); 
                transform: translateY(-2px);
                box-shadow: 0 20px 25px -5px rgba(99, 102, 241, 0.4);
            }
            #result { 
                margin-top: 2rem; 
                padding: 1.5rem; 
                border-radius: 12px; 
                display: none; 
                background: rgba(0,0,0,0.3); 
                border: 1px solid rgba(255,255,255,0.1);
                font-family: 'Courier New', Courier, monospace;
                font-size: 0.85rem;
                color: #4ade80;
                max-height: 300px;
                overflow-y: auto;
                text-align: left;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="nav-buttons">
                <a href="/" class="nav-link active">Parser</a>
                <a href="/dashboard" class="nav-link">Predictor</a>
            </div>
            <h1>Lumina</h1>
            <p class="subtitle">Cloud-Based Energy Intelligence</p>
            
            <div class="upload-area" onclick="document.getElementById('billFile').click()">
                <span class="upload-icon">📄</span>
                <span class="upload-label">Upload a bill to get started</span>
                <input type="file" id="billFile" accept=".pdf,.csv" onchange="updateFileName()" />
                <div id="fileNameDisplay" style="margin-top:1rem;color:var(--accent)"></div>
            </div>
            
            <button onclick="uploadFile()"><span>Extract Data</span> ⚡</button>
            <div id="result"></div>
        </div>

        <script>
            function updateFileName() {
                const input = document.getElementById('billFile');
                const display = document.getElementById('fileNameDisplay');
                if (input.files.length > 0) {
                    display.innerText = "Selected: " + input.files[0].name;
                }
            }

            async function uploadFile() {
                const fileInput = document.getElementById('billFile');
                const resultDiv = document.getElementById('result');
                if (!fileInput.files[0]) {
                    alert("Please select a file first.");
                    return;
                }

                const formData = new FormData();
                formData.append("file", fileInput.files[0]);

                resultDiv.style.display = 'block';
                resultDiv.innerText = "// Initializing neural extraction...";

                try {
                    const response = await fetch("/upload", {
                        method: "POST",
                        body: formData
                    });
                    const data = await response.json();
                    resultDiv.innerText = JSON.stringify(data, null, 2);
                } catch (error) {
                    resultDiv.innerText = "!! Error: " + error.message;
                }
            }
        </script>
    </body>
    </html>
    """
    return content

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Lumina | Prediction Dashboard</title>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            :root {
                --primary: #6366f1;
                --bg: #0f172a;
                --card: #1e293b;
                --text: #f8fafc;
                --text-muted: #94a3b8;
                --accent: #22d3ee;
                --success: #4ade80;
                --warning: #fbbf24;
                --danger: #f87171;
            }
            body { 
                font-family: 'Outfit', sans-serif; 
                background: var(--bg); 
                color: var(--text); 
                margin: 0;
                padding: 2rem;
                background-image: radial-gradient(circle at top right, #1e1b4b, transparent);
            }
            .grid {
                display: grid;
                grid-template-columns: 2fr 1fr;
                gap: 2rem;
                max-width: 1200px;
                margin: 0 auto;
            }
            .card {
                background: var(--card);
                padding: 2rem;
                border-radius: 24px;
                border: 1px solid rgba(255,255,255,0.1);
                box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
            }
            .header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                max-width: 1200px;
                margin: 0 auto 2rem auto;
            }
            h1 { font-size: 2rem; margin: 0; }
            h2 { font-size: 1.25rem; margin-top: 0; color: var(--accent); }
            .stat-card {
                margin-bottom: 1rem;
                padding: 1rem;
                background: rgba(255,255,255,0.05);
                border-radius: 12px;
            }
            .stat-value {
                font-size: 1.5rem;
                font-weight: 600;
                color: var(--success);
            }
            .stat-label {
                font-size: 0.8rem;
                color: var(--text-muted);
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }
            .nav-link {
                color: var(--text-muted);
                text-decoration: none;
                font-weight: 600;
                padding: 0.5rem 1rem;
                border-radius: 8px;
                transition: all 0.3s;
            }
            .nav-link:hover, .nav-link.active {
                color: var(--accent);
                background: rgba(34, 211, 238, 0.1);
            }
            .badge {
                padding: 0.25rem 0.75rem;
                border-radius: 999px;
                font-size: 0.75rem;
                font-weight: 600;
            }
            .badge-cheap { background: rgba(74, 222, 128, 0.1); color: var(--success); border: 1px solid var(--success); }
            .badge-expensive { background: rgba(248, 113, 113, 0.1); color: var(--danger); border: 1px solid var(--danger); }
        </style>
    </head>
    <body>
        <div class="header">
            <div>
                <h1>Smart Dashboard</h1>
                <p style="color:var(--text-muted)">Predictive Insights & Asset Optimization</p>
            </div>
            <div>
                <a href="/" class="nav-link">Parser</a>
                <a href="/dashboard" class="nav-link active">Predictor</a>
            </div>
        </div>

        <div class="grid">
            <div class="card">
                <h2>48-Hour Price Forecast</h2>
                <canvas id="priceChart" height="150"></canvas>
            </div>
            
            <div class="card">
                <h2>Asset: EV Scheduler</h2>
                <div class="stat-card">
                    <div class="stat-label">Total Est. Cost</div>
                    <div class="stat-value" id="total-cost-val">$0.00</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Projected Savings</div>
                    <div class="stat-value" id="savings-val" style="color:var(--success)">$0.00</div>
                </div>
                
                <div style="margin-top:1.5rem">
                    <h3 style="font-size:0.9rem; color:var(--text-muted); margin-bottom:0.5rem">CONSTRAINTS</h3>
                    <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(255,255,255,0.05); padding:0.75rem; border-radius:12px; margin-bottom:1rem">
                        <span>Ready By:</span>
                        <input type="time" id="ready-time" value="07:00" style="background:transparent; border:1px solid var(--accent); color:white; padding:0.25rem; border-radius:4px" onchange="updateConstraints()">
                    </div>
                </div>

                <div style="margin-top:1.5rem">
                    <h3 style="font-size:0.9rem; color:var(--text-muted); margin-bottom:0.5rem">SYSTEM STATUS</h3>
                    <div id="status-badge" class="badge badge-cheap">Optimizing</div>
                    <p id="strategy-text" style="font-size:0.85rem; margin-top:0.5rem">Shifted charging to lowest price slots before 07:00.</p>
                </div>

                <button id="override-btn" onclick="toggleOverride()" style="margin-top:1rem; background:rgba(248, 113, 113, 0.1); border:1px solid var(--danger); color:var(--danger); box-shadow:none">
                    Manual Override
                </button>
            </div>
        </div>

        <script>
            let currentSchedule = null;
            let manualOverride = false;

            async function fetchData() {
                const response = await fetch('/api/schedule');
                const data = await response.json();
                currentSchedule = data;
                manualOverride = data.manual_override;
                
                // Update UI elements
                document.getElementById('total-cost-val').innerText = "$" + data.total_cost;
                document.getElementById('savings-val').innerText = "$" + data.savings;
                document.getElementById('status-badge').innerText = data.status;
                document.getElementById('status-badge').className = 'badge ' + 
                    (data.manual_override ? 'badge-expensive' : 'badge-cheap');
                document.getElementById('strategy-text').innerText = data.manual_override ? 
                    "System in override mode. Starting charge immediately regardless of price." :
                    `Optimizing for lowest prices. All requirements will be met by ${data.ready_by}.`;
                document.getElementById('ready-time').value = data.ready_by;
                
                const overrideBtn = document.getElementById('override-btn');
                if (data.manual_override) {
                    overrideBtn.innerText = "Cancel Override";
                    overrideBtn.style.background = "rgba(74, 222, 128, 0.1)";
                    overrideBtn.style.borderColor = "var(--success)";
                    overrideBtn.style.color = "var(--success)";
                } else {
                    overrideBtn.innerText = "Manual Override";
                    overrideBtn.style.background = "rgba(248, 113, 113, 0.1)";
                    overrideBtn.style.borderColor = "var(--danger)";
                    overrideBtn.style.color = "var(--danger)";
                }

                // Update Chart
                const ctx = document.getElementById('priceChart').getContext('2d');
                if (window.myChart) window.myChart.destroy();
                
                window.myChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: data.slots.map(s => {
                            const d = new Date(s.timestamp);
                            return d.getHours() + ":00";
                        }),
                        datasets: [{
                            label: 'Price (c/kWh)',
                            data: data.slots.map(s => s.price),
                            borderColor: '#6366f1',
                            backgroundColor: data.slots.map(s => s.is_active ? 'rgba(34, 211, 238, 0.4)' : 'rgba(99, 102, 241, 0.1)'),
                            pointBackgroundColor: data.slots.map(s => s.is_active ? 'var(--accent)' : 'transparent'),
                            pointRadius: data.slots.map(s => s.is_active ? 4 : 0),
                            fill: true,
                            tension: 0.4
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: { 
                            legend: { display: false },
                            tooltip: {
                                callbacks: {
                                    afterLabel: function(context) {
                                        const slot = data.slots[context.dataIndex];
                                        return slot.is_active ? "⚡ SCHEDULED" : "○ STANDBY";
                                    }
                                }
                            }
                        },
                        scales: {
                            y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
                            x: { grid: { display : false }, ticks: { color: '#94a3b8', maxRotation: 0 } }
                        }
                    }
                });
            }

            async function updateConstraints() {
                const readyTime = document.getElementById('ready-time').value;
                await fetch('/api/schedule/update', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        device_id: "EV-001",
                        constraints: { ready_by_time: readyTime }
                    })
                });
                fetchData();
            }

            async function toggleOverride() {
                manualOverride = !manualOverride;
                await fetch('/api/schedule/update', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        device_id: "EV-001",
                        manual_override: manualOverride
                    })
                });
                fetchData();
            }

            fetchData();
            // Refresh every 30 seconds
            setInterval(fetchData, 30000);
        </script>
    </body>
    </html>
    """
    return content

@app.get("/api/predict")
async def get_predictions():
    from predictor import PricePredictor
    from asset_manager import EVAssetManager
    
    predictor = PricePredictor()
    predictions = predictor.predict()
    
    if predictions is None:
        return {"error": "No data available"}
        
    manager = EVAssetManager()
    optimization = manager.optimize_charging(predictions)
    
    # Format predictions for JSON
    pred_list = predictions.to_dict(orient="records")
    
    return {
        "predictions": pred_list,
        "optimization": optimization
    }

@app.get("/api/schedule")
async def get_current_schedule():
    predictions = predictor.predict()
    if predictions is None:
        raise HTTPException(status_code=500, detail="Failed to get price predictions")
    
    scheduler = SmartScheduler(current_device, current_constraints)
    schedule = scheduler.get_schedule(predictions, manual_override=manual_override_active)
    
    return schedule

@app.post("/api/schedule/update")
async def update_schedule(request: ScheduleUpdateRequest):
    global current_constraints, manual_override_active
    
    if request.constraints:
        current_constraints = request.constraints
    
    if request.manual_override is not None:
        manual_override_active = request.manual_override
        
    return {"status": "success", "manual_override": manual_override_active, "ready_by": current_constraints.ready_by_time}



@app.post("/upload")
async def upload_bill(file: UploadFile = File(...)):
    content = await file.read()
    filename = file.filename.lower()
    
    if filename.endswith(".pdf"):
        result = parser.parse_pdf(content)
    elif filename.endswith(".csv"):
        result = parser.parse_csv(content)
    else:
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF and CSV are supported.")
    
    return result

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
