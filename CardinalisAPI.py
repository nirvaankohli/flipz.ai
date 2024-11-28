
from pydantic import BaseModel
import os
import openai

class Format(BaseModel):
    questions: list[str]
    answers: list[str]
    terms: list[str]
    definitions_of_terms: list[str]
    main_events_people_and_explenation: list[str]
    
class FormatStudyGuide(BaseModel):
    name: str
    date: str
    participants: list[str]

class API:

    def __init__(self, key):
        self.key = os.getenv("OPENAI_API_KEY")
        if not self.key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        self.activate()

        self.model = 'gpt-4o-mini-2024-07-18'
        self.activate()

    def activate(self):


        self.client = openai.OpenAI(api_key=self.key)

    def get_key(self):
        return self.key
    
    def set_key(self, key):
        self.key = key

    def set_model(self, model):
        self.model = model

    def get_model(self):
        return self.model
    
    def get_client(self):
        return self.client

    def flashcards(self, topic, grade_level):

        self.activate()

        
        grade_level_1 = grade_level
        completion = self.client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=[
        {"role": "system", "content": f"""You are a assistant for a {grade_level_1} level student and help them by generating flashcards on a given topic. Topic is provided below. Generate flash cards(12+) in json format."""},

        {"role": "user", "content": f"Topic - {topic}"},
        ], response_format= {
        "type": "json_schema",
        "json_schema": {
  "name": "study_guide",
  "schema": {
    "type": "object",
    "properties": {
      "terms": {
        "type": "array",
        "description": "A list of terms that are included in the study guide.",
        "items": {
          "type": "object",
          "properties": {
            "term": {
              "type": "string",
              "description": "The term to be defined."
            },
            "answer": {
              "type": "string",
              "description": "The definition or explanation of the term."
            }
          },
          "required": [
            "term",
            "answer"
          ],
          "additionalProperties": False
        }
      },
      "study_guide_details": {
        "type": "string",
        "description": "A brief overview or further information regarding the study material."
      }
    },
    "required": [
      "terms",
      "study_guide_details"
    ],
    "additionalProperties": False
  },
  "strict": True
}}
         
)
        event = completion.choices[0].message.content
      


        return event


    def flashcards_and_study_guide(self):

        None

