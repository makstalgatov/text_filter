from fastapi import FastAPI, Form, UploadFile, File, HTTPException
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
        input[type="file"] {
            margin: 10px 0;
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
        }
        .result h3 {
            margin: 0 0 10px;
            color: #555;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Text Filter Application</h1>
        <form action="/process" method="post" enctype="multipart/form-data">
            <label for="text">Enter text or upload a file:</label>
            <textarea name="text" id="text" placeholder="Enter your text here..."></textarea>
            <input type="file" name="file" id="file"><br>
            <button type="submit">Process</button>
        </form>
        {result_section}
    </div>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTML_TEMPLATE.replace("{result_section}", "")

@app.post("/process", response_class=HTMLResponse)
async def process_text(
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    if not text and not file:
        raise HTTPException(status_code=400, detail="Please provide text or upload a file.")

    # Combine text input and file content if provided
    if file:
        file_content = (await file.read()).decode("utf-8")
        text = (text or "") + "\n" + file_content

    if not text:
        raise HTTPException(status_code=400, detail="No text found.")

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
        result_html = f"<div class='result'><h3>Result:</h3><p>{'<br>'.join(results)}</p></div>"
    else:
        result_html = "<div class='result'><h3>Result:</h3><p>No matches found.</p></div>"

    return HTML_TEMPLATE.replace("{result_section}", result_html)
