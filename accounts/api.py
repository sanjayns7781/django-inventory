# from fastapi import FastAPI, Request
import openai

app = FastAPI()
openai.api_key = "YOUR_API_KEY"

@app.post("/chat/")
async def chat(request: Request):
    data = await request.json()
    user_message = data.get("message")
    
    response = openai.ChatCompletion.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": user_message}]
    )
    
    return {"reply": response.choices[0].message['content']}
