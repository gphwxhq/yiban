import json

__fileName= "list.json"

def configWriter(form):
    with open(__fileName, "w", encoding='utf-8') as f:
        json.dump(form, f, ensure_ascii=False)

def configLoader():
        with open(__fileName, 'r', encoding='utf-8') as f:
            t = f.read()
            oform = json.loads(t)
        return oform