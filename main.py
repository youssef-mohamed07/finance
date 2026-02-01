import os
import io
import json
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from pydub import AudioSegment

# ---------- Load ENV ----------
load_dotenv()

GROQ_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_KEY:
    raise Exception("GROQ_API_KEY missing")

groq_client = Groq(api_key=GROQ_KEY)

# ---------- Setup FFmpeg & FFprobe (Railway compatible) ----------
AudioSegment.converter = "/usr/bin/ffmpeg"
AudioSegment.ffprobe = "/usr/bin/ffprobe"

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

# ---------- AI Prompt (Dynamic Category Creation) ----------
FINANCE_PROMPT = """
You are a financial analysis AI.

Analyze the following sentence and return ONLY a JSON object.

If the expense category does NOT match any common category,
generate a NEW meaningful category name.

Return JSON in this exact format:

{
  "amount": number | null,
  "category": "string",
  "item": "string | null",
  "place": "string | null",
  "type": "expense | income"
}

Sentence:
"{text}"
"""

# ---------- Text Analyze ----------
@app.post("/analyze")
def analyze_text(input: TextInput):
    try:
        prompt = FINANCE_PROMPT.format(text=input.text)

        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        output = response.choices[0].message.content
        start = output.find("{")
        end = output.rfind("}")
        parsed = json.loads(output[start:end+1])

        return {"analysis": parsed}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------- Voice Analyze ----------
@app.post("/voice")
async def analyze_voice(file: UploadFile = File(...)):
    try:
        audio_bytes = await file.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Empty audio")

        # Convert audio → WAV mono 16kHz
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
        audio = audio.set_channels(1).set_frame_rate(16000)

        buffer = io.BytesIO()
        audio.export(buffer, format="wav")
        buffer.seek(0)
        buffer.name = "voice.wav"

        # Transcription using Groq Whisper
        transcript = groq_client.audio.transcriptions.create(
            model="whisper-large-v3-turbo",
            file=buffer,
            language="ar"
        )

        text = transcript.text

        # Finance Analysis
        prompt = FINANCE_PROMPT.format(text=text)

        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        output = response.choices[0].message.content
        start = output.find("{")
        end = output.rfind("}")
        parsed = json.loads(output[start:end+1])

        return {
            "text": text,
            "analysis": parsed
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------- Run Server ----------
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
