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
    model="gemini-3.6-flash",
    google_api_key=GEMINI_API_KEY
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
    <html>
    <head><title>AI Bike Recommendation Agent</title></head>
    <body style="font-family:Arial;max-width:800px;margin:50px auto;padding:20px">
    <h1>🏍️ AI Bike Recommendation Agent</h1>
    <p>Ask about adventure, sports, touring, commuter and other bikes.</p>
    <input id="question" type="text" placeholder="Suggest an adventure bike under 3 lakh"
           style="width:75%;padding:12px">
    <button onclick="askQuestion()" style="padding:12px">Ask Agent</button>
    <h3>Answer:</h3><div id="answer" style="white-space:pre-wrap"></div>
    <script>
    async function askQuestion() {
        const question=document.getElementById("question").value;
        document.getElementById("answer").innerText="Agent is thinking...";
       async function askQuestion() {
    const question = document.getElementById("question").value;
    const answerBox = document.getElementById("answer");

    answerBox.innerText = "Agent is thinking...";

    try {
        const response = await fetch("/ask", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ question: question })
        });

        const data = await response.json();

        if (!response.ok) {
            answerBox.innerText = data.answer || data.error || "Server error";
            return;
        }

        answerBox.innerText = data.answer || "No answer returned.";

    } catch (error) {
        answerBox.innerText = "Connection error: " + error.message;
    }
}
        document.getElementById("answer").innerText=data.answer||data.error;
    }
    </script>
    </body></html>
    """

@app.route("/ask", methods=["POST"])
def ask():
    try:
        data = request.get_json()
        question = data.get("question", "").strip()
        if not question:
            return jsonify({"answer":"Please enter a question."})
        result = agent.invoke({
    "messages": [
        {"role": "user", "content": question}
    ]
})

messages = result.get("messages", [])

if not messages:
    return jsonify({"answer": "Agent returned no response."}), 500

answer = messages[-1].content

if isinstance(answer, list):
    final_answer = "\n".join(
        item.get("text", str(item)) if isinstance(item, dict) else str(item)
        for item in answer
    )
else:
    final_answer = str(answer)

return jsonify({"answer": final_answer})
        if isinstance(answer, str):
            final_answer = answer
        elif isinstance(answer, list):
            final_answer = "\n".join(
                str(item.get("text", item.get("content", ""))) if isinstance(item, dict) else str(item)
                for item in answer
            )
        else:
            final_answer = str(answer)
        return jsonify({"answer":final_answer})
    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({"answer":"Error: " + str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
