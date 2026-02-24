import os
import uuid

from flask import Flask, render_template, redirect, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user
)
from werkzeug.utils import secure_filename


# -----------------------
# APP CONFIG
# -----------------------

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "supersecret")

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///recipes.db"

app.config["UPLOAD_FOLDER"] = os.path.join(
    app.root_path,
    "static",
    "uploads"
)

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


# -----------------------
# DATABASE
# -----------------------

db = SQLAlchemy(app)


# -----------------------
# LOGIN
# -----------------------

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)


# -----------------------
# SINGLE USER
# -----------------------

USERNAME = os.environ.get("APP_USERNAME", "mama")
PASSWORD = os.environ.get("APP_PASSWORD", "secret")


class SingleUser(UserMixin):
    id = 1


@login_manager.user_loader
def load_user(user_id):

    if user_id == "1":
        return SingleUser()

    return None


# -----------------------
# MODELS
# -----------------------

class Folder(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))


class Recipe(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200))
    ingredients = db.Column(db.Text)
    instructions = db.Column(db.Text)

    image = db.Column(db.String(300), nullable=True)

    folder_id = db.Column(db.Integer, nullable=True)


# -----------------------
# INIT DB
# -----------------------

with app.app_context():
    db.create_all()


# -----------------------
# ROUTES
# -----------------------

@app.route("/")
def index():

    folders = Folder.query.all()

    return render_template(
        "index.html",
        folders=folders,
        recipes=[],
        active_folder=None
    )


@app.route("/folder/<int:folder_id>")
def view_folder(folder_id):

    folder = Folder.query.get_or_404(folder_id)

    recipes = Recipe.query.filter_by(
        folder_id=folder_id
    ).all()

    folders = Folder.query.all()

    return render_template(
        "index.html",
        folders=folders,
        recipes=recipes,
        active_folder=folder
    )


# -----------------------
# LOGIN
# -----------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        if (
            request.form["username"] == USERNAME and
            request.form["password"] == PASSWORD
        ):

            login_user(SingleUser())
            return redirect("/")

        flash("Wrong login")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():

    logout_user()
    return redirect("/")


# -----------------------
# RECIPES
# -----------------------

@app.route("/recipe/new", methods=["GET", "POST"])
@login_required
def new_recipe():

    folders = Folder.query.all()

    if request.method == "POST":

        filename = None

        if "image" in request.files:

            file = request.files["image"]

            if file and file.filename:

                unique = str(uuid.uuid4()) + "_" + secure_filename(file.filename)

                file.save(
                    os.path.join(
                        app.config["UPLOAD_FOLDER"],
                        unique
                    )
                )

                filename = unique

        recipe = Recipe(
            title=request.form["title"],
            ingredients=request.form["ingredients"],
            instructions=request.form["instructions"],
            folder_id=request.form["folder"],
            image=filename
        )

        db.session.add(recipe)
        db.session.commit()

        return redirect("/folder/" + request.form["folder"])

    return render_template(
        "recipe_form.html",
        folders=folders,
        recipe=None
    )


@app.route("/recipe/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_recipe(id):

    recipe = Recipe.query.get_or_404(id)

    folders = Folder.query.all()

    if request.method == "POST":

        recipe.title = request.form["title"]
        recipe.ingredients = request.form["ingredients"]
        recipe.instructions = request.form["instructions"]
        recipe.folder_id = request.form["folder"]

        db.session.commit()

        return redirect("/folder/" + str(recipe.folder_id))

    return render_template(
        "recipe_form.html",
        folders=folders,
        recipe=recipe
    )


@app.route("/recipe/delete/<int:id>")
@login_required
def delete_recipe(id):

    recipe = Recipe.query.get_or_404(id)

    db.session.delete(recipe)
    db.session.commit()

    return redirect("/")


# -----------------------
# FOLDERS
# -----------------------

@app.route("/folders", methods=["GET", "POST"])
@login_required
def folders():

    if request.method == "POST":

        folder = Folder(
            name=request.form["name"]
        )

        db.session.add(folder)
        db.session.commit()

    folders = Folder.query.all()

    return render_template(
        "folders.html",
        folders=folders
    )


@app.route("/folder/delete/<int:folder_id>")
@login_required
def delete_folder(folder_id):

    folder = Folder.query.get(folder_id)

    if not folder:
        return redirect("/")

    Recipe.query.filter_by(
        folder_id=folder_id
    ).update({"folder_id": None})

    db.session.delete(folder)
    db.session.commit()

    return redirect("/")


# -----------------------
# START
# -----------------------

if __name__ == "__main__":


    app.run(host="0.0.0.0", port=5000)
