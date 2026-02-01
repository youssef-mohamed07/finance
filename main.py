import os
import io
import json
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pydub import AudioSegment
from pydub.utils import mediainfo
import openai
import dateparser

# ---------- Load ENV ----------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise Exception("OPENAI_API_KEY missing")
openai.api_key = OPENAI_API_KEY

# ---------- Setup FFmpeg for Windows ----------
AudioSegment.converter = r"C:\ffmpeg\bin\ffmpeg.exe"
AudioSegment.ffprobe = r"C:\ffmpeg\bin\ffprobe.exe"

# ---------- App ----------
app = FastAPI(title="Voice & Text Finance Analyzer")

# ---------- CORS ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")

# ---------- Home ----------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ---------- Text Input ----------
class TextInput(BaseModel):
    text: str

# ---------- Finance Analysis Prompt ----------
PROMPT_TEMPLATE = """
Extract financial transaction details from the following user text.
Return a strict JSON object only, with keys:
- amount
- category (Food, Shopping, Bills, Transport, Health, Education, Entertainment, Other)
- date (YYYY-MM-DD)
- description

Now analyse this text:
"{text}"
"""

def analyze_text_with_openai(text: str) -> dict:
    prompt = PROMPT_TEMPLATE.format(text=text.replace('"', '\\"'))
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    content = resp.choices[0].message["content"].strip()
    try:
        data = json.loads(content)
    except:
        # fallback لو JSON مش مضبوط
        start = content.find('{')
        end = content.rfind('}')
        data = json.loads(content[start:end+1])

    # Normalize amount
    try:
        data["amount"] = float(data.get("amount"))
    except:
        data["amount"] = None

    # Normalize date
    parsed = dateparser.parse(data.get("date"))
    if parsed:
        data["date"] = parsed.strftime("%Y-%m-%d")
    else:
        data["date"] = dateparser.parse("today").strftime("%Y-%m-%d")

    # Defaults
    if not data.get("category"):
        data["category"] = "Other"
    if not data.get("description"):
        data["description"] = text[:80]

    return data

# ---------- Text Analyze Endpoint ----------
@app.post("/analyze")
def analyze_text(input: TextInput):
    try:
        result = analyze_text_with_openai(input.text)
        return {"analysis": result}
    except Exception as e:
        print("Text analyze error:", e)
        raise HTTPException(status_code=500, detail=str(e))

# ---------- Voice Analyze Endpoint ----------
@app.post("/voice")
async def analyze_voice(file: UploadFile = File(...)):
    try:
        audio_bytes = await file.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Empty audio file")

        # Detect format automatically
        try:
            info = mediainfo(io.BytesIO(audio_bytes))
            format = info.get('format_name')
            if not format:
                format = os.path.splitext(file.filename)[1].lower()[1:]
        except Exception:
            format = os.path.splitext(file.filename)[1].lower()[1:]

        # Convert audio → WAV mono 16kHz
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format=format)
        audio = audio.set_channels(1).set_frame_rate(16000)

        buffer = io.BytesIO()
        audio.export(buffer, format="wav")
        buffer.seek(0)
        buffer.name = "voice.wav"

        # Transcription using OpenAI Whisper
        transcript_resp = openai.Audio.transcriptions.create(
            model="whisper-1",
            file=buffer
        )
        text = transcript_resp["text"]

        # Analyze text
        analysis = analyze_text_with_openai(text)

        return {
            "text": text,
            "analysis": analysis
        }

    except Exception as e:
        print("Voice analyze error:", e)
        raise HTTPException(status_code=500, detail=str(e))

# ---------- Run Server ----------
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
