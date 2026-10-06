"""
HeritageLens AI
Explore. Understand. Preserve.
 
An Intelligent Platform for Exploring, Understanding, and Learning About
Historical and Cultural Heritage Using Artificial Intelligence.
 
Run with:
    python -m streamlit run app.py
"""
 
import copy
import html
import json
import os
import re
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
 
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types
 
load_dotenv()
 
st.set_page_config(
    page_title="HeritageLens AI",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "HeritageLens AI - an educational platform for exploring heritage with AI.",
    },
)
 
# =============================================================================
# CONSTANTS
# =============================================================================
DEFAULT_MODEL = "gemini-2.5-flash"
 
PAGES = [
    "Home",
    "Explore Heritage",
    "AI Heritage Guide",
    "Heritage Quiz",
    "Recommendations",
    "Favorites",
    "About",
]
PAGE_ICONS = {
    "Home": "🏠",
    "Explore Heritage": "🧭",
    "AI Heritage Guide": "🤖",
    "Heritage Quiz": "🧠",
    "Recommendations": "✨",
    "Favorites": "♥",
    "About": "ℹ️",
}
 
CATEGORIES = [
    "Fort",
    "Temple",
    "Monument",
    "Palace",
    "Archaeological Site",
    "Cave",
    "Tomb",
    "Cultural Heritage",
]
PERIODS = ["Ancient", "Medieval", "Mughal", "Colonial", "Modern"]
PERIOD_ORDER = {p: i for i, p in enumerate(PERIODS)}
CATEGORY_ICONS = {
    "Fort": "🏰",
    "Temple": "🛕",
    "Monument": "🏛️",
    "Palace": "👑",
    "Archaeological Site": "⛏️",
    "Cave": "🪨",
    "Tomb": "🕌",
    "Cultural Heritage": "🎭",
}
INTEREST_OPTIONS = [
    "Architecture",
    "History",
    "Culture",
    "Ancient civilizations",
    "Forts",
    "Temples",
    "Palaces",
    "Archaeology",
]
SORT_OPTIONS = [
    "Name (A-Z)",
    "Name (Z-A)",
    "Period (oldest first)",
    "Category",
    "State",
]
 
SYSTEM_INSTRUCTION = (
    "You are HeritageLens AI, an educational assistant specializing in historical "
    "and cultural heritage.\n\n"
    "Your purpose is to help users understand historical sites, monuments, "
    "architecture, traditions and cultural significance.\n\n"
    "Give clear, educational and easy-to-understand answers.\n\n"
    "Do not invent historical facts.\n\n"
    "If information is uncertain, say that it is uncertain.\n\n"
    "When the user asks about a heritage site available in the HeritageLens "
    "database, prioritize the supplied site information.\n\n"
    "Do not present guesses as facts.\n\n"
    "Use simple language when requested.\n\n"
    "For academic questions, provide structured explanations.\n\n"
    "Your responses should be informative, respectful and suitable for students."
)
 
MSG_NO_KEY = (
    "Gemini API key is not configured. Please add GEMINI_API_KEY to Streamlit "
    "secrets or your .env file."
)
MSG_AI_DOWN = "HeritageLens AI is temporarily unavailable. Please try again."
AI_NOTICE = (
    "HeritageLens AI provides AI-generated educational information. Historical "
    "interpretations may vary between sources. For academic or professional "
    "research, users should verify information using authoritative historical, "
    "archaeological and heritage sources."
)
 
# =============================================================================
# HERITAGE DATABASE
# `image` holds the English Wikipedia article title used to look up a photo at
# runtime (see fetch_images). If the lookup fails, a placeholder is shown.
# =============================================================================
HERITAGE_SITES = [
    {
        "id": "golconda-fort",
        "name": "Golconda Fort",
        "location": "Hyderabad",
        "state": "Telangana",
        "category": "Fort",
        "period": "Medieval",
        "description": (
            "A massive granite fortress on the western edge of Hyderabad, once the "
            "capital of the Qutb Shahi dynasty and famous for its acoustics and "
            "water-supply system."
        ),
        "history": (
            "Golconda began as a smaller fort under the Kakatiya dynasty in the 13th "
            "century. It later passed to the Bahmani Sultanate and, from the early "
            "16th century, became the capital of the Qutb Shahi dynasty, who greatly "
            "expanded the fortifications. The Qutb Shahi capital later shifted to "
            "Hyderabad, but Golconda remained an important stronghold until the "
            "Mughal emperor Aurangzeb captured it in 1687 after a prolonged siege."
        ),
        "architecture": (
            "Built mainly of granite on a hill, the fort has several layers of walls, "
            "many bastions, massive gateways, and palaces and mosques inside. It is "
            "known for the acoustic design of the Fateh Darwaza entrance and for an "
            "advanced water-supply system. The style blends Indo-Islamic traditions."
        ),
        "significance": (
            "Golconda was a political and commercial centre of the Deccan, closely "
            "associated with the diamond trade of the region, and it reflects the "
            "Indo-Persian culture of the Qutb Shahi court."
        ),
        "facts": [
            "A hand-clap at the Fateh Darwaza entrance is traditionally said to be audible near the highest point of the fort.",
            "The region around Golconda was a famous centre of the diamond trade.",
            "The Qutb Shahi Tombs are located a short distance from the fort.",
            "The fort's name is often linked to the Telugu words for 'shepherd's hill', though the origin of the name is debated.",
        ],
        "why_it_matters": "It shows how medieval Deccan rulers combined military engineering, trade and court culture in one stronghold.",
        "image": "Golconda Fort",
        "keywords": ["Hyderabad", "Telangana", "Qutb Shahi", "Kakatiya", "Bahmani", "granite", "Deccan", "diamond", "Aurangzeb", "fort"],
    },
    {
        "id": "charminar",
        "name": "Charminar",
        "location": "Hyderabad",
        "state": "Telangana",
        "category": "Monument",
        "period": "Medieval",
        "description": (
            "A four-minaret granite monument built in 1591 that has become the "
            "best-known symbol of Hyderabad."
        ),
        "history": (
            "Charminar was built in 1591 by Muhammad Quli Qutb Shah, the Qutb Shahi "
            "ruler who founded Hyderabad. A popular tradition says it was built to "
            "mark the end of a plague epidemic in the city, although historians "
            "discuss other motives as well."
        ),
        "architecture": (
            "The monument is built of granite, limestone and mortar in the Indo-Islamic "
            "style. It has four grand arches and four tall minarets, and a mosque "
            "occupies the upper floor."
        ),
        "significance": (
            "Charminar marks the founding of Hyderabad and stands at the heart of the "
            "old city's markets, crafts and food culture."
        ),
        "facts": [
            "The name Charminar means 'four minarets'.",
            "A mosque is located on the upper floor of the monument.",
            "It stands in the middle of one of Hyderabad's busiest old-city market areas.",
            "The Mecca Masjid, another Qutb Shahi landmark, is close by.",
        ],
        "why_it_matters": "It is a living landmark where 400-year-old architecture still sits at the centre of everyday city life.",
        "image": "Charminar",
        "keywords": ["Hyderabad", "Telangana", "Qutb Shahi", "Muhammad Quli Qutb Shah", "minaret", "old city", "1591", "mosque"],
    },
    {
        "id": "qutb-shahi-tombs",
        "name": "Qutb Shahi Tombs",
        "location": "Ibrahim Bagh, near Golconda, Hyderabad",
        "state": "Telangana",
        "category": "Tomb",
        "period": "Medieval",
        "description": (
            "A garden complex of domed tombs where Qutb Shahi rulers and members of "
            "their families were laid to rest."
        ),
        "history": (
            "The tombs were built over roughly the 16th and 17th centuries by the "
            "Qutb Shahi dynasty, which ruled the kingdom of Golconda. Over time the "
            "complex became a royal burial ground. Conservation work in recent "
            "years, including a project with the Aga Khan Trust for Culture, has "
            "restored many of the structures."
        ),
        "architecture": (
            "The tombs are domed structures set on raised platforms, built of stone "
            "with decorative plasterwork. The style combines Persian, Pathan and "
            "Hindu architectural influences, and the tombs are set in landscaped "
            "gardens."
        ),
        "significance": (
            "The complex shows the artistic taste of the Qutb Shahi court and "
            "preserves the memory of the dynasty that shaped early Hyderabad."
        ),
        "facts": [
            "The complex lies close to Golconda Fort, in an area known as Ibrahim Bagh.",
            "Each major tomb has a dome and stands on a raised platform.",
            "The site was extensively conserved in recent decades.",
        ],
        "why_it_matters": "It is one of the best places to see how the Qutb Shahi rulers wanted to be remembered.",
        "image": "Qutb Shahi Tombs",
        "keywords": ["Hyderabad", "Telangana", "Qutb Shahi", "tomb", "dome", "garden", "Golconda", "Deccan", "Ibrahim Bagh"],
    },
    {
        "id": "warangal-fort",
        "name": "Warangal Fort",
        "location": "Warangal",
        "state": "Telangana",
        "category": "Fort",
        "period": "Medieval",
        "description": (
            "The ruined capital fort of the Kakatiya dynasty, known for its four "
            "monumental stone gateways."
        ),
        "history": (
            "Warangal was the capital of the Kakatiya dynasty, which ruled much of the "
            "Telugu region in the 12th to 14th centuries. The fort took shape in the "
            "13th century under rulers such as Ganapati Deva and was associated with "
            "Rani Rudrama Devi. It was taken by the Delhi Sultanate in the early 14th "
            "century."
        ),
        "architecture": (
            "The fort has concentric layers of defences with an earthen outer rampart "
            "and an inner stone fort. Its most famous features are the four large "
            "carved stone gateways known as the Kakatiya Kala Thoranam, which stand "
            "near the ruins of a Shiva temple."
        ),
        "significance": (
            "The Kakatiya Kala Thoranam has become an emblem of Telangana, and the fort "
            "represents the political and artistic achievements of the Kakatiya period."
        ),
        "facts": [
            "The four carved gateways are called the Kakatiya Kala Thoranam.",
            "Much of the fort is in ruins, but the gateways and temple remains survive.",
            "Rani Rudrama Devi is remembered as one of the notable women rulers of medieval India.",
        ],
        "why_it_matters": "It preserves the memory of the Kakatiya kingdom, which shaped the art and identity of the Telugu region.",
        "image": "Warangal Fort",
        "keywords": ["Warangal", "Telangana", "Kakatiya", "Rudrama Devi", "Ganapati Deva", "gateway", "toranam", "fort"],
    },
    {
        "id": "thousand-pillar-temple",
        "name": "Thousand Pillar Temple",
        "location": "Hanamkonda, Warangal",
        "state": "Telangana",
        "category": "Temple",
        "period": "Medieval",
        "description": (
            "A 12th-century Kakatiya temple, also called the Rudreshwara Swamy "
            "Temple, famous for its carved pillars and polished stonework."
        ),
        "history": (
            "The temple was built in 1163 CE by the Kakatiya king Rudra Deva and is "
            "also known as the Rudreshwara Swamy Temple. It is one of the earliest "
            "major monuments of the Kakatiya dynasty."
        ),
        "architecture": (
            "The temple follows the Kakatiya style, with a star-shaped (stellate) "
            "platform, finely carved pillars and a triple-shrine plan with shrines "
            "for Shiva, Vishnu and Surya. A large monolithic Nandi (bull) statue "
            "sits in front of the temple."
        ),
        "significance": (
            "It is one of the finest examples of Kakatiya temple architecture and "
            "stone craftsmanship in Telangana."
        ),
        "facts": [
            "The temple was built in 1163 CE.",
            "It has three shrines, often described as dedicated to Shiva, Vishnu and Surya.",
            "A large Nandi carved from a single block of dark stone faces the main shrine.",
            "The star-shaped layout is a signature feature of Kakatiya temples.",
        ],
        "why_it_matters": "It shows the skill of Kakatiya sculptors and set the style for later temples in the region.",
        "image": "Thousand Pillar Temple",
        "keywords": ["Warangal", "Hanamkonda", "Telangana", "Kakatiya", "Rudra Deva", "temple", "Shiva", "Nandi", "pillars"],
    },
    {
        "id": "hampi",
        "name": "Hampi",
        "location": "Hampi, Vijayanagara district",
        "state": "Karnataka",
        "category": "Archaeological Site",
        "period": "Medieval",
        "description": (
            "The ruins of Vijayanagara, the capital of one of South India's greatest "
            "empires, spread across a landscape of giant boulders."
        ),
        "history": (
            "Hampi was the centre of the Vijayanagara Empire, which rose in the 14th "
            "century and reached its height under rulers such as Krishnadevaraya in "
            "the early 16th century. After the Battle of Talikota in 1565, the "
            "capital was captured and abandoned. It is a UNESCO World Heritage Site "
            "(inscribed in 1986)."
        ),
        "architecture": (
            "The site includes temples, royal enclosures, markets, water structures "
            "and elephant stables. Temple architecture follows the Dravidian style, "
            "and highlights include the Virupaksha Temple and the Vittala Temple "
            "with its famous stone chariot."
        ),
        "significance": (
            "Hampi preserves the layout of a great medieval city and shows the "
            "artistic and religious culture of the Vijayanagara period."
        ),
        "facts": [
            "The stone chariot at the Vittala Temple is one of India's most recognised monuments.",
            "The Virupaksha Temple is still used for worship today.",
            "Hampi lies along the Tungabhadra River among striking granite boulders.",
            "It was inscribed as a UNESCO World Heritage Site in 1986.",
        ],
        "why_it_matters": "It lets visitors walk through the remains of an entire imperial city and its landscape.",
        "image": "Hampi",
        "keywords": ["Karnataka", "Vijayanagara", "Krishnadevaraya", "Dravidian", "UNESCO", "Tungabhadra", "ruins", "empire", "Vittala"],
    },
    {
        "id": "taj-mahal",
        "name": "Taj Mahal",
        "location": "Agra",
        "state": "Uttar Pradesh",
        "category": "Tomb",
        "period": "Mughal",
        "description": (
            "A white-marble mausoleum on the banks of the Yamuna, built by the "
            "Mughal emperor Shah Jahan in memory of his wife Mumtaz Mahal."
        ),
        "history": (
            "Mumtaz Mahal died in 1631, and Shah Jahan commissioned the Taj Mahal in "
            "her memory. Construction began around 1632, the main mausoleum was "
            "largely complete by the early 1640s, and the wider complex was finished "
            "in the following years. Ustad Ahmad Lahori is traditionally credited as "
            "the chief architect. It was inscribed as a UNESCO World Heritage Site "
            "in 1983."
        ),
        "architecture": (
            "The monument is a Mughal masterpiece with a central dome, four minarets, "
            "a raised platform and a symmetrical charbagh (four-part) garden with "
            "reflecting pools. White marble is decorated with inlaid semi-precious "
            "stones and calligraphy, blending Persian, Islamic and Indian elements."
        ),
        "significance": (
            "The Taj Mahal is one of the world's best-known buildings and a symbol of "
            "Mughal art, architecture and the memory of love and loss."
        ),
        "facts": [
            "Shah Jahan himself is also buried at the Taj Mahal.",
            "The decoration uses inlaid stones in a technique known as pietra dura.",
            "The gardens follow the charbagh plan used in Mughal and Persian gardens.",
            "It was inscribed as a UNESCO World Heritage Site in 1983.",
        ],
        "why_it_matters": "It is a landmark of world architecture that shows how art, symmetry and craftsmanship can express human emotion.",
        "image": "Taj Mahal",
        "keywords": ["Agra", "Uttar Pradesh", "Mughal", "Shah Jahan", "Mumtaz Mahal", "marble", "mausoleum", "UNESCO", "charbagh"],
    },
    {
        "id": "red-fort",
        "name": "Red Fort",
        "location": "Delhi",
        "state": "Delhi",
        "category": "Fort",
        "period": "Mughal",
        "description": (
            "A red-sandstone fort-palace built by Shah Jahan as the centre of his new "
            "capital, Shahjahanabad."
        ),
        "history": (
            "Shah Jahan moved his capital from Agra to Delhi and built the Red Fort "
            "between 1638 and 1648 as the palace-fort of the new city of "
            "Shahjahanabad. It remained the main residence of the Mughal emperors "
            "for about two centuries. After the events of 1857, the British took "
            "control and used it as a military base. It was inscribed as part of a "
            "UNESCO World Heritage Site in 2007."
        ),
        "architecture": (
            "The fort is built of red sandstone with massive walls and gateways such "
            "as the Lahori Gate. Inside are audience halls (Diwan-i-Aam and "
            "Diwan-i-Khas), pavilions, gardens and water channels, combining Mughal, "
            "Persian and Indian design."
        ),
        "significance": (
            "The Red Fort was the political heart of the Mughal Empire and is a "
            "symbol of Indian independence, where the national flag is hoisted every "
            "Independence Day."
        ),
        "facts": [
            "The fort takes its name from the red sandstone of its walls.",
            "The Prime Minister of India addresses the nation from the Red Fort on Independence Day.",
            "The Lahori Gate is its main entrance.",
            "It was built between 1638 and 1648.",
        ],
        "why_it_matters": "It connects the history of the Mughal court with the story of modern India.",
        "image": "Red Fort",
        "keywords": ["Delhi", "Mughal", "Shah Jahan", "Shahjahanabad", "red sandstone", "Lahori Gate", "UNESCO", "fort", "Independence Day"],
    },
    {
        "id": "ajanta-caves",
        "name": "Ajanta Caves",
        "location": "Near Chhatrapati Sambhajinagar (Aurangabad)",
        "state": "Maharashtra",
        "category": "Cave",
        "period": "Ancient",
        "description": (
            "About thirty rock-cut Buddhist caves known for their ancient paintings "
            "and sculptures."
        ),
        "history": (
            "The caves were carved in two main phases, starting around the 2nd century "
            "BCE and continuing until roughly the 5th to 6th century CE. They were "
            "used as Buddhist monasteries and prayer halls and were later forgotten "
            "until a British officer came across them in 1819. Ajanta was inscribed "
            "as a UNESCO World Heritage Site in 1983."
        ),
        "architecture": (
            "The caves are cut into a horseshoe-shaped rock face above the Waghora "
            "river gorge. They include chaitya halls (prayer halls) and viharas "
            "(monasteries), with carved pillars, sculptures and wall paintings."
        ),
        "significance": (
            "Ajanta's paintings, many illustrating Buddhist Jataka stories, are among "
            "the most important surviving examples of ancient Indian painting."
        ),
        "facts": [
            "The site contains about 30 rock-cut caves.",
            "Many paintings depict Jataka tales, stories of the Buddha's previous lives.",
            "The caves were rediscovered in 1819.",
            "Ajanta is a UNESCO World Heritage Site (1983).",
        ],
        "why_it_matters": "It preserves rare ancient paintings and shows how Buddhist communities lived and worshipped.",
        "image": "Ajanta Caves",
        "keywords": ["Maharashtra", "Buddhist", "rock-cut", "paintings", "Jataka", "Satavahana", "Vakataka", "UNESCO", "cave", "ancient"],
    },
    {
        "id": "ellora-caves",
        "name": "Ellora Caves",
        "location": "Near Chhatrapati Sambhajinagar (Aurangabad)",
        "state": "Maharashtra",
        "category": "Cave",
        "period": "Medieval",
        "description": (
            "A group of 34 rock-cut Buddhist, Hindu and Jain caves, including the "
            "magnificent Kailasa Temple."
        ),
        "history": (
            "The caves at Ellora were carved between about the 6th and 10th centuries "
            "CE. The famous Kailasa Temple (Cave 16) is associated with the "
            "Rashtrakuta dynasty. Ellora was inscribed as a UNESCO World Heritage "
            "Site in 1983."
        ),
        "architecture": (
            "The site has 34 monasteries and temples cut into a basalt cliff: about 12 "
            "Buddhist, 17 Hindu and 5 Jain. The Kailasa Temple is carved top-down "
            "from a single rock into a freestanding temple complex."
        ),
        "significance": (
            "Ellora is a rare place where Buddhist, Hindu and Jain monuments stand "
            "side by side, showing religious coexistence in ancient and early "
            "medieval India."
        ),
        "facts": [
            "Ellora has 34 caves: roughly 12 Buddhist, 17 Hindu and 5 Jain.",
            "The Kailasa Temple was carved out of a single rock mass.",
            "It is a UNESCO World Heritage Site (1983).",
        ],
        "why_it_matters": "It is a monument to engineering skill and to the shared religious heritage of India.",
        "image": "Ellora Caves",
        "keywords": ["Maharashtra", "Kailasa", "Rashtrakuta", "rock-cut", "Buddhist", "Hindu", "Jain", "UNESCO", "cave"],
    },
    {
        "id": "konark-sun-temple",
        "name": "Konark Sun Temple",
        "location": "Konark, Puri district",
        "state": "Odisha",
        "category": "Temple",
        "period": "Medieval",
        "description": (
            "A 13th-century temple shaped like a giant chariot of the Sun god, "
            "decorated with carved wheels, horses and sculptures."
        ),
        "history": (
            "The temple was built in the 13th century, around the 1250s, by King "
            "Narasimhadeva I of the Eastern Ganga dynasty. It is dedicated to Surya, "
            "the Sun god. The main sanctum tower has since collapsed, but the "
            "remaining structures are preserved. It is a UNESCO World Heritage Site "
            "(1984)."
        ),
        "architecture": (
            "The temple is designed as a colossal stone chariot with 12 pairs of "
            "carved wheels pulled by seven horses. It follows the Kalinga style of "
            "temple architecture and is covered in sculptures and fine carvings."
        ),
        "significance": (
            "Konark is a masterpiece of Kalinga architecture and a symbol of the "
            "importance of Sun worship in Odisha."
        ),
        "facts": [
            "The temple is shaped as the chariot of the Sun god, with 12 pairs of wheels and seven horses.",
            "It is often called the 'Black Pagoda' in older European accounts.",
            "The wheels of the chariot can be read as sundials.",
            "It is a UNESCO World Heritage Site (1984).",
        ],
        "why_it_matters": "It combines astronomy, religion and sculpture in a single architectural idea.",
        "image": "Konark Sun Temple",
        "keywords": ["Odisha", "Kalinga", "Sun god", "Surya", "Eastern Ganga", "chariot", "UNESCO", "temple", "wheel"],
    },
    {
        "id": "sanchi-stupa",
        "name": "Sanchi Stupa",
        "location": "Sanchi, Raisen district",
        "state": "Madhya Pradesh",
        "category": "Archaeological Site",
        "period": "Ancient",
        "description": (
            "One of the oldest stone structures in India, a Buddhist stupa famed for "
            "its beautifully carved gateways."
        ),
        "history": (
            "The Great Stupa at Sanchi was commissioned by the Mauryan emperor Ashoka "
            "in the 3rd century BCE and was enlarged and decorated in later centuries. "
            "The four carved gateways (toranas) were added around the 1st century "
            "BCE during the Satavahana period. Sanchi was inscribed as a UNESCO "
            "World Heritage Site in 1989."
        ),
        "architecture": (
            "The Great Stupa is a solid hemispherical dome surrounded by a railing and "
            "four elaborately carved gateways. The carvings show scenes from the "
            "Buddha's life and the Jataka tales, often using symbols such as the "
            "wheel, the footprints and the Bodhi tree to represent the Buddha."
        ),
        "significance": (
            "Sanchi is among the best preserved early Buddhist monuments in India and "
            "an important record of early Buddhist art."
        ),
        "facts": [
            "The Great Stupa was originally commissioned by Ashoka in the 3rd century BCE.",
            "Its four gateways are covered in detailed carvings.",
            "Early carvings show the Buddha through symbols rather than as a human figure.",
            "Sanchi is a UNESCO World Heritage Site (1989).",
        ],
        "why_it_matters": "It is a window into how early Buddhism looked, spread and was supported in ancient India.",
        "image": "Sanchi Stupa",
        "keywords": ["Madhya Pradesh", "Buddhist", "Ashoka", "stupa", "Mauryan", "Satavahana", "torana", "UNESCO", "archaeology", "ancient"],
    },
    {
        "id": "mysore-palace",
        "name": "Mysore Palace",
        "location": "Mysuru",
        "state": "Karnataka",
        "category": "Palace",
        "period": "Colonial",
        "description": (
            "The royal palace of the Wadiyar dynasty, an Indo-Saracenic landmark that "
            "lights up during the Dasara festival."
        ),
        "history": (
            "An older wooden palace on this site was destroyed by fire in 1897. The "
            "present palace was built to replace it and was completed in 1912 for "
            "the Wadiyar rulers of Mysore, with the English architect Henry Irwin "
            "associated with the design."
        ),
        "architecture": (
            "The palace is built in the Indo-Saracenic style, blending Hindu, Islamic, "
            "Rajput and Gothic elements. It has domes, arches, turrets, ornate halls "
            "and richly decorated interiors."
        ),
        "significance": (
            "It is the centrepiece of Mysuru's royal heritage and the focus of the "
            "city's Dasara celebrations."
        ),
        "facts": [
            "The present palace was completed in 1912.",
            "It is illuminated with thousands of lights during special occasions such as Dasara.",
            "The architecture mixes several regional and international styles.",
        ],
        "why_it_matters": "It shows how Indian royal architecture adapted to the colonial era while remaining a living cultural centre.",
        "image": "Mysore Palace",
        "keywords": ["Karnataka", "Mysuru", "Mysore", "Wadiyar", "Indo-Saracenic", "Dasara", "palace", "royal", "Henry Irwin"],
    },
    {
        "id": "meenakshi-amman-temple",
        "name": "Meenakshi Amman Temple",
        "location": "Madurai",
        "state": "Tamil Nadu",
        "category": "Temple",
        "period": "Medieval",
        "description": (
            "A vibrant Dravidian temple complex dedicated to Meenakshi and "
            "Sundareswarar, with towering, colourfully sculpted gateway towers."
        ),
        "history": (
            "The temple's worship traditions are very old and Madurai is mentioned in "
            "classical Tamil literature. The present form of the temple complex was "
            "largely built or rebuilt during the Nayak period in the 16th and 17th "
            "centuries, with rulers such as Thirumalai Nayak associated with its "
            "expansion."
        ),
        "architecture": (
            "The temple is a classic example of Dravidian architecture, with a large "
            "rectangular complex, around fourteen gopurams (gateway towers) covered "
            "in colourful sculptures, a Hall of Thousand Pillars and the Golden Lotus "
            "tank (Potramarai Kulam)."
        ),
        "significance": (
            "It is one of the most important temples of Tamil Nadu and the centre of "
            "the city's religious and cultural life, including the Chithirai "
            "festival."
        ),
        "facts": [
            "The temple is dedicated to Meenakshi (a form of Parvati) and her consort Sundareswarar (Shiva).",
            "It has around fourteen gopurams covered in sculpted figures.",
            "The complex contains a Hall of Thousand Pillars and the Golden Lotus Tank.",
            "The Chithirai festival celebrates the divine wedding of Meenakshi and Sundareswarar.",
        ],
        "why_it_matters": "It is a living temple where architecture, ritual, music and festivals continue as a daily tradition.",
        "image": "Meenakshi Temple",
        "keywords": ["Tamil Nadu", "Madurai", "Dravidian", "gopuram", "Nayak", "temple", "Meenakshi", "Chithirai", "Shiva"],
    },
    {
        "id": "fatehpur-sikri",
        "name": "Fatehpur Sikri",
        "location": "Near Agra",
        "state": "Uttar Pradesh",
        "category": "Cultural Heritage",
        "period": "Mughal",
        "description": (
            "A red-sandstone city founded by Emperor Akbar as his capital, famous for "
            "the grand Buland Darwaza."
        ),
        "history": (
            "Akbar founded Fatehpur Sikri in 1571 and made it his capital. The city "
            "was abandoned after only about fifteen years; reasons suggested include "
            "water shortage and political needs, though historians debate the exact "
            "cause. It was inscribed as a UNESCO World Heritage Site in 1986."
        ),
        "architecture": (
            "The city is built of red sandstone and blends Persian, Islamic and "
            "Indian (including Gujarati and Rajput) styles. Highlights include the "
            "Jama Masjid, the Buland Darwaza gateway, the Panch Mahal and the tomb of "
            "the Sufi saint Salim Chishti."
        ),
        "significance": (
            "Fatehpur Sikri reflects Akbar's vision of a cosmopolitan court and shows "
            "the synthesis of different architectural traditions in the Mughal "
            "Empire."
        ),
        "facts": [
            "Fatehpur Sikri served as the Mughal capital for only about fifteen years.",
            "The Buland Darwaza is one of the tallest gateways in India.",
            "The city contains the tomb of the Sufi saint Salim Chishti.",
            "It is a UNESCO World Heritage Site (1986).",
        ],
        "why_it_matters": "It is a rare, well-preserved Mughal city that shows how Akbar's ideas shaped architecture and court life.",
        "image": "Fatehpur Sikri",
        "keywords": ["Uttar Pradesh", "Agra", "Akbar", "Mughal", "Buland Darwaza", "Jama Masjid", "UNESCO", "red sandstone", "capital"],
    },
]
 
# =============================================================================
# DATA HELPERS
# =============================================================================
 
 
def load_heritage_data():
    """Return the list of heritage sites."""
    return HERITAGE_SITES
 
 
def get_site(site_id):
    for site in HERITAGE_SITES:
        if site["id"] == site_id:
            return site
    return None
 
 
def get_site_by_name(name):
    for site in HERITAGE_SITES:
        if site["name"] == name:
            return site
    return None
 
 
def site_to_text(site):
    """Plain-text version of a site record, used as context for Gemini."""
    facts = "\n".join(f"- {f}" for f in site["facts"])
    return (
        f"SITE: {site['name']}\n"
        f"Location: {site['location']}, {site['state']}\n"
        f"Category: {site['category']}\n"
        f"Historical period: {site['period']}\n"
        f"Overview: {site['description']}\n"
        f"History: {site['history']}\n"
        f"Architecture: {site['architecture']}\n"
        f"Significance: {site['significance']}\n"
        f"Facts:\n{facts}"
    )
 
 
def find_mentioned_sites(text):
    """Sites whose name (or main keyword) appears in a piece of text."""
    low = text.lower()
    found = []
    for site in HERITAGE_SITES:
        short = site["name"].lower().replace(" fort", "").replace(" temple", "")
        if site["name"].lower() in low or (len(short) > 4 and short in low):
            found.append(site)
    return found
 
 
def search_heritage(query="", category="All", state="All", period="All", sort="Name (A-Z)"):
    """Search, filter and sort heritage sites. Filters combine with AND."""
    df = pd.DataFrame(load_heritage_data())
    if category != "All":
        df = df[df["category"] == category]
    if state != "All":
        df = df[df["state"] == state]
    if period != "All":
        df = df[df["period"] == period]
    if df.empty:
        return []
 
    terms = query.strip().lower().split()
    if terms:
        haystack = df.apply(
            lambda r: " ".join(
                [r["name"], r["location"], r["state"], r["category"], r["period"], r["description"]]
                + list(r["keywords"])
            ).lower(),
            axis=1,
        )
        df = df[haystack.apply(lambda text: all(t in text for t in terms))]
        if df.empty:
            return []
 
    df = df.copy()
    df["_period_rank"] = df["period"].map(PERIOD_ORDER)
    if sort == "Name (Z-A)":
        df = df.sort_values("name", ascending=False)
    elif sort == "Period (oldest first)":
        df = df.sort_values(["_period_rank", "name"])
    elif sort == "Category":
        df = df.sort_values(["category", "name"])
    elif sort == "State":
        df = df.sort_values(["state", "name"])
    else:
        df = df.sort_values("name")
    return df.drop(columns=["_period_rank"]).to_dict("records")
 
 
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_images(titles):
    """Look up a photo URL for each Wikipedia article title (runs in parallel).
 
    Uses the public Wikipedia REST summary endpoint. Any failure simply returns
    an empty string so the UI falls back to a placeholder.
    """
 
    def one(title):
        try:
            url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(
                title.replace(" ", "_")
            )
            req = urllib.request.Request(
                url, headers={"User-Agent": "HeritageLensAI/1.0 (educational project)"}
            )
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.load(resp)
            thumb = (data.get("thumbnail") or {}).get("source", "")
            if not thumb:
                return ""
            width = (data.get("originalimage") or {}).get("width", 0)
            if width >= 960:
                return re.sub(r"/\d+px-", "/960px-", thumb)
            if width >= 500:
                return re.sub(r"/\d+px-", "/500px-", thumb)
            return thumb
        except Exception:
            return ""
 
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(one, titles))
    return dict(zip(titles, results))
 
 
def get_image_url(site):
    images = fetch_images(tuple(s["image"] for s in HERITAGE_SITES))
    return images.get(site["image"], "")
 
 
# =============================================================================
# SESSION STATE
# =============================================================================
DEFAULT_STATE = {
    "page": "Home",
    "favorites": [],
    "chat_history": [],
    "quiz_score": 0,
    "quiz_questions": [],
    "quiz_answers": {},
    "quiz_index": 0,
    "quiz_finished": False,
    "quiz_id": 0,
    "best_quiz": None,
    "sites_explored": [],
    "ai_questions": 0,
    "quizzes_completed": 0,
    "selected_site": None,
    "explain_cache": {},
    "recommendations": None,
}
 
# Widget keys whose values should survive navigating to another page.
PERSISTENT_WIDGET_KEYS = [
    "f_search",
    "f_category",
    "f_state",
    "f_period",
    "f_sort",
    "guide_site_sel",
    "quiz_site_sel",
    "quiz_cat_sel",
    "quiz_n_sel",
    "rec_interests",
    "rec_region",
    "rec_period",
]
 
 
def initialize_session_state():
    """Create session variables once; never overwrite them on reruns."""
    for key, value in DEFAULT_STATE.items():
        if key not in st.session_state:
            st.session_state[key] = copy.deepcopy(value)
    for key in PERSISTENT_WIDGET_KEYS:
        if key in st.session_state:
            st.session_state[key] = st.session_state[key]
 
 
# ---- callbacks -------------------------------------------------------------
def navigate(page, **extra):
    st.session_state["page"] = page
    for key, value in extra.items():
        st.session_state[key] = value
 
 
def open_site(site_id):
    st.session_state["selected_site"] = site_id
    st.session_state["page"] = "Explore Heritage"
    st.session_state["_keep_detail"] = True
 
 
def close_detail():
    st.session_state["selected_site"] = None
 
 
def open_quiz_for(site_name):
    """Jump to the quiz page and auto-generate a quiz for one site."""
    st.session_state["quiz_questions"] = []
    st.session_state["quiz_answers"] = {}
    st.session_state["quiz_index"] = 0
    st.session_state["quiz_finished"] = False
    st.session_state["quiz_site_sel"] = site_name
    st.session_state["quiz_n_sel"] = 5
    st.session_state["_auto_quiz"] = True
    st.session_state["page"] = "Heritage Quiz"
 
 
def toggle_favorite(site_id):
    favs = st.session_state["favorites"]
    if site_id in favs:
        favs.remove(site_id)
    else:
        favs.append(site_id)
 
 
def is_favorite(site_id):
    return site_id in st.session_state["favorites"]
 
 
def mark_explored(site_id):
    if site_id not in st.session_state["sites_explored"]:
        st.session_state["sites_explored"].append(site_id)
 
 
# =============================================================================
# GEMINI
# =============================================================================
def get_api_key():
    """Read the key from Streamlit secrets first, then environment / .env."""
    key = None
    try:
        key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        key = None
    if not key:
        key = os.getenv("GEMINI_API_KEY")
    key = (key or "").strip()
    if not key or key.upper().startswith("YOUR_API_KEY"):
        return None
    return key
 
 
def get_model_name():
    name = None
    try:
        name = st.secrets["GEMINI_MODEL"]
    except Exception:
        name = None
    return name or os.getenv("GEMINI_MODEL") or DEFAULT_MODEL
 
 
@st.cache_resource(show_spinner=False)
def _build_client(api_key):
    return genai.Client(api_key=api_key)
 
 
def get_gemini_client():
    key = get_api_key()
    if not key:
        return None
    return _build_client(key)
 
 
def generate_ai_response(prompt, system_instruction=SYSTEM_INSTRUCTION, temperature=0.4, json_mode=False):
    """Send a prompt to Gemini and return clean text, or None on any problem.
 
    Errors are shown to the user with st.error so the app never crashes.
    """
    client = get_gemini_client()
    if client is None:
        st.error(MSG_NO_KEY)
        return None
    try:
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
            response_mime_type="application/json" if json_mode else None,
        )
        response = client.models.generate_content(
            model=get_model_name(), contents=prompt, config=config
        )
        text = (response.text or "").strip()
    except Exception as exc:
        st.error(MSG_AI_DOWN)
        key = get_api_key() or ""
        detail = str(exc).replace(key, "***") if key else str(exc)
        with st.expander("Technical details"):
            st.code(f"{type(exc).__name__}: {detail[:400]}")
        return None
    if not text:
        st.warning("HeritageLens AI returned an empty response. Please try again.")
        return None
    return text
 
 
def extract_json(raw):
    """Parse JSON from a model reply, tolerating code fences and extra text."""
    if not raw:
        return None
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.I)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"(\[.*\]|\{.*\})", text, re.S)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            return None
    return None
 
 
def explain_site_simply(site):
    prompt = (
        "Explain this heritage site in simple language for a student.\n\n"
        "Include:\n"
        "1. What is it?\n"
        "2. Where is it?\n"
        "3. Historical background\n"
        "4. Why is it important?\n"
        "5. Architecture\n"
        "6. Two interesting facts\n\n"
        "Keep the response easy to understand. Use short sentences and the "
        "numbered headings above.\n\n"
        "Use this information from the HeritageLens database:\n"
        f"{site_to_text(site)}"
    )
    return generate_ai_response(prompt, temperature=0.4)
 
 
def build_chat_prompt(question, site, history):
    parts = []
    if site:
        parts.append(
            "The user is studying this site from the HeritageLens database. "
            "Prioritize this information:\n" + site_to_text(site)
        )
    else:
        mentioned = find_mentioned_sites(question)
        if mentioned:
            parts.append(
                "HeritageLens database records for sites mentioned in the question:\n\n"
                + "\n\n".join(site_to_text(s) for s in mentioned[:3])
            )
        index = ", ".join(f"{s['name']} ({s['state']})" for s in HERITAGE_SITES)
        parts.append(f"Sites available in the HeritageLens database: {index}.")
    recent = history[-6:]
    if recent:
        convo = "\n".join(
            f"{'User' if m['role'] == 'user' else 'HeritageLens AI'}: {m['content']}" for m in recent
        )
        parts.append("Conversation so far:\n" + convo)
    parts.append("User question: " + question)
    return "\n\n".join(parts)
 
 
def generate_quiz(site_name, category, num_questions):
    """Ask Gemini for a multiple-choice quiz; return a validated list or None."""
    if site_name != "All sites":
        site = get_site_by_name(site_name)
        sites = [site] if site else []
        scope = site_name
    elif category != "All":
        sites = [s for s in HERITAGE_SITES if s["category"] == category]
        scope = f"the category '{category}'"
    else:
        sites = HERITAGE_SITES
        scope = "Indian heritage sites"
    if not sites:
        st.warning("No heritage sites found for this selection.")
        return None
 
    context = "\n\n".join(site_to_text(s) for s in sites)
    prompt = (
        f"Create a multiple-choice quiz with exactly {num_questions} questions about {scope}.\n"
        "Base every question ONLY on the information below. Mix easy and moderate "
        "questions. Each question must have exactly four options and one correct answer.\n\n"
        "Return ONLY a JSON array (no markdown). Each element must look like:\n"
        '{"question": "...", "options": {"A": "...", "B": "...", "C": "...", "D": "..."}, '
        '"correct": "A", "explanation": "..."}\n\n'
        f"INFORMATION:\n{context}"
    )
    raw = generate_ai_response(prompt, temperature=0.5, json_mode=True)
    if raw is None:
        return None
    questions = validate_quiz(extract_json(raw), num_questions)
    if not questions:
        st.error("The quiz could not be read from the AI response. Please try again.")
        return None
    return questions
 
 
def validate_quiz(data, limit):
    if isinstance(data, dict):
        data = data.get("questions") or data.get("quiz")
    if not isinstance(data, list):
        return None
    cleaned = []
    for item in data:
        try:
            options = item["options"]
            if isinstance(options, list):
                options = dict(zip("ABCD", options))
            options = {str(k).strip().upper()[:1]: str(v).strip() for k, v in options.items()}
            correct = str(item["correct"]).strip().upper()[:1]
            if set(options) != set("ABCD") or correct not in options:
                continue
            cleaned.append(
                {
                    "question": str(item["question"]).strip(),
                    "options": options,
                    "correct": correct,
                    "explanation": str(item.get("explanation", "")).strip(),
                }
            )
        except (KeyError, AttributeError, TypeError):
            continue
    return cleaned[:limit] or None
 
 
def get_recommendations(interests, region, period):
    """Ask Gemini to pick sites from the dataset; return [(site, reason)] or None."""
    catalogue = "\n".join(
        f"- id={s['id']} | {s['name']} | {s['state']} | {s['category']} | {s['period']} | "
        f"{s['description']}"
        for s in HERITAGE_SITES
    )
    prompt = (
        "Recommend between 3 and 5 heritage sites for a learner.\n"
        f"Interests: {', '.join(interests) if interests else 'any'}\n"
        f"Preferred region/state: {region}\n"
        f"Preferred historical period: {period}\n\n"
        "Choose ONLY from the sites listed below and use their exact id values. Rank "
        "the best matches first. If region or period is 'Any', ignore that preference.\n\n"
        'Return ONLY a JSON array (no markdown) of objects like {"id": "...", "reason": '
        '"one or two sentences on why it matches the user\'s interests"}.\n\n'
        f"SITES:\n{catalogue}"
    )
    raw = generate_ai_response(prompt, temperature=0.4, json_mode=True)
    if raw is None:
        return None
    data = extract_json(raw)
    if isinstance(data, dict):
        data = data.get("recommendations")
    results, seen = [], set()
    if isinstance(data, list):
        for item in data:
            try:
                site = get_site(str(item["id"]).strip())
                if site and site["id"] not in seen:
                    seen.add(site["id"])
                    results.append((site, str(item.get("reason", "")).strip()))
            except (KeyError, AttributeError, TypeError):
                continue
    if not results:
        st.error("The recommendations could not be read from the AI response. Please try again.")
        return None
    return results[:5]
 
 
# =============================================================================
# HTML / CSS
# =============================================================================
def h(markup):
    """Collapse HTML so Streamlit's markdown parser never sees indented code."""
    return "".join(line.strip() for line in markup.strip().splitlines())
 
 
def esc(text):
    return html.escape(str(text), quote=True)
 
 
def apply_custom_css():
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');
 
:root {
    --cream: #FBF6EA;
    --ivory: #F4ECD8;
    --brown: #4A2C1A;
    --brown-soft: #6B4630;
    --terracotta: #B5573B;
    --gold: #C9A24B;
    --charcoal: #2B2B2B;
    --line: #E7D9B5;
    --shadow: 0 6px 22px rgba(74, 44, 26, 0.12);
    --shadow-hover: 0 14px 34px rgba(74, 44, 26, 0.20);
}
 
html, body, .stApp, [data-testid="stAppViewContainer"] {
    background: var(--cream);
    color: var(--charcoal);
    font-family: 'Inter', sans-serif;
}
[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] { visibility: hidden; }
.block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1250px; }
 
h1, h2, h3, h4 { font-family: 'Playfair Display', serif; color: var(--brown); letter-spacing: 0.2px; }
p, li, label, span { color: var(--charcoal); }
 
/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #4A2C1A 0%, #3A2112 100%);
    border-right: 3px solid var(--gold);
}
[data-testid="stSidebar"] * { color: #F7EEDB; }
.side-brand { text-align: center; padding: 8px 0 14px; border-bottom: 1px solid rgba(201,162,75,.45); margin-bottom: 14px; }
.side-brand .logo { font-size: 2.2rem; }
.side-brand .name { font-family: 'Playfair Display', serif; font-size: 1.5rem; color: #F7EEDB; font-weight: 700; }
.side-brand .tag { font-size: .8rem; letter-spacing: 2px; color: var(--gold); text-transform: uppercase; }
[data-testid="stSidebar"] [role="radiogroup"] { gap: 4px; }
[data-testid="stSidebar"] [role="radiogroup"] label {
    padding: 9px 14px; border-radius: 10px; width: 100%; cursor: pointer; transition: all .2s ease;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover { background: rgba(201,162,75,.20); transform: translateX(3px); }
[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child { display: none; }
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
    background: linear-gradient(90deg, var(--terracotta), #C86B4C); box-shadow: 0 4px 12px rgba(0,0,0,.25);
}
.side-note { font-size: .78rem; opacity: .85; line-height: 1.5; border-top: 1px solid rgba(201,162,75,.35); padding-top: 10px; margin-top: 18px; }
 
/* ---------- Hero ---------- */
.hero {
    border-radius: 22px; padding: 64px 48px; color: #fff; box-shadow: var(--shadow);
    background: linear-gradient(120deg, rgba(58,33,18,.88), rgba(181,87,59,.55)), linear-gradient(135deg, #4A2C1A, #B5573B);
    background-size: cover; background-position: center; position: relative; overflow: hidden;
}
.hero .eyebrow { letter-spacing: 6px; font-size: .85rem; color: var(--gold); font-weight: 600; margin-bottom: 8px; }
.hero h1 { color: #fff; font-size: 3.4rem; margin: 0 0 4px; line-height: 1.1; }
.hero .subtitle { font-family: 'Playfair Display', serif; font-style: italic; font-size: 1.6rem; color: #F3D9A0; margin-bottom: 14px; }
.hero .lead { font-size: 1.05rem; max-width: 760px; color: #FBF1DD; line-height: 1.65; margin-bottom: 8px; }
.hero .desc { max-width: 760px; color: #F1E3C6; font-size: .95rem; opacity: .95; }
 
/* ---------- Cards & sections ---------- */
.section-title { font-family: 'Playfair Display', serif; font-size: 1.7rem; color: var(--brown); margin: 34px 0 6px; position: relative; padding-bottom: 10px; }
.section-title::after { content: ""; position: absolute; left: 0; bottom: 0; width: 64px; height: 3px; background: var(--gold); border-radius: 4px; }
.section-sub { color: var(--brown-soft); margin-bottom: 16px; }
 
.card, .site-card, .feature-card, .metric-card {
    background: #fff; border: 1px solid var(--line); border-radius: 16px; box-shadow: var(--shadow);
    transition: transform .25s ease, box-shadow .25s ease, border-color .25s ease;
}
.card { padding: 22px 24px; margin-bottom: 16px; }
.card:hover, .feature-card:hover, .metric-card:hover { transform: translateY(-4px); box-shadow: var(--shadow-hover); border-color: var(--gold); }
.card h4 { margin: 0 0 8px; color: var(--terracotta); font-size: 1.15rem; }
.card p, .card li { line-height: 1.7; margin: 0; }
.card ul { margin: 0; padding-left: 20px; }
 
.feature-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 18px; }
.feature-card { padding: 24px 20px; text-align: center; }
.feature-card .icon { font-size: 2.1rem; margin-bottom: 8px; }
.feature-card h4 { margin: 4px 0 6px; font-size: 1.1rem; color: var(--brown); }
.feature-card p { font-size: .92rem; color: #4d4d4d; margin: 0; line-height: 1.55; }
 
.stat-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 18px; margin-top: 8px; }
.metric-card { padding: 20px; text-align: center; background: linear-gradient(180deg, #fff, var(--ivory)); }
.metric-card .num { font-family: 'Playfair Display', serif; font-size: 2.3rem; color: var(--terracotta); font-weight: 700; }
.metric-card .lbl { font-size: .9rem; color: var(--brown-soft); letter-spacing: .5px; }
 
.badge { display: inline-block; padding: 3px 11px; border-radius: 999px; font-size: .74rem; font-weight: 600; letter-spacing: .3px;
         background: rgba(181,87,59,.12); color: var(--terracotta); border: 1px solid rgba(181,87,59,.35); margin: 0 6px 6px 0; }
.badge-alt { background: rgba(201,162,75,.18); color: #7a5c14; border-color: rgba(201,162,75,.6); }
 
/* ---------- Images ---------- */
.img-box { position: relative; width: 100%; overflow: hidden; background: linear-gradient(135deg, #6B4630, #B5573B 60%, #C9A24B); }
.img-box .img-fallback { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font-size: 3rem; opacity: .85; }
.img-box .img-layer { position: absolute; inset: 0; background-size: cover; background-position: center; transition: transform .5s ease; }
[class*="st-key-sitecard"]:hover .img-layer { transform: scale(1.06); }
 
/* ---------- Site card (Streamlit container with key "sitecard_*") ---------- */
[class*="st-key-sitecard"] {
    background: #fff; border: 1px solid var(--line); border-radius: 18px; box-shadow: var(--shadow);
    overflow: hidden; padding: 0 0 14px; gap: 0.4rem; transition: transform .25s ease, box-shadow .25s ease, border-color .25s ease;
}
[class*="st-key-sitecard"]:hover { transform: translateY(-5px); box-shadow: var(--shadow-hover); border-color: var(--gold); }
[class*="st-key-sitecard"] > div { padding-left: 0; padding-right: 0; }
.site-body { padding: 14px 18px 4px; }
.site-body h4 { margin: 4px 0 2px; font-size: 1.2rem; }
.site-meta { color: var(--brown-soft); font-size: .85rem; margin-bottom: 8px; }
.site-desc { font-size: .9rem; line-height: 1.55; color: #3d3d3d; min-height: 4.6em; }
[class*="st-key-sitecard"] [data-testid="stHorizontalBlock"] { padding: 0 14px; }
 
/* ---------- Chat ---------- */
.user-message, .ai-message, [class*="st-key-aimsg"] {
    border-radius: 16px; padding: 14px 18px; margin: 8px 0; line-height: 1.65; box-shadow: 0 3px 10px rgba(74,44,26,.08);
}
.user-message { background: var(--brown); color: #FBF1DD; margin-left: 18%; border-bottom-right-radius: 4px; }
.user-message * { color: #FBF1DD; }
.ai-message, [class*="st-key-aimsg"] { background: #fff; border: 1px solid var(--line); border-left: 4px solid var(--terracotta); margin-right: 8%; border-bottom-left-radius: 4px; }
 
/* ---------- Streamlit widgets ---------- */
.stButton > button, .stDownloadButton > button {
    width: 100%; background: #fff; color: var(--brown); border: 1.5px solid var(--gold); border-radius: 10px;
    font-weight: 600; padding: .5rem .9rem; transition: all .2s ease;
}
.stButton > button:hover { background: var(--terracotta); color: #fff; border-color: var(--terracotta); transform: translateY(-1px); box-shadow: 0 6px 14px rgba(181,87,59,.30); }
.stButton > button:hover p { color: #fff; }
.stButton > button:disabled { opacity: .5; }
.stButton > button[kind="primary"], button[data-testid="stBaseButton-primary"] {
    background: linear-gradient(90deg, var(--terracotta), #C86B4C); color: #fff; border-color: var(--terracotta);
}
.stButton > button[kind="primary"] p, button[data-testid="stBaseButton-primary"] p { color: #fff; }
.stButton > button[kind="primary"]:hover, button[data-testid="stBaseButton-primary"]:hover { background: var(--brown); border-color: var(--brown); }
[data-testid="stSidebar"] .stButton > button { background: transparent; }
 
.stTextInput input, .stTextArea textarea, div[data-baseweb="select"] > div, [data-testid="stChatInput"] textarea {
    background: #fff !important; border: 1.5px solid var(--line) !important; border-radius: 10px !important; color: var(--charcoal) !important;
}
.stTextInput input:focus, .stTextArea textarea:focus { border-color: var(--terracotta) !important; box-shadow: 0 0 0 2px rgba(181,87,59,.18) !important; }
[data-testid="stChatInput"] { border-radius: 14px; }
 
[data-testid="stMetric"] {
    background: #fff; border: 1px solid var(--line); border-radius: 14px; padding: 14px 18px; box-shadow: var(--shadow);
    border-top: 4px solid var(--gold); transition: transform .2s ease;
}
[data-testid="stMetric"]:hover { transform: translateY(-3px); }
[data-testid="stMetricValue"] { font-family: 'Playfair Display', serif; color: var(--terracotta); }
[data-testid="stMetricLabel"] p { color: var(--brown-soft); font-weight: 600; }
 
button[data-baseweb="tab"] { font-weight: 600; color: var(--brown-soft); }
button[data-baseweb="tab"][aria-selected="true"] { color: var(--terracotta); }
div[data-baseweb="tab-highlight"] { background-color: var(--terracotta) !important; }
 
[data-testid="stExpander"] { background: #fff; border: 1px solid var(--line); border-radius: 12px; box-shadow: 0 3px 10px rgba(74,44,26,.06); }
[data-testid="stExpander"] summary:hover { color: var(--terracotta); }
 
[data-testid="stProgress"] > div > div > div > div { background-color: var(--terracotta); }
[data-testid="stAlert"] { border-radius: 12px; }
 
.score-card { text-align: center; padding: 30px; border-radius: 20px; color: #fff; box-shadow: var(--shadow);
              background: linear-gradient(135deg, var(--brown), var(--terracotta)); margin: 10px 0 18px; }
.score-card .title { letter-spacing: 3px; text-transform: uppercase; font-size: .85rem; color: #F3D9A0; }
.score-card .score { font-family: 'Playfair Display', serif; font-size: 3.6rem; font-weight: 700; color: #fff; }
 
.notice { background: #FFF8E4; border: 1px solid var(--gold); border-left: 5px solid var(--gold); border-radius: 12px; padding: 14px 18px; font-size: .9rem; line-height: 1.6; }
.notice b { color: var(--brown); }
.footer { text-align: center; color: var(--brown-soft); font-size: .8rem; margin-top: 46px; padding-top: 16px; border-top: 1px solid var(--line); line-height: 1.7; }
 
/* ---------- Responsive ---------- */
@media (max-width: 1000px) {
    .feature-grid, .stat-grid { grid-template-columns: repeat(2, 1fr); }
    .hero { padding: 44px 28px; }
    .hero h1 { font-size: 2.6rem; }
}
@media (max-width: 640px) {
    .feature-grid, .stat-grid { grid-template-columns: 1fr; }
    .hero { padding: 32px 20px; border-radius: 16px; }
    .hero h1 { font-size: 2.1rem; }
    .hero .subtitle { font-size: 1.25rem; }
    .section-title { font-size: 1.4rem; }
    .user-message { margin-left: 4%; }
    .ai-message, [class*="st-key-aimsg"] { margin-right: 2%; }
    .score-card .score { font-size: 2.8rem; }
}
</style>
        """,
        unsafe_allow_html=True,
    )
 
 
def section_title(text, sub=None):
    st.markdown(f'<div class="section-title">{esc(text)}</div>', unsafe_allow_html=True)
    if sub:
        st.markdown(f'<div class="section-sub">{esc(sub)}</div>', unsafe_allow_html=True)
 
 
def image_block(url, icon, height):
    layer = ""
    if url:
        layer = f'<div class="img-layer" style="background-image:url(\'{esc(url)}\')"></div>'
    return (
        f'<div class="img-box" style="height:{height}px">'
        f'<div class="img-fallback">{icon}</div>{layer}</div>'
    )
 
 
def render_footer():
    st.markdown(
        h(
            """
<div class="footer">
HeritageLens AI &middot; Explore. Understand. Preserve.<br>
Educational project &middot; AI-generated content may contain errors &middot; Photos via Wikipedia / Wikimedia Commons
</div>
"""
        ),
        unsafe_allow_html=True,
    )
 
 
def render_ai_notice():
    st.markdown(
        f'<div class="notice"><b>AI Information Notice</b><br>{esc(AI_NOTICE)}</div>',
        unsafe_allow_html=True,
    )
 
 
# =============================================================================
# SHARED COMPONENTS
# =============================================================================
def render_site_card(site, ctx):
    """A site card: image, text, and View Details / Favorite buttons."""
    icon = CATEGORY_ICONS.get(site["category"], "🏛️")
    with st.container(key=f"sitecard_{ctx}_{site['id']}"):
        st.markdown(
            h(
                f"""
{image_block(get_image_url(site), icon, 190)}
<div class="site-body">
<span class="badge">{esc(site['category'])}</span><span class="badge badge-alt">{esc(site['period'])}</span>
<h4>{esc(site['name'])}</h4>
<div class="site-meta">📍 {esc(site['location'])}, {esc(site['state'])}</div>
<div class="site-desc">{esc(site['description'])}</div>
</div>
"""
            ),
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns(2)
        c1.button(
            "View Details",
            key=f"view_{ctx}_{site['id']}",
            on_click=open_site,
            args=(site["id"],),
        )
        c2.button(
            "♥ Remove from Favorites" if is_favorite(site["id"]) else "♡ Add to Favorites",
            key=f"fav_{ctx}_{site['id']}",
            on_click=toggle_favorite,
            args=(site["id"],),
        )
 
 
def render_site_grid(sites, ctx, columns=3):
    for start in range(0, len(sites), columns):
        cols = st.columns(columns, gap="large")
        for col, site in zip(cols, sites[start : start + columns]):
            with col:
                render_site_card(site, ctx)
 
 
def render_dashboard():
    section_title("Your Learning Dashboard", "Statistics for your current session.")
    best = st.session_state["best_quiz"]
    cols = st.columns(5)
    cols[0].metric("Heritage Sites Explored", len(st.session_state["sites_explored"]))
    cols[1].metric("AI Questions Asked", st.session_state["ai_questions"])
    cols[2].metric("Quizzes Completed", st.session_state["quizzes_completed"])
    cols[3].metric("Best Quiz Score", f"{best['score']}/{best['total']}" if best else "-")
    cols[4].metric("Favorite Sites", len(st.session_state["favorites"]))
 
 
# =============================================================================
# PAGES
# =============================================================================
def render_home():
    hero_img = ""
    for site in HERITAGE_SITES:
        if site["id"] == "golconda-fort":
            hero_img = get_image_url(site)
    hero_style = ""
    if hero_img:
        hero_style = (
            "background-image: linear-gradient(120deg, rgba(58,33,18,.88), rgba(181,87,59,.50)), "
            f"url('{esc(hero_img)}'), linear-gradient(135deg, #4A2C1A, #B5573B);"
        )
    st.markdown(
        h(
            f"""
<div class="hero" style="{hero_style}">
<div class="eyebrow">🏛️ HERITAGELENS AI</div>
<h1>HeritageLens AI</h1>
<div class="subtitle">Explore. Understand. Preserve.</div>
<div class="lead">Discover India's historical places, architectural wonders and cultural heritage with the power of artificial intelligence.</div>
<div class="desc">An Intelligent Platform for Exploring, Understanding, and Learning About Historical and Cultural Heritage Using Artificial Intelligence.</div>
</div>
"""
        ),
        unsafe_allow_html=True,
    )
    st.write("")
    b1, b2, _ = st.columns([1, 1, 2])
    b1.button(
        "Explore Heritage",
        type="primary",
        key="hero_explore",
        on_click=navigate,
        args=("Explore Heritage",),
    )
    b2.button(
        "Ask HeritageLens AI",
        key="hero_ask",
        on_click=navigate,
        args=("AI Heritage Guide",),
    )
 
    section_title("Why HeritageLens AI?", "Four ways to experience heritage, all connected in one place.")
    st.markdown(
        h(
            """
<div class="feature-grid">
<div class="feature-card"><div class="icon">🧭</div><h4>Explore Heritage</h4><p>Search and filter forts, temples, caves, palaces and monuments across India.</p></div>
<div class="feature-card"><div class="icon">🤖</div><h4>Ask AI</h4><p>Chat with a Gemini-powered guide that answers using verified site information.</p></div>
<div class="feature-card"><div class="icon">🧒</div><h4>Learn Simply</h4><p>Turn complex history into short, student-friendly explanations in one click.</p></div>
<div class="feature-card"><div class="icon">🧠</div><h4>Test Your Knowledge</h4><p>Generate AI quizzes, track your score and review every explanation.</p></div>
</div>
"""
        ),
        unsafe_allow_html=True,
    )
 
    section_title("HeritageLens at a Glance")
    st.markdown(
        h(
            """
<div class="stat-grid">
<div class="metric-card"><div class="num">15+</div><div class="lbl">Heritage Sites</div></div>
<div class="metric-card"><div class="num">8+</div><div class="lbl">Heritage Categories</div></div>
<div class="metric-card"><div class="num">5+</div><div class="lbl">Historical Periods</div></div>
<div class="metric-card"><div class="num">4+</div><div class="lbl">AI Learning Tools</div></div>
</div>
"""
        ),
        unsafe_allow_html=True,
    )
    st.caption("Application demo statistics for this project, not official UNESCO or government figures.")
 
    render_dashboard()
 
    section_title("Featured Heritage Sites", "A few places to start your journey.")
    featured = [get_site(i) for i in ("golconda-fort", "taj-mahal", "hampi")]
    render_site_grid(featured, "home")
    render_footer()
 
 
def render_explore():
    if st.session_state["selected_site"]:
        render_site_details(get_site(st.session_state["selected_site"]))
        return
 
    st.markdown("## 🧭 Explore Heritage")
    st.markdown("Search and filter heritage sites, then open one to learn more.")
 
    states = ["All"] + sorted({s["state"] for s in HERITAGE_SITES})
    categories = ["All"] + [c for c in CATEGORIES if any(s["category"] == c for s in HERITAGE_SITES)]
    periods = ["All"] + [p for p in PERIODS if any(s["period"] == p for s in HERITAGE_SITES)]
 
    query = st.text_input(
        "Search",
        key="f_search",
        placeholder="Try: Hyderabad, Fort, Kakatiya, Buddhist...",
    )
    c1, c2, c3, c4 = st.columns(4)
    category = c1.selectbox("Category", categories, key="f_category")
    state = c2.selectbox("Region / State", states, key="f_state")
    period = c3.selectbox("Historical Period", periods, key="f_period")
    sort = c4.selectbox("Sort by", SORT_OPTIONS, key="f_sort")
 
    results = search_heritage(query, category, state, period, sort)
    if not results:
        st.info("No heritage sites match your search.")
    else:
        st.markdown(f"**{len(results)} heritage sites found**")
        render_site_grid(results, "explore")
    render_footer()
 
 
def render_site_details(site):
    if site is None:
        close_detail()
        st.rerun()
        return
    mark_explored(site["id"])
    icon = CATEGORY_ICONS.get(site["category"], "🏛️")
 
    st.button("← Back to results", key="back_to_results", on_click=close_detail)
 
    st.markdown(
        h(
            f"""
<div class="card" style="padding:0;overflow:hidden;margin-top:12px;">
{image_block(get_image_url(site), icon, 380)}
<div style="padding:22px 26px 14px;">
<span class="badge">{esc(site['category'])}</span><span class="badge badge-alt">{esc(site['period'])}</span>
<h2 style="margin:6px 0 4px;">{esc(site['name'])}</h2>
<div class="site-meta">📍 {esc(site['location'])} &nbsp;|&nbsp; State: <b>{esc(site['state'])}</b> &nbsp;|&nbsp; Category: <b>{esc(site['category'])}</b> &nbsp;|&nbsp; Period: <b>{esc(site['period'])}</b></div>
</div>
</div>
"""
        ),
        unsafe_allow_html=True,
    )
 
    b1, b2, b3, b4 = st.columns(4)
    b1.button(
        "Ask AI About This Site",
        type="primary",
        key="det_ask",
        on_click=navigate,
        args=("AI Heritage Guide",),
        kwargs={"guide_site_sel": site["name"]},
    )
    explain_clicked = b2.button("Explain Simply", key="det_explain")
    b3.button(
        "Generate Quiz",
        key="det_quiz",
        on_click=open_quiz_for,
        args=(site["name"],),
    )
    b4.button(
        "♥ Remove from Favorites" if is_favorite(site["id"]) else "♡ Add to Favorites",
        key="det_fav",
        on_click=toggle_favorite,
        args=(site["id"],),
    )
 
    if explain_clicked:
        with st.spinner("Simplifying with Gemini..."):
            text = explain_site_simply(site)
        if text:
            st.session_state["explain_cache"][site["id"]] = text
 
    cached = st.session_state["explain_cache"].get(site["id"])
    if cached:
        st.markdown('<div class="section-title">Explained Simply</div>', unsafe_allow_html=True)
        with st.container(key=f"aimsg_explain_{site['id']}"):
            st.markdown(cached)
 
    def card(title, body):
        st.markdown(
            f'<div class="card"><h4>{esc(title)}</h4><p>{esc(body)}</p></div>',
            unsafe_allow_html=True,
        )
 
    left, right = st.columns(2, gap="large")
    with left:
        card("Overview", site["description"])
        card("Historical Background", site["history"])
        card("Architecture", site["architecture"])
    with right:
        card("Cultural Significance", site["significance"])
        facts_html = "".join(f"<li>{esc(f)}</li>" for f in site["facts"])
        st.markdown(
            f'<div class="card"><h4>Interesting Facts</h4><ul>{facts_html}</ul></div>',
            unsafe_allow_html=True,
        )
        card("Why It Matters", site["why_it_matters"])
 
    render_footer()
 
 
def ask_guide(question, site):
    """Send one question to Gemini and store both messages in chat history."""
    history = st.session_state["chat_history"]
    prompt = build_chat_prompt(question, site, history)
    with st.spinner("HeritageLens AI is thinking..."):
        answer = generate_ai_response(prompt, temperature=0.4)
    if answer:
        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": answer})
        st.session_state["ai_questions"] += 1
        if site:
            mark_explored(site["id"])
 
 
def render_ai_guide():
    st.markdown("## 🤖 Ask HeritageLens AI")
    st.markdown("Your intelligent guide to historical and cultural heritage.")
 
    options = ["All heritage sites"] + [s["name"] for s in HERITAGE_SITES]
    choice = st.selectbox("Topic", options, key="guide_site_sel")
    site = get_site_by_name(choice)
 
    st.caption("Suggested questions")
    target = site["name"] if site else "this heritage site"
    suggestions = [
        ("Tell me the history", f"Tell me the history of {target}."),
        ("Explain the architecture", f"Explain the architecture of {target}."),
        ("Why is it important?", f"Why is {target} important?"),
        ("Give me 5 interesting facts", f"Give me 5 interesting facts about {target}."),
        ("Explain it simply", f"Explain {target} simply, for a school student."),
    ]
    cols = st.columns(len(suggestions))
    clicked = None
    for i, (col, (label, full_question)) in enumerate(zip(cols, suggestions)):
        if col.button(label, key=f"sugg_{i}"):
            if site:
                clicked = full_question
            else:
                st.info("Choose a heritage site in the Topic box above, then use the suggested questions.")
 
    typed = st.chat_input("Ask about a monument, its history, architecture or significance...")
    question = typed if typed is not None else clicked
    if question is not None:
        if not question.strip():
            st.warning("Please enter a question.")
        else:
            ask_guide(question.strip(), site)
 
    if st.session_state["chat_history"]:
        for i, msg in enumerate(st.session_state["chat_history"]):
            if msg["role"] == "user":
                st.markdown(
                    f'<div class="user-message">{esc(msg["content"])}</div>',
                    unsafe_allow_html=True,
                )
            else:
                with st.container(key=f"aimsg_{i}"):
                    st.markdown(msg["content"])
        st.button(
            "Clear conversation",
            key="clear_chat",
            on_click=lambda: st.session_state.update(chat_history=[]),
        )
    else:
        st.info(
            "Pick a topic above and ask a question, for example "
            "'Why is Golconda Fort important?' or 'Explain the architecture of Charminar.'"
        )
    st.write("")
    render_ai_notice()
    render_footer()
 
 
# ---- quiz ------------------------------------------------------------------
def start_quiz(site_name, category, count):
    with st.spinner("Gemini is writing your quiz..."):
        questions = generate_quiz(site_name, category, count)
    if questions:
        st.session_state["quiz_questions"] = questions
        st.session_state["quiz_answers"] = {}
        st.session_state["quiz_index"] = 0
        st.session_state["quiz_finished"] = False
        st.session_state["quiz_score"] = 0
        st.session_state["quiz_id"] += 1
        if site_name != "All sites":
            site = get_site_by_name(site_name)
            if site:
                mark_explored(site["id"])
        st.session_state["_quiz_recorded"] = False
 
 
def next_question():
    quiz_id = st.session_state["quiz_id"]
    index = st.session_state["quiz_index"]
    selected = st.session_state.get(f"quiz_radio_{quiz_id}_{index}")
    if selected is None:
        return
    st.session_state["quiz_answers"][index] = selected[0]
    questions = st.session_state["quiz_questions"]
    if index + 1 < len(questions):
        st.session_state["quiz_index"] = index + 1
    else:
        score = sum(
            1 for i, q in enumerate(questions) if st.session_state["quiz_answers"].get(i) == q["correct"]
        )
        st.session_state["quiz_score"] = score
        st.session_state["quiz_finished"] = True
        if not st.session_state.get("_quiz_recorded"):
            st.session_state["quizzes_completed"] += 1
            best = st.session_state["best_quiz"]
            if best is None or score / len(questions) > best["score"] / best["total"]:
                st.session_state["best_quiz"] = {"score": score, "total": len(questions)}
            st.session_state["_quiz_recorded"] = True
 
 
def reset_quiz():
    st.session_state["quiz_questions"] = []
    st.session_state["quiz_answers"] = {}
    st.session_state["quiz_index"] = 0
    st.session_state["quiz_finished"] = False
    st.session_state["quiz_score"] = 0
 
 
def render_quiz():
    st.markdown("## 🧠 Heritage Quiz")
    st.markdown("Test what you have learned with an AI-generated multiple-choice quiz.")
 
    questions = st.session_state["quiz_questions"]
 
    # ----- setup -----
    if not questions:
        site_options = ["All sites"] + [s["name"] for s in HERITAGE_SITES]
        category_options = ["All"] + CATEGORIES
        c1, c2, c3 = st.columns(3)
        site_name = c1.selectbox("Heritage site", site_options, key="quiz_site_sel")
        category = c2.selectbox(
            "Category",
            category_options,
            key="quiz_cat_sel",
            disabled=site_name != "All sites",
            help="Only used when 'All sites' is selected.",
        )
        count = c3.selectbox("Number of questions", [5, 10], key="quiz_n_sel")
 
        auto = st.session_state.pop("_auto_quiz", False)
        if st.button("Generate Quiz", type="primary", key="quiz_generate") or auto:
            start_quiz(site_name, category, count)
            if st.session_state["quiz_questions"]:
                st.rerun()
        st.write("")
        render_ai_notice()
        render_footer()
        return
 
    total = len(questions)
 
    # ----- results -----
    if st.session_state["quiz_finished"]:
        score = st.session_state["quiz_score"]
        accuracy = round(100 * score / total)
        st.markdown(
            h(
                f"""
<div class="score-card">
<div class="title">Heritage Knowledge Score</div>
<div class="score">{score} / {total}</div>
</div>
"""
            ),
            unsafe_allow_html=True,
        )
        m1, m2, m3 = st.columns(3)
        m1.metric("Correct answers", score)
        m2.metric("Wrong answers", total - score)
        m3.metric("Accuracy", f"{accuracy}%")
 
        section_title("Review")
        for i, q in enumerate(questions):
            given = st.session_state["quiz_answers"].get(i)
            ok = given == q["correct"]
            with st.expander(f"{'✅' if ok else '❌'} Q{i + 1}. {q['question']}"):
                st.markdown(f"**Your answer:** {given}. {q['options'].get(given, '-')}")
                st.markdown(f"**Correct answer:** {q['correct']}. {q['options'][q['correct']]}")
                if q["explanation"]:
                    st.markdown(f"**Why:** {q['explanation']}")
        r1, r2 = st.columns(2)
        r1.button("Try Again", type="primary", key="quiz_again", on_click=reset_quiz)
        r2.button(
            "Get Recommendations",
            key="quiz_to_rec",
            on_click=navigate,
            args=("Recommendations",),
        )
        render_footer()
        return
 
    # ----- question -----
    index = st.session_state["quiz_index"]
    q = questions[index]
    st.progress((index) / total, text=f"Question {index + 1} of {total}")
    st.markdown(f'<div class="card"><h4>Question {index + 1}</h4><p>{esc(q["question"])}</p></div>', unsafe_allow_html=True)
    radio_key = f"quiz_radio_{st.session_state['quiz_id']}_{index}"
    choice = st.radio(
        "Choose one answer",
        [f"{letter}. {q['options'][letter]}" for letter in "ABCD"],
        index=None,
        key=radio_key,
    )
    is_last = index + 1 == total
    st.button(
        "Finish Quiz" if is_last else "Next Question",
        type="primary",
        key=f"quiz_next_{index}",
        disabled=choice is None,
        on_click=next_question,
    )
    st.button("Cancel quiz", key="quiz_cancel", on_click=reset_quiz)
    render_footer()
 
 
def render_recommendations():
    st.markdown("## ✨ Recommendations")
    st.markdown("Tell us what you enjoy and Gemini will suggest sites from the HeritageLens collection.")
 
    interests = st.multiselect(
        "Which type of heritage interests you?",
        INTEREST_OPTIONS,
        key="rec_interests",
    )
    c1, c2 = st.columns(2)
    regions = ["Any"] + sorted({s["state"] for s in HERITAGE_SITES})
    periods = ["Any"] + [p for p in PERIODS if any(s["period"] == p for s in HERITAGE_SITES)]
    region = c1.selectbox("Preferred region?", regions, key="rec_region")
    period = c2.selectbox("Preferred historical period?", periods, key="rec_period")
 
    if st.button("Get AI Recommendations", type="primary", key="rec_go"):
        if not interests:
            st.warning("Please choose at least one interest.")
        else:
            with st.spinner("Finding your best matches..."):
                st.session_state["recommendations"] = get_recommendations(interests, region, period)
 
    recs = st.session_state["recommendations"]
    if recs:
        section_title("Recommended for You")
        for site, reason in recs:
            with st.container(key=f"sitecard_rec_{site['id']}"):
                st.markdown(
                    h(
                        f"""
<div class="site-body" style="padding-top:18px;">
<h4>{esc(site['name'])}</h4>
<span class="badge">{esc(site['category'])}</span><span class="badge badge-alt">{esc(site['period'])}</span>
<div class="site-meta">📍 {esc(site['location'])}, {esc(site['state'])}</div>
<div class="site-desc" style="min-height:0;"><b>Why it matches:</b> {esc(reason)}</div>
</div>
"""
                    ),
                    unsafe_allow_html=True,
                )
                b1, b2 = st.columns(2)
                b1.button("View Details", key=f"view_rec_{site['id']}", on_click=open_site, args=(site["id"],))
                b2.button(
                    "♥ Remove from Favorites" if is_favorite(site["id"]) else "♡ Add to Favorites",
                    key=f"fav_rec_{site['id']}",
                    on_click=toggle_favorite,
                    args=(site["id"],),
                )
    render_ai_notice()
    render_footer()
 
 
def render_favorites():
    st.markdown("## ♥ Favorites")
    favs = [get_site(i) for i in st.session_state["favorites"] if get_site(i)]
    if not favs:
        st.info("No heritage sites added to favorites yet.")
        st.button(
            "Explore Heritage",
            type="primary",
            key="fav_explore",
            on_click=navigate,
            args=("Explore Heritage",),
        )
    else:
        st.markdown(f"**{len(favs)} saved heritage sites**")
        render_site_grid(favs, "fav")
    render_footer()
 
 
def render_about():
    st.markdown("## ℹ️ About HeritageLens AI")
    st.markdown(
        '<div class="card"><p>HeritageLens AI is an educational artificial intelligence platform '
        "designed to make historical and cultural heritage easier to explore, understand and learn.</p></div>",
        unsafe_allow_html=True,
    )
    section_title("Goals")
    goals = [
        "Make heritage education interactive",
        "Simplify historical information",
        "Encourage cultural awareness",
        "Support students",
        "Make learning engaging",
        "Demonstrate the use of AI in heritage education",
    ]
    st.markdown(
        '<div class="card"><ul>' + "".join(f"<li>{esc(g)}</li>" for g in goals) + "</ul></div>",
        unsafe_allow_html=True,
    )
 
    section_title("How It Works")
    t1, t2, t3 = st.tabs(["Heritage data", "AI guide", "Technology"])
    with t1:
        st.write(
            "Each site in the collection has a curated record: overview, history, "
            "architecture, significance and facts. Search and filters run on this data."
        )
    with t2:
        st.write(
            "When you ask a question, the app sends Gemini the site record together "
            "with a system instruction that tells it not to invent facts and to say "
            "when something is uncertain. Quizzes and recommendations use the same "
            "records as their source."
        )
    with t3:
        st.write("Python, Streamlit, Google Gemini API (google-genai), pandas, python-dotenv, and HTML/CSS embedded in the app.")
 
    section_title("Responsible AI")
    render_ai_notice()
    render_footer()
 
 
# =============================================================================
# MAIN
# =============================================================================
def render_sidebar():
    with st.sidebar:
        st.markdown(
            h(
                """
<div class="side-brand">
<div class="logo">🏛️</div>
<div class="name">HeritageLens AI</div>
<div class="tag">Explore &middot; Understand &middot; Preserve</div>
</div>
"""
            ),
            unsafe_allow_html=True,
        )
        st.radio(
            "Navigation",
            PAGES,
            key="page",
            format_func=lambda p: f"{PAGE_ICONS[p]}  {p}",
            label_visibility="collapsed",
        )
        status = "Gemini connected ✓" if get_api_key() else "Gemini key not configured"
        st.markdown(
            f'<div class="side-note">{status}<br>AI answers are educational and may contain errors. '
            "Please verify important facts.</div>",
            unsafe_allow_html=True,
        )
 
 
def main():
    initialize_session_state()
    apply_custom_css()
 
    keep_detail = st.session_state.pop("_keep_detail", False)
    render_sidebar()
    page = st.session_state["page"]
 
    previous = st.session_state.get("_prev_page")
    if previous is not None and previous != page and page == "Explore Heritage" and not keep_detail:
        st.session_state["selected_site"] = None
    st.session_state["_prev_page"] = page
 
    if page == "Home":
        render_home()
    elif page == "Explore Heritage":
        render_explore()
    elif page == "AI Heritage Guide":
        render_ai_guide()
    elif page == "Heritage Quiz":
        render_quiz()
    elif page == "Recommendations":
        render_recommendations()
    elif page == "Favorites":
        render_favorites()
    else:
        render_about()
 
 
main()
 
