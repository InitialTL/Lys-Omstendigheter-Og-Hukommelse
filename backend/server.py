from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import helper_functions
import database

app = FastAPI()

database.init_db()

questions_and_information = helper_functions.get_qap()
texts = helper_functions.get_texts()

keys = list(texts.keys())

@app.get("/text/{textID}")
def text(textID: int):
    if not (0 <= textID <= len(questions_and_information) - 1):
        raise HTTPException(status_code=404, detail="Text not found")
    
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
    
class AnswerSubmission(BaseModel):
    answers: list[int]
    
@app.post("/answers/{textID}")
def submit_answers(textID: int, submission: AnswerSubmission):
    if not (0 <= textID < len(keys)):
        raise HTTPException(status_code=404, detail="Text not found")
    
    questions = questions_and_information[keys[textID]]
    
    if (len(submission.answers) != len(questions)):
        raise HTTPException(status_code=400, detail="Invalid answer count")

    score = 0
    max_score = 0
    for question, answer in zip(questions, submission.answers):
        if not (0 <= answer < len(question["options"])):
            raise HTTPException(status_code=400, detail="Invalid answer")
        
        max_score += question["points"]
        if answer == question["answer"]:
            score += question["points"]
            
    database.save_result(
        text_id=textID,
        answers=submission.answers,
        score=score,
        max_score=max_score
    )
    
    return {
        "status": "OK",
        "score": score,
        "max_score": max_score,
    }


if (__name__ == '__main__'):
    uvicorn.run(app, host="127.0.0.1", port=8000)