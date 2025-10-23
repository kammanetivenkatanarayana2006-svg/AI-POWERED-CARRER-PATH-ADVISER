from flask import Flask, request, jsonify, send_file
import google.generativeai as genai
import requests

app = Flask(__name__)

# 🔑 API Keys
genai.configure(api_key="AIzaSyAfSKFkki7qfSbvCUTyb_8b1e0pCpGl5b8")
YOUTUBE_API_KEY = "AIzaSyCToJ5AeKMvmyT8ScMPE4d6xFLEcpylbs4"


@app.route('/')
def home():
    return send_file("index.html")


@app.route('/get_career_paths', methods=['POST'])
def get_career_paths():
    data = request.get_json()
    subjects = data.get('subjects', '')
    coding = data.get('coding', '')
    communication = data.get('communication', '')
    skills = data.get('skills', [])
    goal = data.get('goal', '').strip()

    try:
        model = genai.GenerativeModel("models/gemini-2.5-flash")

        # --- Case 1: No goal entered (show 5 cards) ---
        if goal == "":
            prompt = f"""
You are a professional AI career advisor.

User Info:
- Favourite Subjects: {subjects}
- Coding Experience: {coding}
- Communication Skills: {communication}
- Skills: {skills}

Suggest 5 most suitable career paths with:
1️⃣ Career Name
2️⃣ Reason (why suitable)
3️⃣ Future growth/salary in India.

Each career should be inside HTML cards like:
<div style='background:#000;color:white;padding:15px;margin:10px;border-radius:15px;border:1px solid cyan;box-shadow:0 0 10px cyan;'>
  <h2 style='color:#00ffff;'>💼 Career Name</h2>
  <p>Reason text...</p>
  <p>📈 Growth Info...</p>
  <button style='background:linear-gradient(135deg,#00ffff,#0099ff);color:black;border:none;padding:8px 15px;border-radius:8px;cursor:pointer;font-weight:bold;margin-top:8px;' onclick="getCareerPlan('Career Name')">View Career Plan</button>
</div>
"""
            response = model.generate_content(prompt)
            html_output = f"<div style='background:black;padding:20px;border-radius:10px;color:white;'>{response.text}</div>"

        # --- Case 2: Goal entered (show detailed plan) ---
        else:
            prompt = f"""
You are a professional career planner.

User's Goal: {goal}
User Details:
- Subjects: {subjects}
- Coding: {coding}
- Communication: {communication}
- Skills: {skills}

Create a detailed career roadmap with:
1. Step-by-step plan (with timeline)
2. Skills to learn
3. Projects/internships
4. Job preparation
5. Salary growth in INR
6. Use attractive <div> and <br> for formatting.
"""
            response = model.generate_content(prompt)
            html_output = f"<div style='background:white;color:black;border-radius:15px;padding:25px;'>{response.text}</div>"

        return jsonify({"response": html_output})

    except Exception as e:
        return jsonify({"response": f"Error: {str(e)}"})


def fetch_youtube_videos(query, max_results=5):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": f"{query} tutorial OR course OR for beginners",
        "key": YOUTUBE_API_KEY,
        "maxResults": max_results,
        "type": "video",
        "safeSearch": "strict"
    }
    response = requests.get(url, params=params).json()
    videos = []
    for idx, item in enumerate(response.get("items", []), start=1):
        title = item["snippet"]["title"]
        channel = item["snippet"]["channelTitle"]
        link = f"https://www.youtube.com/watch?v={item['id']['videoId']}"
        thumbnail = item["snippet"]["thumbnails"]["medium"]["url"]
        videos.append(f"""
        <div style='margin:10px;background:white;color:black;padding:10px;border-radius:10px;'>
        <img src='{thumbnail}' width='450' style='border-radius:8px;'><br>
        <b style='color:#007bff;'>{idx}. {title}</b><br>
        🎓 {channel}<br>
        <a href='{link}' target='_blank' style='color:#ff6600;'>Watch</a>
        </div>
        """)
    return "<br>".join(videos) if videos else "No videos found."


@app.route('/get_resources', methods=['POST'])
def get_resources():
    data = request.get_json()
    category = data.get('category', '')
    goal = data.get('goal', '')

    try:
        if category == "YouTube Videos":
            result_html = fetch_youtube_videos(goal)
        else:
            prompt = f"""
Suggest top 4 {category} for learning "{goal}".
Include best & free options.
Format with:
<b>Title</b> — short description<br>
<a href='URL' target='_blank'>Access Here</a>
"""
            model = genai.GenerativeModel("models/gemini-2.5-flash")
            response = model.generate_content(prompt)
            result_html = response.text.replace("\n", "<br>")
        return jsonify({"response": f"<div style='padding:20px;'>{result_html}</div>"})
    except Exception as e:
        return jsonify({"response": f"Error fetching resources: {str(e)}"})


if __name__ == '__main__':
    app.run(debug=True)
