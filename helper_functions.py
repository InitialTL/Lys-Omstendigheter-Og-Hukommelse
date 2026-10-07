from pathlib import Path
import json

TEXT_DIRECTORY = Path("tekster")
TEXT_FILES = list(TEXT_DIRECTORY.glob("*.txt"))

Q_AND_A_DIRECTORY = Path("spørsmål_og_svar")
Q_AND_A_FILES = list(Q_AND_A_DIRECTORY.glob("*.json"))

def get_texts() -> dict[str, str]:
    """
    Returns:
        Tekstene som ligger i mappen ./tekster/
        
        dict[str, str]: Et dictionary med navn på teksten og selve teksten.
    """
    texts = {}
    
    for text in TEXT_FILES:
        if text.stat().st_size == 0:
            continue
        
        with text.open("r", encoding="utf-8") as t:
            texts[text.stem] = t.readlines()
    
    return texts

def get_qap() -> dict[str, tuple[dict]]:
    """
    Returns:
        Alle spørsmålene, svarene og poengene for hver av spørsmålene som ligger i ./spørsmål_og_svar/
    
        dict[str, tuple[dict]]: Hensikten til et dictionary her, er at vi har flere tekster, og sorterer spørsmålene inn i kategorier
    """
    
    q_and_a = {}
    
    for file in Q_AND_A_FILES:
        if file.stat().st_size == 0:
            continue
        
        with file.open("r", encoding="utf-8") as f:
            q_and_a[file.stem] = tuple(json.load(f))
    return q_and_a

if __name__ == '__main__':
    print(f"get_qap:\n\t{get_qap()}")
    print(f"get_texts:\n\t{get_texts()}")