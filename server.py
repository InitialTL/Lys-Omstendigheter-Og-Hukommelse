from fastapi import FastAPI
import uvicorn
import helper_functions

app = FastAPI()

questions_and_information = helper_functions.get_qap()
texts = helper_functions.get_texts()

keys = list(texts.keys())

@app.get("/test/{textID}")
def test(textID: int):
    if not (0 <= textID <= len(questions_and_information) - 1):
        return None    
    
    information_for_id = questions_and_information[list(keys)[textID]]
    text = texts[keys[textID]]
    
    return {"status": "OK",
            "text": text}

if (__name__ == '__main__'):
    uvicorn.run(app, host="127.0.0.1", port=8000)