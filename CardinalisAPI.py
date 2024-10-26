
from pydantic import BaseModel



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
        self.key = key
        self.model = 'gpt-4o-mini'
        self.activate()

    def activate(self):

        from openai import OpenAI
        self.client = OpenAI(api_key=self.key)

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

        if type(grade_level) == int:
            grade_level_1 = str(grade_level) + "th grade student"

        else: 
            grade_level_1 = grade_level
        completion = self.client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
        {"role": "system", "content": f"You are a assistant for a {grade_level_1} and help them by generating flashcards on a given topic. Topic is provided below. Generate flash cards(12+) in json format."},
        {"role": "user", "content": f"Topic - {topic}"},
        ],
         response_format=Format,
)
        event = completion.to_dict()


        return event


    def flashcards_and_study_guide(self):

        None

if __name__ == '__main__':
    API()