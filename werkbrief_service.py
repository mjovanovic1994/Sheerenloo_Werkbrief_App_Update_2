import os
import json
import uuid
from datetime import datetime

MAP = "werkbrieven"


def ensure_map():
    if not os.path.exists(MAP):
        os.makedirs(MAP)


def save(data):
    ensure_map()

    data["id"] = str(uuid.uuid4())
    data["datum"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    path = os.path.join(MAP, f"{data['id']}.json")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    return data["id"]


def get_all():
    ensure_map()
    result = []

    for file in os.listdir(MAP):
        if file.endswith(".json"):
            with open(os.path.join(MAP, file), encoding="utf-8") as f:
                result.append(json.load(f))

    return sorted(result, key=lambda x: x["datum"], reverse=True)


def get(id):
    path = os.path.join(MAP, f"{id}.json")
    if not os.path.exists(path):
        return None

    with open(path, encoding="utf-8") as f:
        return json.load(f)


def delete(id):
    path = os.path.join(MAP, f"{id}.json")
    if os.path.exists(path):
        os.remove(path)
        return True
    return False