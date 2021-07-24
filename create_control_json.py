import json

ctrl = {"polling_interval": 5,
        "safe_as_csv": True,
        "max_current": 64,
       }

with open("control.json", "w") as file:
    json.dump(ctrl, file)

"""
with open("control.json", "r") as file:
    c2 = json.load(file)

print(c2)
"""