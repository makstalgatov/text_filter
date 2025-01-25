from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse
from typing import List, Optional

app = FastAPI()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Text Filter App</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f9;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        .container {
            background: white;
            padding: 20px 30px;
            border-radius: 10px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
            width: 90%;
            max-width: 600px;
            text-align: center;
        }
        h1 {
            color: #333;
        }
        textarea {
            width: 100%;
            height: 150px;
            margin: 10px 0;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
        }
        button {
            padding: 10px 20px;
            background-color: #007BFF;
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
        }
        button:hover {
            background-color: #0056b3;
        }
        .result {
            margin-top: 20px;
            padding: 15px;
            background: #f9f9f9;
            border: 1px solid #ddd;
            border-radius: 5px;
            text-align: left;
            position: relative;
        }
        .result h3 {
            margin: 0 0 10px;
            color: #555;
        }
        .copy-btn {
            position: absolute;
            top: 10px;
            right: 10px;
            padding: 5px 10px;
            background-color: #28a745;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
        }
        .copy-btn:hover {
            background-color: #218838;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Text Filter Application</h1>
        <form action="/process" method="post">
            <label for="text">Enter text:</label>
            <textarea name="text" id="text" placeholder="Enter your text here..."></textarea>
            <button type="submit">Process</button>
        </form>
        {result_section}
    </div>
    <script>
        function copyToClipboard(elementId) {
            const text = document.getElementById(elementId).innerText;
            navigator.clipboard.writeText(text).catch(err => {
                console.error('Failed to copy: ', err);
            });
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTML_TEMPLATE.replace("{result_section}", "")

@app.post("/process", response_class=HTMLResponse)
async def process_text(
    text: Optional[str] = Form(None)
):
    if not text:
        raise HTTPException(status_code=400, detail="Please provide text.")

    # Process the text to find "42123" and its numeric following line
    lines = text.splitlines()
    results = []
    for i, line in enumerate(lines):
        if line.strip().startswith("42123") and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if next_line.isdigit() or (next_line.startswith("+") and next_line[1:].isdigit()):
                results.append(next_line)

    result_html = ""
    if results:
        result_text = "<br>".join(results)
        result_html = (
            f"<div class='result'>"
            f"<h3>Result:</h3>"
            f"<p id='result-text'>{result_text}</p>"
            f"<button class='copy-btn' onclick=\"copyToClipboard('result-text')\">Copy</button>"
            f"</div>"
        )
    else:
        result_html = "<div class='result'><h3>Result:</h3><p>No matches found.</p></div>"

    return HTML_TEMPLATE.replace("{result_section}", result_html)
