import os
import json
from flask import Flask, request, jsonify
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import tool
from langchain.agents import create_agent

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set.")

bike_database = [{'name': 'Royal Enfield Himalayan 450', 'category': 'Adventure', 'price_lakh': 2.85, 'price': '₹2.85 lakh', 'engine': '452cc', 'power': '40 PS', 'mileage': '30 km/l approx', 'weight': '196 kg', 'best_for': 'Adventure riding, touring and off-road'}, {'name': 'KTM 390 Adventure', 'category': 'Adventure', 'price_lakh': 3.4, 'price': '₹3.40 lakh', 'engine': '399cc', 'power': '46 PS', 'mileage': '30 km/l approx', 'weight': '176 kg approx', 'best_for': 'Adventure riding, touring and performance'}, {'name': 'Yezdi Adventure', 'category': 'Adventure', 'price_lakh': 2.2, 'price': '₹2.20 lakh', 'engine': '334cc', 'power': '30 PS', 'mileage': '30 km/l approx', 'weight': '187 kg approx', 'best_for': 'Adventure riding and touring'}, {'name': 'KTM RC 390', 'category': 'Sports', 'price_lakh': 3.2, 'price': '₹3.20 lakh', 'engine': '373cc', 'power': '43.5 PS', 'mileage': '25 km/l approx', 'weight': '172 kg', 'best_for': 'Sports riding and track-oriented riding'}, {'name': 'Yamaha R15 V4', 'category': 'Sports', 'price_lakh': 1.85, 'price': '₹1.85 lakh', 'engine': '155cc', 'power': '18.4 PS', 'mileage': '45 km/l approx', 'weight': '141 kg', 'best_for': 'Sports riding and daily use'}, {'name': 'TVS Apache RR 310', 'category': 'Sports', 'price_lakh': 2.8, 'price': '₹2.80 lakh', 'engine': '312cc', 'power': '38 PS', 'mileage': '30 km/l approx', 'weight': '174 kg', 'best_for': 'Sports riding and touring'}, {'name': 'Royal Enfield Classic 350', 'category': 'Cruiser', 'price_lakh': 2.0, 'price': '₹2.00 lakh', 'engine': '349cc', 'power': '20.2 PS', 'mileage': '35 km/l approx', 'weight': '195 kg', 'best_for': 'Daily riding and relaxed touring'}, {'name': 'Bajaj Pulsar NS200', 'category': 'Naked', 'price_lakh': 1.6, 'price': '₹1.60 lakh', 'engine': '199cc', 'power': '24.5 PS', 'mileage': '35 km/l approx', 'weight': '158 kg', 'best_for': 'Daily use and sporty riding'}, {'name': 'TVS Apache RTR 200 4V', 'category': 'Naked', 'price_lakh': 1.55, 'price': '₹1.55 lakh', 'engine': '197cc', 'power': '20.8 PS', 'mileage': '40 km/l approx', 'weight': '152 kg', 'best_for': 'Daily commuting and sporty riding'}, {'name': 'Honda SP 125', 'category': 'Commuter', 'price_lakh': 0.95, 'price': '₹0.95 lakh', 'engine': '124cc', 'power': '10.9 PS', 'mileage': '60 km/l approx', 'weight': '116 kg', 'best_for': 'Daily commuting and fuel economy'}, {'name': 'Hero Splendor Plus', 'category': 'Commuter', 'price_lakh': 0.8, 'price': '₹0.80 lakh', 'engine': '97cc', 'power': '8.0 PS', 'mileage': '60 km/l approx', 'weight': '112 kg', 'best_for': 'Daily commuting and economy'}, {'name': 'Bajaj Dominar 400', 'category': 'Touring', 'price_lakh': 2.4, 'price': '₹2.40 lakh', 'engine': '373cc', 'power': '40 PS', 'mileage': '30 km/l approx', 'weight': '193 kg', 'best_for': 'Long-distance touring'}]

@tool
def search_bikes(query: str):
    """Search bikes by name, category, riding style or requirement."""
    q = query.lower()
    results = []
    for bike in bike_database:
        text = (bike["name"] + " " + bike["category"] + " " + bike["best_for"] + " " + bike["engine"]).lower()
        if any(word in text for word in q.split() if len(word) > 2):
            if bike not in results:
                results.append(bike)
    return json.dumps(results, indent=2) if results else "No matching bikes found."

@tool
def filter_by_budget(max_budget_lakh: float):
    """Find bikes within the specified budget in Indian lakh."""
    results = [b for b in bike_database if b["price_lakh"] <= max_budget_lakh]
    return json.dumps(results, indent=2) if results else "No bikes found within this budget."

@tool
def filter_by_category(category: str):
    """Find bikes in a requested category."""
    q = category.lower()
    results = [b for b in bike_database if q in b["category"].lower()]
    return json.dumps(results, indent=2) if results else "No bikes found in this category."

@tool
def compare_bikes(bike_names: str):
    """Compare two or more bikes. Give names separated by commas."""
    names = [x.strip().lower() for x in bike_names.split(",")]
    results = []
    for bike in bike_database:
        name = bike["name"].lower()
        if any(x in name or name in x for x in names):
            results.append(bike)
    return json.dumps(results, indent=2) if results else "The requested bikes were not found."

@tool
def recommend_bike(category: str, max_budget_lakh: float, purpose: str):
    """Recommend bikes using category, budget and riding purpose."""
    c, p = category.lower(), purpose.lower()
    results = []
    for bike in bike_database:
        if (c == "any" or c in bike["category"].lower()) and bike["price_lakh"] <= max_budget_lakh and (p == "any" or p in bike["best_for"].lower()):
            results.append(bike)
    if not results:
        results = [b for b in bike_database if (c == "any" or c in b["category"].lower()) and b["price_lakh"] <= max_budget_lakh]
    return json.dumps(results, indent=2) if results else "No exact recommendation was found."

llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    google_api_key=GEMINI_API_KEY,
    temperature=0,
    timeout=30,
    max_retries=2
)

agent = create_agent(
    model=llm,
    tools=[search_bikes, filter_by_budget, filter_by_category, compare_bikes, recommend_bike],
    system_prompt="""
You are an AI Bike Recommendation Agent.
Use the available tools for bike facts, prices, categories,
comparisons, budgets and recommendations.
Never invent specifications. Respect the user's budget.
Explain why a recommendation matches the user's requirement.
Mention that prices and specifications can change and should
be verified with the manufacturer or dealer.
"""
)

@app.route("/")
def home():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>AI Bike Recommendation Agent</title>

    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: Arial, Helvetica, sans-serif;
            background:
                radial-gradient(circle at top left, #252044 0%, transparent 35%),
                radial-gradient(circle at bottom right, #172f3d 0%, transparent 35%),
                #090b12;
            color: #ffffff;
            min-height: 100vh;
        }

        .container {
            width: 90%;
            max-width: 1100px;
            margin: auto;
            padding: 45px 0;
        }

        /* HEADER */

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 45px;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 14px;
        }

        .logo {
            width: 55px;
            height: 55px;
            border-radius: 16px;
            background: linear-gradient(135deg, #ff4d6d, #7c3aed);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 28px;
            box-shadow: 0 10px 35px rgba(124, 58, 237, 0.35);
        }

        .brand h1 {
            font-size: 30px;
            letter-spacing: -1px;
        }

        .brand p {
            color: #9ca3af;
            margin-top: 5px;
            font-size: 14px;
        }

        .status {
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.1);
            padding: 10px 15px;
            border-radius: 30px;
            color: #d1d5db;
            font-size: 13px;
        }

        .status-dot {
            width: 9px;
            height: 9px;
            background: #22c55e;
            border-radius: 50%;
            box-shadow: 0 0 12px #22c55e;
        }

        /* HERO */

        .hero {
            text-align: center;
            margin-bottom: 35px;
        }

        .hero h2 {
            font-size: 48px;
            line-height: 1.1;
            max-width: 800px;
            margin: auto;
            background: linear-gradient(90deg, #ffffff, #a78bfa, #fb7185);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .hero p {
            color: #9ca3af;
            margin-top: 18px;
            font-size: 17px;
        }

        /* SEARCH */

        .search-card {
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 22px;
            padding: 10px;
            backdrop-filter: blur(20px);
            box-shadow: 0 25px 70px rgba(0,0,0,0.35);
        }

        .search-box {
            display: flex;
            gap: 10px;
        }

        #question {
            flex: 1;
            border: none;
            outline: none;
            background: #11141d;
            color: white;
            border-radius: 15px;
            padding: 20px;
            font-size: 16px;
        }

        #question::placeholder {
            color: #6b7280;
        }

        .ask-btn {
            border: none;
            border-radius: 15px;
            padding: 0 28px;
            background: linear-gradient(135deg, #7c3aed, #ec4899);
            color: white;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: 0.2s;
        }

        .ask-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(236,72,153,0.3);
        }

        /* QUICK QUESTIONS */

        .quick {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 16px;
        }

        .quick button {
            border: 1px solid rgba(255,255,255,0.1);
            background: rgba(255,255,255,0.05);
            color: #d1d5db;
            padding: 9px 14px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 13px;
            transition: 0.2s;
        }

        .quick button:hover {
            background: rgba(124,58,237,0.25);
            border-color: #7c3aed;
            color: white;
        }

        /* FEATURES */

        .features {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin: 25px 0;
        }

        .feature {
            background: rgba(255,255,255,0.045);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 17px;
            padding: 20px;
        }

        .feature-icon {
            font-size: 25px;
            margin-bottom: 12px;
        }

        .feature h3 {
            font-size: 15px;
            margin-bottom: 6px;
        }

        .feature p {
            color: #8b93a3;
            font-size: 13px;
            line-height: 1.5;
        }

        /* ANSWER */

        .answer-card {
            background: rgba(255,255,255,0.055);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 22px;
            padding: 25px;
            margin-top: 25px;
            min-height: 130px;
        }

        .answer-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 18px;
        }

        .ai-icon {
            width: 38px;
            height: 38px;
            border-radius: 12px;
            background: linear-gradient(135deg, #7c3aed, #ec4899);
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .answer-header h3 {
            font-size: 17px;
        }

        #answer {
            color: #d1d5db;
            line-height: 1.7;
            white-space: pre-wrap;
            font-size: 15px;
        }

        .thinking {
            color: #a78bfa;
            animation: pulse 1.3s infinite;
        }

        @keyframes pulse {
            0%, 100% {
                opacity: 0.4;
            }
            50% {
                opacity: 1;
            }
        }

        /* FOOTER */

        footer {
            text-align: center;
            color: #596170;
            font-size: 12px;
            margin-top: 40px;
        }

        /* MOBILE */

        @media (max-width: 700px) {

            .container {
                width: 94%;
                padding: 25px 0;
            }

            .header {
                align-items: flex-start;
            }

            .status {
                display: none;
            }

            .brand h1 {
                font-size: 21px;
            }

            .logo {
                width: 45px;
                height: 45px;
                font-size: 23px;
            }

            .hero h2 {
                font-size: 34px;
            }

            .search-box {
                flex-direction: column;
            }

            .ask-btn {
                padding: 16px;
            }

            .features {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>

<body>

<div class="container">

    <!-- HEADER -->

    <div class="header">

        <div class="brand">
            <div class="logo">🏍️</div>

            <div>
                <h1>AI Bike Agent</h1>
                <p>Your intelligent motorcycle recommendation assistant</p>
            </div>
        </div>

        <div class="status">
            <span class="status-dot"></span>
            AI Agent Online
        </div>

    </div>


    <!-- HERO -->

    <div class="hero">

        <h2>Find the bike that fits your ride.</h2>

        <p>
            Tell me your budget, riding style or requirements.
            I'll find the best match.
        </p>

    </div>


    <!-- SEARCH -->

    <div class="search-card">

        <div class="search-box">

            <input
                id="question"
                type="text"
                placeholder="Try: Suggest an adventure bike under 3 lakh"
                onkeydown="if(event.key === 'Enter') askQuestion()"
            >

            <button class="ask-btn" onclick="askQuestion()">
                Ask AI ✨
            </button>

        </div>


        <div class="quick">

            <button onclick="setQuestion('Suggest an adventure bike under 3 lakh')">
                🏔️ Adventure
            </button>

            <button onclick="setQuestion('Suggest a sports bike under 3 lakh')">
                🏁 Sports
            </button>

            <button onclick="setQuestion('Suggest a bike for daily commuting')">
                🏙️ Commuter
            </button>

            <button onclick="setQuestion('Suggest a bike for touring')">
                🛣️ Touring
            </button>

            <button onclick="setQuestion('Compare Royal Enfield Himalayan 450 and Yezdi Adventure')">
                ⚖️ Compare Bikes
            </button>

        </div>

    </div>


    <!-- FEATURES -->

    <div class="features">

        <div class="feature">
            <div class="feature-icon">💰</div>
            <h3>Budget Smart</h3>
            <p>
                Find motorcycles that match your specified budget.
            </p>
        </div>

        <div class="feature">
            <div class="feature-icon">🎯</div>
            <h3>Personalized</h3>
            <p>
                Recommendations based on your riding purpose and category.
            </p>
        </div>

        <div class="feature">
            <div class="feature-icon">⚡</div>
            <h3>AI Powered</h3>
            <p>
                LangChain agent intelligently selects the right bike tools.
            </p>
        </div>

    </div>


    <!-- ANSWER -->

    <div class="answer-card">

        <div class="answer-header">

            <div class="ai-icon">
                ✨
            </div>

            <h3>AI Recommendation</h3>

        </div>

        <div id="answer">
            Ask me about a motorcycle to get started.
        </div>

    </div>


    <footer>
        AI Bike Recommendation Agent • Powered by LangChain & Gemini
    </footer>

</div>


<script>

function setQuestion(text) {
    document.getElementById("question").value = text;
    document.getElementById("question").focus();
}


async function askQuestion() {

    const question = document.getElementById("question").value.trim();
    const answerBox = document.getElementById("answer");

    if (!question) {
        answerBox.innerText = "Please enter a question first.";
        return;
    }

    answerBox.innerHTML =
        '<span class="thinking">🧠 AI is analyzing your requirements...</span>';

    try {

        const response = await fetch("/ask", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                question: question
            })
        });

        const data = await response.json();

        if (!response.ok) {
            answerBox.innerText =
                data.answer || "Something went wrong.";
            return;
        }

        answerBox.innerText =
            data.answer || "No recommendation received.";

    } catch (error) {

        answerBox.innerText =
            "Unable to connect to the AI agent. Please try again.";

        console.error(error);
    }
}

</script>

</body>
</html>
"""
@app.route("/ask", methods=["POST"])
def ask():
    try:
        data = request.get_json()
        question = data.get("question", "").strip()

        if not question:
            return jsonify({
                "answer": "Please enter a question."
            })

        print("QUESTION:", question, flush=True)

        result = agent.invoke({
            "messages": [
                {
                    "role": "user",
                    "content": question
                }
            ]
        })

        print("AGENT RESPONSE RECEIVED", flush=True)

        messages = result.get("messages", [])

        if not messages:
            return jsonify({
                "answer": "Agent returned no response."
            }), 500

        answer = messages[-1].content

        if isinstance(answer, str):
            final_answer = answer
        elif isinstance(answer, list):
            final_answer = "\n".join(
                str(item.get("text", item.get("content", "")))
                if isinstance(item, dict)
                else str(item)
                for item in answer
            )
        else:
            final_answer = str(answer)

        return jsonify({
            "answer": final_answer
        })

    except Exception as e:
        print("ERROR:", str(e), flush=True)
        return jsonify({
            "answer": "Error: " + str(e)
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
