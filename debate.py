
import gradio as gr
from gtts import gTTS
import os
import speech_recognition as sr
import openai
import json
import time
import speech_recognition as sr
from IPython.display import Audio



def play_audio(audio_file):
    return Audio(audio_file, autoplay=True)

def load_config():
    with open('/Users/yashtobre/Downloads/config.json', 'r') as f:
        config = json.load(f)
    return config

config = load_config()
os.environ['OPENAI_API_KEY'] = config['openai_api_key']
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_audio(question, filename):
    tts = gTTS(text=question, lang='en')
    tts.save(filename)

def query_questions(topic, num_questions):
    prompt = f"Generate a debate prompt with topic as {topic}."

    messages = [
        {"role": "system", "content": prompt}
    ]

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages
        )

        # Split the response into a list of questions
        questions_list = response.choices[0].message["content"].split("\n")

        # Remove any empty strings from the list
        questions_list = [question.strip() for question in questions_list if question.strip()]

        return questions_list
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

def conduct_debate(topic, question):
    answers = {}
    recognizer = sr.Recognizer()

    # Playing the question
    print("Question:", question[0])
    generate_audio(question[0], "question.mp3")
    os.system("afplay question.mp3")
    time.sleep(10)  # 30-second preparation time

    # Determining which team argues for and which against
    teams = ["for", "against"]

    for i, team in enumerate(teams, start=1):  # Assuming 2 teams
        team_prompt = f"Team {i}, arguing {team}. Participant {i}, please speak your answer within 1 minute."
        generate_audio(team_prompt, f"response_team_{i}.mp3")
        os.system(f"afplay response_team_{i}.mp3")

        with sr.Microphone() as source:
            print("Listening...")
            audio = recognizer.listen(source, timeout=60)
            print("Recognition completed.")

        try:
            answer = recognizer.recognize_google(audio)
            print(f"Team {i} answered:", answer)
            answers.setdefault(team, []).append(answer)
        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand audio")
        except sr.RequestError as e:
            print("Could not request results from Google Speech Recognition service; {0}".format(e))

    return answers

def debate_interface(topic, num_questions):
    topic = topic[0]
    num_questions = int(num_questions[0])
    questions = query_questions(topic, num_questions)
    debate_answers = conduct_debate(topic, questions)

    # Analyze and decide the winner
    affirmative_answers = debate_answers.get("for", [])
    negative_answers = debate_answers.get("against", [])
    prompt = f"Analyze answers by each participant, For side : {affirmative_answers}; Against side {negative_answers} for the debate_topic, {questions[0]} and provide feedback as a judge of debate competition, announce the winner and highlight action items or additional resources for improvement."

    messages = [
        {"role": "system", "content": prompt}
    ]

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages
        )

        # Split the response into a list of feedback messages
        feedback_list = response.choices[0].message["content"].split("\n")

        # Remove any empty strings from the list
        feedback_list = [feedback.strip() for feedback in feedback_list if feedback.strip()]

        # Concatenate the feedback messages into a single string
        feedback_string = "\n".join(feedback_list)

        return feedback_string
    except Exception as e:
        print(f"An error occurred: {e}")
        return ""

iface = gr.Interface(
    fn=debate_interface,
    inputs=["text", "text"],
    outputs="text",
    title="Debate Interface",
    description="Generate a debate prompt based on a given topic and conduct a debate with participants.",
    examples=[
        ["Climate Change", "1"]
    ]
)

iface.launch()
