from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from parser import BillParser
import uvicorn

app = FastAPI(title="Utility Bill Parser Service")
parser = BillParser()

@app.get("/", response_class=HTMLResponse)
async def main():
    content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Lumina | Smart Bill Parser</title>
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
            }
            h1 { 
                font-weight: 600; 
                font-size: 2rem;
                margin-bottom: 0.5rem;
                background: linear-gradient(to right, #fff, var(--accent));
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                text-align: center;
            }
            p.subtitle { 
                color: var(--text-muted); 
                text-align: center; 
                margin-bottom: 2rem;
                font-size: 0.9rem;
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
            .upload-label {
                display: block;
                cursor: pointer;
            }
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
            }
            .file-name {
                margin-top: 1rem;
                font-size: 0.9rem;
                color: var(--accent);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Lumina</h1>
            <p class="subtitle">Intelligent Utility Bill Analysis & Normalization</p>
            
            <div class="upload-area" onclick="document.getElementById('billFile').click()">
                <span class="upload-icon">📄</span>
                <span class="upload-label">Click to upload PDF or CSV bill</span>
                <input type="file" id="billFile" accept=".pdf,.csv" onchange="updateFileName()" />
                <div id="fileNameDisplay" class="file-name"></div>
            </div>
            
            <button onclick="uploadFile()">Analyze Bill</button>
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
                resultDiv.innerText = "// Running neural extraction...";

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
