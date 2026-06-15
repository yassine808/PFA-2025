import json
import os
from flask import (
    Blueprint, render_template, request, jsonify,
    session, redirect, url_for, flash, Response, stream_with_context
)
from app.DLchatbotFrancais import get_answer_stream # Streaming function you must define


main = Blueprint('main', __name__)

USERS_FILE = os.path.join(os.path.dirname(__file__), "../users.txt")
USER_DATA_DIR = os.path.join(os.path.dirname(__file__), "../user_data")

def save_user(user):
    users = []
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            users = [json.loads(line) for line in f]
        users = [u for u in users if u["email"] != user["email"]]
    users.append(user)
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        for u in users:
            f.write(json.dumps(u, ensure_ascii=False) + "\n")

def find_user(email, password=None):
    if not os.path.exists(USERS_FILE):
        return None
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            u = json.loads(line)
            if u["email"] == email and (password is None or u["password"] == password):
                return u
    return None

def user_history_path(email):
    safe_email = email.replace("@", "_at_").replace(".", "_dot_")
    return os.path.join(USER_DATA_DIR, f"history_{safe_email}.json")

def load_history(email):
    path = user_history_path(email)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_history(email, history):
    os.makedirs(USER_DATA_DIR, exist_ok=True)
    path = user_history_path(email)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False)

def update_user_infos(email, name, username, gender):
    users = []
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            users = [json.loads(line) for line in f]
    for u in users:
        if u["email"] == email:
            u["name"] = name
            u["username"] = username
            u["gender"] = gender
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        for u in users:
            f.write(json.dumps(u, ensure_ascii=False) + "\n")

def update_user_password(email, new_password):
    users = []
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            users = [json.loads(line) for line in f]
    for u in users:
        if u["email"] == email:
            u["password"] = new_password
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        for u in users:
            f.write(json.dumps(u, ensure_ascii=False) + "\n")

@main.route("/")
def home():
    if "user" in session:
        return redirect(url_for("main.homepage"))
    return render_template("index.html")

@main.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        gender = request.form["gender"]
        if find_user(email):
            flash("Cet email existe déjà.", "danger")
            return render_template("signup.html")
        user = {
            "name": name, "username": username, "email": email,
            "password": password, "gender": gender
        }
        save_user(user)
        session["user"] = user
        session["chat_history"] = load_history(email)
        return redirect(url_for("main.homepage"))
    return render_template("signup.html")

@main.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = find_user(email, password)
        if user:
            session["user"] = user
            session["chat_history"] = load_history(email)
            return redirect(url_for("main.homepage"))
        flash("Email ou mot de passe incorrect.", "danger")
    return render_template("login.html")

@main.route("/homepage")
def homepage():
    if "user" not in session:
        return redirect(url_for("main.login"))
    return render_template("homepage.html", user=session["user"])

@main.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.home"))

@main.route("/chatbot")
def chatbot():
    if "user" not in session:
        return redirect(url_for("main.login"))
    return render_template("chatbot.html", user=session["user"])

#--------------------------------------------------------------------------------
from flask import Response, stream_with_context, after_this_request

@main.route("/chat-stream", methods=["POST"])
def chat_stream():
    if "user" not in session:
        return jsonify({"error": "Veuillez vous connecter pour utiliser le chatbot."}), 401

    data = request.get_json()
    question = data.get("question", "")
    email = session["user"]["email"]
    
    # Save the question immediately (same as /ask endpoint)
    history = session.get("chat_history", [])
    history.append({"role": "user", "text": question})
    session["chat_history"] = history
    save_history(email, history)
    
    full_answer = []

    def generate():
        try:
            # Stream the answer chunks
            for chunk in get_answer_stream(question):
                full_answer.append(chunk)
                yield chunk
        except Exception as e:
            error_msg = f"\n[Erreur] {str(e)}"
            full_answer.append(error_msg)
            yield error_msg
        finally:
            # This will run after streaming completes (success or error)
            answer_text = "".join(full_answer)
            
            # Reload fresh history to avoid any race conditions
            current_history = load_history(email)
            
            # Find our question in history (should be the last one)
            if current_history and current_history[-1]["role"] == "user" and current_history[-1]["text"] == question:
                # Add the answer after the question
                current_history.append({"role": "bot", "text": answer_text})
            else:
                # Fallback: add both question and answer
                current_history.extend([
                    {"role": "user", "text": question},
                    {"role": "bot", "text": answer_text}
                ])
            
            # Update both session and file storage
            session["chat_history"] = current_history
            save_history(email, current_history)

    return Response(stream_with_context(generate()), mimetype="text/plain")
#-----------------------------------------------------------------
 
@main.route("/chat-history")
def chat_history():
    if "user" not in session:
        return jsonify([])
    
    # Always load fresh history from file
    email = session["user"]["email"]
    history = load_history(email)
    
    # Update session to keep it in sync
    session["chat_history"] = history
    
    return jsonify(history)


# ----- PAGE PROFIL --------------------
@main.route("/profile", methods=["GET", "POST"])
def profile():
    if "user" not in session:
        return redirect(url_for("main.login"))
    user = session["user"]
    if request.method == "POST":
        name = request.form.get("name", user["name"])
        username = request.form.get("username", user["username"])
        gender = request.form.get("gender", user["gender"])
        update_user_infos(user["email"], name, username, gender)
        user = find_user(user["email"])
        session["user"] = user
        flash("Profil mis à jour !", "success")
        return redirect(url_for("main.profile"))
    return render_template("profile.html", user=user)

@main.route("/change-password", methods=["POST"])
def change_password():
    if "user" not in session:
        return redirect(url_for("main.login"))
    email = session["user"]["email"]
    old_pw = request.form.get("old_password")
    new_pw = request.form.get("new_password")
    user = find_user(email)
    if user["password"] != old_pw:
        flash("Ancien mot de passe incorrect", "danger")
    else:
        update_user_password(email, new_pw)
        session["user"] = find_user(email)
        flash("Mot de passe modifié !", "success")
    return redirect(url_for("main.profile"))