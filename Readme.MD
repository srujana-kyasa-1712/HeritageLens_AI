HeritageLens AI

Explore. Understand. Preserve.

An Intelligent Platform for Exploring, Understanding, and Learning About Historical and Cultural Heritage Using Artificial Intelligence.

Project description

HeritageLens AI is an educational web application built with Streamlit and the Google Gemini API. Users can browse 15 Indian heritage sites, read curated information about each one, chat with an AI guide, get simple explanations, take AI-generated quizzes and receive personalised recommendations.

All AI features are grounded in the site records stored in the app, and the system instruction tells Gemini not to invent facts and to say when something is uncertain.

Features
Home: hero section, feature overview, demo statistics and a learning dashboard
Explore Heritage: live search plus Category, Region/State and Historical Period filters (they work together), sorting, site cards with images
Site details: overview, history, architecture, cultural significance, facts and why it matters
AI Heritage Guide: chat interface with suggested questions, conversation history and site-specific context
Explain Simply: student-friendly explanation of any site in one click
Heritage Quiz: 5 or 10 multiple-choice questions by site or category, one question at a time, score, accuracy and answer review
Recommendations: Gemini picks sites from the collection based on your interests, region and period
Favorites: save sites for the current session
Learning dashboard: sites explored, questions asked, quizzes completed, best score, favorites
Error handling: missing API key, API failures, empty questions, bad AI output and failed images never crash the app
Technology stack
Python 3.10+
Streamlit
Google Gemini API (google-genai)
pandas
python-dotenv
HTML and CSS embedded in app.py
Project structure
HeritageLens-AI/
├── app.py
├── requirements.txt
├── README.md
├── .env.example      (copy to .env and add your key)
└── .gitignore
Installation
Install Python 3.10 or newer.
Create and activate a virtual environment. Windows (PowerShell):
   python -m venv venv
   venv\Scripts\Activate.ps1

Mac / Linux:

   python3 -m venv venv
   source venv/bin/activate
Install the requirements:
   pip install -r requirements.txt
Gemini API setup
Create a free API key at Google AI Studio.
Provide the key in one of these ways.

Local development (.env file)

Copy .env.example to .env and edit it:

GEMINI_API_KEY=YOUR_API_KEY

Local development (Streamlit secrets)

Create .streamlit/secrets.toml:

GEMINI_API_KEY = "YOUR_API_KEY"

Streamlit Community Cloud

Open your app, go to Settings → Secrets and add:

GEMINI_API_KEY = "YOUR_API_KEY"

The app reads st.secrets["GEMINI_API_KEY"] first, then the GEMINI_API_KEY environment variable (including .env). The key is never displayed and never sent to the browser.

The default model is gemini-2.5-flash. To use another model, set GEMINI_MODEL in .env or in Streamlit secrets.

How to run
python -m streamlit run app.py

Do not start the app with python app.py.

Usage
Open Explore Heritage, search or filter, and click View Details on a site.
Use Ask AI About This Site, Explain Simply or Generate Quiz from the detail page.
Chat with the guide on AI Heritage Guide, or take a custom quiz on Heritage Quiz.
Add sites to Favorites and get ideas from Recommendations.

Favorites, chat history and statistics last for the current browser session only.

Images

Photos are looked up at runtime from Wikipedia (REST summary API) using each site's article title, then cached for an hour. If a lookup fails or you are offline, a styled placeholder is shown instead. Photos belong to their respective authors on Wikimedia Commons.

Security
Never put a real API key in app.py.
Never commit .env or .streamlit/secrets.toml (both are in .gitignore).
If a key is ever exposed, delete it in Google AI Studio and create a new one.
Data accuracy

The heritage records were written for educational use. Before submitting this project or relying on it for research, please verify names, dates and claims against authoritative sources such as the Archaeological Survey of India, UNESCO and state tourism departments.

Future enhancements
Interactive map of heritage sites
More sites and a database backend
Telugu and Hindi explanations
Saved favorites and quiz history across sessions
Image upload to identify a monument
Audio narration of site stories
Author

Your Name, Your College, Year