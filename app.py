from flask import Flask, render_template, request, redirect, make_response
import json
import os

from datetime import datetime

app = Flask(__name__)

def load_tasks():
    try:
        with open("tasks.json", "r") as file:
            return json.load(file)
    except:
        return []

def save_tasks(tasks):
    sort_tasks(tasks)
    with open("tasks.json", "w") as file:
        json.dump(tasks, file, indent=4)

def sort_tasks(tasks):
    priority_order = {"high": 1, "low": 2}
    category_order = {"work": 1, "personal": 2}

    tasks.sort(key=lambda t: (
        t.get("done",False),                      # False first (pending)
        priority_order.get(t.get("priority"), 2),  # high first
        category_order.get(t.get("category"), 2)   # work first
    ))

@app.route("/sw.js")
def sw():
    response = app.send_static_file("sw.js")
    response.headers["Cache-Control"] = "no-store"
    return response

@app.route("/")
def index():
    tasks = load_tasks()
    filter_type = request.args.get("filter") # pending / completed
    category_filter = request.args.get("category") # work / personal
    if not category_filter:
        category_filter = None

    indexed_tasks = list(enumerate(tasks))  # keep original index

    today = datetime.today().date()
    
    if filter_type == "completed":
        indexed_tasks = [(i, t) for i, t in indexed_tasks if t["done"]]
    elif filter_type == "pending":
        indexed_tasks = [(i, t) for i, t in indexed_tasks if not t["done"]]

    if category_filter in ["work", "personal"]:
        indexed_tasks = [(i, t) for i, t in indexed_tasks if t["category"] == category_filter]

        
    for i, t in indexed_tasks:
        if t.get("due_date"):
            due = datetime.strptime(t["due_date"], "%Y-%m-%d").date()
            if due < today:
                t["due_status"] = "overdue"
            else:
                t["due_status"] = "upcoming"
        else:
            t["due_status"] = None    

    response = make_response(
    render_template(
        "index.html",
        tasks=indexed_tasks,
        current_filter=filter_type,
        current_category=category_filter
    )
)

# 🔥 Important for PWA caching
    response.headers["Cache-Control"] = "no-store"

    return response


@app.route("/add", methods=["POST"])
def add():
    tasks = load_tasks()

    task_text = request.form["task"]
    priority = request.form["priority"]
    category = request.form["category"]
    
    if category not in ["work", "personal"]:
        category = "personal"  # default

    due_date = request.form.get("due_date")

    tasks.append({
        "task": task_text,
        "done": False,
        "priority": priority,
        "category": category,
        "due_date": due_date if due_date else None
    })

    save_tasks(tasks)
    return redirect("/")


@app.route("/delete/<int:task_id>")
def delete(task_id):
    tasks = load_tasks()

    if 0 <= task_id < len(tasks):
        tasks.pop(task_id)

    save_tasks(tasks)
    return redirect("/")


@app.route("/toggle/<int:task_id>")
def toggle(task_id):
    tasks = load_tasks()

    if 0 <= task_id < len(tasks):
        tasks[task_id]["done"] = not tasks[task_id]["done"]

    save_tasks(tasks)
    return redirect("/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))