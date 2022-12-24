import spacy
import medspacy
from medspacy.ner import TargetRule
from medspacy.visualization import visualize_ent
import pandas as pd
nlp = medspacy.load()

df = pd.read_csv("saved_csv/event_data.csv", sep = "|")
text = df.text

target_matcher = nlp.get_pipe("medspacy_target_matcher")

target_rules = [
    TargetRule("Hypopyon", "PROBLEM"),
    TargetRule("Endophthalmitis", "PROBLEM", pattern=[{"LOWER": "afib"}]),
    TargetRule("pneumonia", "PROBLEM"),
    TargetRule("Type II Diabetes Mellitus", "PROBLEM", 
              pattern=[
                  {"LOWER": "type"},
                  {"LOWER": {"IN": ["2", "ii", "two"]}},
                  {"LOWER": {"IN": ["dm", "diabetes"]}},
                  {"LOWER": "mellitus", "OP": "?"}
              ]),
    TargetRule("Phacoemulsification", "MEDICATION")
]

target_matcher.add(target_rules)

doc = nlp(text[1])
visualize_ent(doc)



