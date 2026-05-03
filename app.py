from flask import Flask, render_template, request, redirect, make_response
import json
import os
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

database_url = os.environ.get("DATABASE_URL")

# Fix for Render PostgreSQL URL
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url or "sqlite:///tasks.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(200), nullable=False)
    done = db.Column(db.Boolean, default=False)
    priority = db.Column(db.String(10))
    category = db.Column(db.String(20))
    due_date = db.Column(db.String(20))


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
    tasks = Task.query.all()

    filter_type = request.args.get("filter")
    category_filter = request.args.get("category")

    today = datetime.today().date()

    filtered_tasks = []

    for t in tasks:
        # Filter logic
        if filter_type == "completed" and not t.done:
            continue
        if filter_type == "pending" and t.done:
            continue
        if category_filter in ["work", "personal"] and t.category != category_filter:
            continue

        # Due date status
        if t.due_date:
            due = datetime.strptime(t.due_date, "%Y-%m-%d").date()
            if due < today:
                t.due_status = "overdue"
            else:
                t.due_status = "upcoming"
        else:
            t.due_status = None

        filtered_tasks.append(t)

    # 🔥 SORT HERE
    priority_order = {"high": 1, "low": 2}
    category_order = {"work": 1, "personal": 2}

    
    filtered_tasks.sort(key=lambda t: (
        t.done,
        priority_order.get(t.priority, 2),
        category_order.get(t.category, 2)
))

    response = make_response(
        render_template(
            "index.html",
            tasks=enumerate(filtered_tasks),
            current_filter=filter_type,
            current_category=category_filter
        )
    )

    response.headers["Cache-Control"] = "no-store"
    return response


@app.route("/add", methods=["POST"])
def add():
    task_text = request.form["task"]
    priority = request.form["priority"]
    category = request.form["category"]
    due_date = request.form.get("due_date")

    new_task = Task(
        task=task_text,
        done=False,
        priority=priority,
        category=category,
        due_date=due_date if due_date else None
    )

    db.session.add(new_task)
    db.session.commit()

    return redirect("/")


@app.route("/delete/<int:task_id>")
def delete(task_id):
    task = db.session.get(Task, task_id)

    if task:
        db.session.delete(task)
        db.session.commit()

    return redirect("/")


@app.route("/toggle/<int:task_id>")
def toggle(task_id):
    task = db.session.get(Task, task_id)

    if task:
        task.done = not task.done
        db.session.commit()

    return redirect("/")


with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))