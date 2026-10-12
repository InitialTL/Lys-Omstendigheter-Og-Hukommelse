from fastapi import FastAPI
import uvicorn
import helper_functions

app = FastAPI()

questions_and_information = helper_functions.get_qap()
texts = helper_functions.get_texts()

keys = list(texts.keys())

@app.get("/text/{textID}")
def text(textID: int):
    if not (0 <= textID <= len(questions_and_information) - 1):
        return None    
    
    information_for_id = questions_and_information[list(keys)[textID]]
    text = texts[keys[textID]]
    
    return {"status": "OK",
            "text": text}
    
@app.get("/questions/{textID}")
def questions(textID: int):
    if not (0 <= textID <= len(questions_and_information) - 1):
        return None   

    questions = [
        {
            "question": q["question"],
            "options": q["options"],
            "points": q["points"]
        }
        for q in questions_and_information[keys[textID]]
    ]
    
    return {"status": "OK",
            "questions": questions}

if (__name__ == '__main__'):
    uvicorn.run(app, host="127.0.0.1", port=8000)