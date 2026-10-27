import json
import requests
import pandas as pd
from helpers import tidy

print(json.dumps(tidy(requests.get("https://api.example.invalid/prs").json())))
