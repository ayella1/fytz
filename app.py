import io
import os
import time
import traceback
import random

from cs50 import SQL
from PIL import Image
from datetime import datetime
from flask_session import Session
from rembg import remove, new_session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, redirect, jsonify, flash, request, session
from helpers import login_required, fetch_weather_logic

# NEW: Import the helpers you just created
from helpers import login_required, fetch_weather_logic

app = Flask(__name__)

# Configure session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, "static/uploads")
Session(app)

# Configure CS50 Library to use SQLite fytz database
db = SQL("sqlite:///fytz.db")

#for user data access
@app.context_processor
def inject_user():
    if session.get("user_id"):
        user = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])[0]
        return dict(user=user)
    return dict(user=None)

#login page
@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        # Check if username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            flash("Invalid username and/or password!", 403)
            return render_template("login.html")

        session["user_id"] = rows[0]["id"]
        return redirect("/")
    return render_template("login.html")


#register route
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        join_date = datetime.now().strftime("%Y-%m-%d")

        if not username or not password or password != confirmation:
            flash("Invalid input!", 400)
            return render_template("register.html")

        hash = generate_password_hash(password)
        try:
            new_user_id = db.execute("INSERT INTO users (username, hash, registered_at) VALUES(?, ?, ?)", username, hash, join_date)
            session["user_id"] = new_user_id

            flash("Registered!")
            return redirect("/")

        except:
            flash("Username already exists!", 400)
            return render_template("register.html")

    return render_template("register.html")

#log out route
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

#main index route
@app.route("/")
@login_required
def index():
    if not session.get("user_id"):
        return redirect("/login")
    # Fetch the logged-in user's info
    user = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])[0]
    return render_template("home.html", user=user)

from rembg import remove

#update user profile pic
@app.route("/upload_profile", methods=["POST"])
@login_required
def upload_profile():
    file = request.files.get("profile_photo")
    # Check if the user opted for background removal
    remove_bg = request.form.get("remove_bg") == "on"

    if file:
        filename = f"profile_{session['user_id']}_{int(time.time())}.png"
        filepath = os.path.join(app.root_path, "static/uploads", filename)

        # Open the uploaded file stream
        input_data = file.read()

        if remove_bg:
            # Process with rembg
            output_data = remove(input_data)
        else:
            output_data = input_data

        # Save the processed (or original) bytes to a file
        with open(filepath, 'wb') as f:
            f.write(output_data)

        db.execute("UPDATE users SET profile_image = ? WHERE id = ?", filename, session["user_id"])
        flash("Profile picture updated!")

    return redirect("/settings")


#update user location and preferences
@app.route("/update_settings", methods=["POST"])
@login_required
def update_settings():
    gender = request.form.get("gender")
    address = request.form.get("address")
    style_preference = request.form.get("style_preference")

    # Update the user record
    db.execute("""
        UPDATE users
        SET gender = ?, address = ?,
        style_preference = ? WHERE id = ?
    """, gender, address, style_preference, session["user_id"])
    flash("Settings updated successfully!")
    return redirect("/settings")

#statistics for setting page
@app.route("/settings")
@login_required
def settings():
    user_id = session["user_id"]
    user = db.execute("SELECT * FROM users WHERE id = ?", user_id)[0]

    raw_date = user.get("registered_at")
    if raw_date:
        formatted_date = datetime.strptime(raw_date, "%Y-%m-%d").strftime("%m/%d/%Y")
    else:
        formatted_date = "05/01/2026" # Fallback

    # Statistics
    total_items = db.execute("SELECT COUNT(*) as count FROM wardrobe WHERE user_id = ? AND is_deleted = 0", user_id)[0]['count']
    total_outfits = db.execute("SELECT COUNT(*) as count FROM outfits WHERE user_id = ?", user_id)[0]['count']

    # Category Breakdown
    rows = db.execute("SELECT category, COUNT(*) as count FROM wardrobe WHERE user_id = ? AND is_deleted = 0 GROUP BY category", user_id)
    breakdown = {row['category']: row['count'] for row in rows}

    return render_template("settings.html", user=user, display_date=formatted_date, total_items=total_items, total_outfits=total_outfits, breakdown=breakdown)


# Update Username
@app.route("/update_username", methods=["POST"])
@login_required
def update_username():
    new_username = request.form.get("username").strip()
    if not new_username:
        flash("Username cannot be empty")
        return redirect("/settings")

    try:
        db.execute("UPDATE users SET username = ? WHERE id = ?", new_username, session["user_id"])
        flash("Username updated!")
    except:
        flash("Username already taken")
    return redirect("/settings")


# Update Password (with Old Password Check)
@app.route("/change_password", methods=["POST"])
@login_required
def change_password():
    old_password = request.form.get("current_password")
    new_password = request.form.get("new_password")
    confirmation = request.form.get("confirmation")

    # Verify identity with old password
    user = db.execute("SELECT hash FROM users WHERE id = ?", session["user_id"])
    if not check_password_hash(user[0]["hash"], old_password):
        flash("Incorrect current password")
        return redirect("/settings")

    # Check match
    if new_password != confirmation:
        flash("New passwords do not match")
        return redirect("/settings")

    # Save new hash
    new_hash = generate_password_hash(new_password)
    db.execute("UPDATE users SET hash = ? WHERE id = ?", new_hash, session["user_id"])
    flash("Password updated successfully!")
    return redirect("/settings")

#get weather data from helpers file
@app.route("/api/weather")
@login_required
def get_weather():
    user = db.execute("SELECT address FROM users WHERE id = ?", session["user_id"])[0]
    address = user.get("address")
    data = fetch_weather_logic(address)

    if not data:
        data = {
            "temp": "70", "forecast": "Sunny(Demo)",
            "location": address or "Cambridge, MA.",
            "icon": "https://www.weather.gov/images/forecast/icons/skc.png"
        }

    session["weather_data"] = data
    session.modified = True
    return jsonify(data)

#smart tag clothes for better searching and suggestions
@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        file = request.files.get("image")
        category = request.form.get("category")
        user_input = request.form.get("tags", "").strip().lower()

        # SMART AUTO-TAGGING DICTIONARY
        # Maps user categories and input keywords to extra search terms
        tag_map = {
            "dresses": ["dress", "one-piece", "gown", "clothing", "formal", "suit", "frock", "bikini"],
            "shirts": ["top", "upper", "blouse", "shirt", "clothing", "casual", "button-down", "t-shirt", "party", "dresses"],
            "pants": ["chinos","bottom", "trousers", "denim", "jeans", "slacks", "clothing", "skirt", "casual"],
            "shoes": ["footwear", "sneakers", "boots", "sandals", "kicks", "slippers", "casual"],
            "shades": ["accessory", "eyewear", "glasses", "sunglasses", "shades", "specs", "casual"]
        }


        # GENERATE TAGS
        # Start with the basic category auto-tags
        final_tags = set(tag_map.get(category, []))

        # Add synonyms based on what the user typed
        user_list = [t.strip() for t in user_input.split(",") if t.strip()]
        for tag in user_list:
            final_tags.add(tag)
            # Link specific items (e.g., if they type 'jeans', auto-add 'pants')
            if tag in ["jeans", "trousers", "chinos"]: final_tags.add("pants")
            if tag in ["t-", "tee", "sweat", "polo", "hoodie"]: final_tags.add("shirts")
            if tag in ["club", "night", "shiny", "sparkly", "dance", "dresses"]: final_tags.add("party")
            if tag in ["relaxed", "hoodie", "t-", "tee", "sweatpants"]: final_tags.add("casual")
        # Combine into a clean comma-separated string
        all_tags_str = ",".join(list(final_tags))

        if file and category:
            # Process image with rembg
            input_image = Image.open(file.stream)
            output_image = remove(input_image).convert("RGBA")

            clean_name = secure_filename(file.filename).rsplit('.', 1)[0]
            filename = f"{clean_name}_{int(time.time())}.png"
            filepath = os.path.join(app.root_path, "static/uploads", filename)
            output_image.save(filepath, "PNG")

            # Save to Database
            db.execute("""
                INSERT INTO wardrobe (user_id, category, tags, view_type, image_file, is_favorite, is_deleted)
                VALUES (?, ?, ?, ?, ?, 0, 0)
            """, session["user_id"], category, all_tags_str, "front", filename)

            flash(f"Item added to {category} with tags: {all_tags_str}")
            return redirect("/upload")

    return render_template("upload.html")


#get ward robe data for main page
@app.route("/api/wardrobe")
@login_required
def get_wardrobe():
    page = int(request.args.get("page", 1))
    category = request.args.get("category", "all")
    search_query = request.args.get("q", "").strip().lower()
    only_favs = request.args.get("favs") == "true"

    per_page = 12
    offset = (page - 1) * per_page

    # Base query parts
    query = "SELECT * FROM wardrobe WHERE user_id = ? AND is_deleted = 0"
    params = [session["user_id"]]

    # Filter by Category
    if category != "all":
        query += " AND category = ?"
        params.append(category)

    # Filter by Favorites
    if only_favs:
        query += " AND is_favorite = 1"

    # Filter by Search (The Smart Part)
    '''
    if search_query:
        query += " AND (tags LIKE ? OR category LIKE ?)"
        params.append(f"%{search_query}%")
        params.append(f"%{search_query}%")
    '''

    if search_query:
        # This checks the category name, the tags, and specific common synonyms
        query += """ AND (
            category LIKE ? OR
            tags LIKE ? OR
            (category = 'pants' AND 'slacks' LIKE ?) OR
            (category = 'shirts' AND 'top' LIKE ?)
        )"""
        params.append(f"%{search_query}%")
        params.append(f"%{search_query}%")
        params.append(f"%{search_query}%")
        params.append(f"%{search_query}%")

    # Get total count for pagination before applying LIMIT
    count_query = query.replace("SELECT *", "SELECT COUNT(*) as count")
    total = db.execute(count_query, *params)[0]['count']

    # Finalize query with Pagination
    query += " LIMIT ? OFFSET ?"
    params.extend([per_page, offset])

    items = db.execute(query, *params)

    return jsonify({
        "items": items,
        "total_pages": (total + per_page - 1) // per_page,
        "current_page": page
    })


#finilize output and update database
@app.route("/finalize", methods=["POST"])
@login_required
def finalize():
    data = request.get_json()
    user_id = session["user_id"]

    # Check if weather exists in session
    weather = session.get("weather_data")

    # If session is empty, try to return a default so the DB doesn't stay empty
    if not weather:
        print("DEBUG: Weather data missing from session! Using defaults.")
        weather = {"temp": 70, "forecast": "Sunny (Demo)", "location": "Cambridge, MA.",
        "icon": "https://www.weather.gov/images/forecast/icons/skc.png" # Standard Sunny Icon
        }


    db.execute("""
        INSERT INTO outfits (user_id, shirt_id, pants_id, shoes_id, shades_id, temp_worn, forecast_worn, icon_worn)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
    user_id,
    data.get('shirts'),
    data.get('pants'),
    data.get('shoes'),
    data.get('shades'),
    weather['temp'],
    weather['forecast'],
    weather['icon'])

    print("DEBUG: Outfit saved to database successfully.")
    flash("Outfit saved successfully!")
    return jsonify({"success": True})


#toggle to have fav only
@app.route("/toggle_favorite", methods=["POST"])
@login_required
def toggle_favorite():
    if not session.get("user_id"):
        return jsonify({"success": False}), 401

    data = request.get_json()
    item_id = data.get("item_id")

    # Get current status
    item = db.execute("SELECT is_favorite FROM wardrobe WHERE id = ? AND user_id = ?",
                      item_id, session["user_id"])

    if item:
        new_status = 1 if item[0]["is_favorite"] == 0 else 0
        db.execute("UPDATE wardrobe SET is_favorite = ? WHERE id = ? AND user_id = ?",
           new_status, item_id, session["user_id"])
        return jsonify({"success": True, "new_status": new_status})

    return jsonify({"success": False}), 400

# saved output data
@app.route("/history")
@login_required
def history():
    rows = db.execute("""
        SELECT o.id, o.date_worn, o.temp_worn, o.forecast_worn, o.icon_worn, o.is_favorite,
               w1.image_file AS shirt_img,
               w2.image_file AS pants_img,
               w3.image_file AS shoes_img,
               w4.image_file AS shades_img
        FROM outfits o
        LEFT JOIN wardrobe w1 ON o.shirt_id = w1.id
        LEFT JOIN wardrobe w2 ON o.pants_id = w2.id
        LEFT JOIN wardrobe w3 ON o.shoes_id = w3.id
        LEFT JOIN wardrobe w4 ON o.shades_id = w4.id
        WHERE o.user_id = ?
        ORDER BY o.date_worn DESC
    """, session["user_id"])

    return render_template("history.html", outfits=rows)


#outfit can be selected as favorites
@app.route("/toggle_outfit_favorite", methods=["POST"])
@login_required
def toggle_outfit_favorite():
    data = request.get_json()
    outfit_id = data.get("outfit_id")

    # Get current status
    outfit = db.execute("SELECT is_favorite FROM outfits WHERE id = ? AND user_id = ?",
                         outfit_id, session["user_id"])

    if outfit:
        new_status = 1 if outfit[0]["is_favorite"] == 0 else 0
        db.execute("UPDATE outfits SET is_favorite = ? WHERE id = ?", new_status, outfit_id)
        return jsonify({"success": True, "new_status": new_status})

    return jsonify({"success": False}), 400

#delete outfit route
@app.route("/delete_outfit/<int:id>", methods=["POST"])
@login_required
def delete_outfit(id):
     db.execute("DELETE FROM outfits WHERE id = ? AND user_id = ?", id, session["user_id"])
     return jsonify({"success": True})

@app.route("/api/recommend")
@login_required
def recommend():
    # Get current User context
    user = db.execute("SELECT gender, style_preference FROM users WHERE id = ?", session["user_id"])[0]
    gender = user.get('gender', 'male')
    style = user.get('style_preference', 'casual')
    fav_only = request.args.get("favorites_only") == "true"

    # Weather Context
    weather = session.get("weather_data")
    weather_data = weather if weather else {"temp": 70, "forecast": "clear"}
    temp = int(weather_data.get('temp', 70))
    forecast = weather_data.get('forecast', "").lower()

    # Calculate Dress Probability
    dress_chance = 0.45 if gender == 'female' else 0.05
    if style in ['party', 'formal']:
        dress_chance += 0.20

    is_dress_day = random.random() < dress_chance

    # Build Query
    query = "SELECT * FROM wardrobe WHERE user_id = ? AND is_deleted = 0"
    params = [session["user_id"]]
    if fav_only:
        query += " AND is_favorite = 1"

    # (Keep your existing weather/vibe tag logic here...)
    # ...

    # EXECUTION ENGINE
    outfit = {}
    categories_to_fetch = ['shoes', 'shades']

    if is_dress_day:
        dress = db.execute(query + " AND category = 'dresses' ORDER BY RANDOM() LIMIT 1", *params)
        if dress:
            outfit['dresses'] = dress[0] # Return the item dictionary directly
            outfit['pants'] = None
        else:
            categories_to_fetch.extend(['shirts', 'pants'])
    else:
        categories_to_fetch.extend(['shirts', 'pants'])

    for cat in categories_to_fetch:
        item = db.execute(query + " AND category = ? ORDER BY RANDOM() LIMIT 1", *params, cat)
        if not item:
            item = db.execute("SELECT * FROM wardrobe WHERE user_id = ? AND category = ? AND is_deleted = 0 ORDER BY RANDOM() LIMIT 1",
                              session["user_id"], cat)
        if item:
            outfit[cat] = item[0] # Return the item dictionary directly

    return jsonify(outfit)


#bulk selection and delete items from wardrobe
@app.route("/api/wardrobe/delete_bulk", methods=["POST"])
@login_required
def delete_bulk():
    data = request.get_json()
    item_ids = data.get("ids", [])

    for item_id in item_ids:
        # Check if this item is part of ANY outfit history
        history_check = db.execute("""
            SELECT id FROM outfits
            WHERE shirt_id = ? OR pants_id = ? OR shoes_id = ? OR shades_id = ?
            LIMIT 1
        """, item_id, item_id, item_id, item_id)

        if history_check:
            # SOFT DELETE: It's in the history, so just hide it from the closet
            db.execute("UPDATE wardrobe SET is_favorite = 0, is_deleted = 1 WHERE id = ? AND user_id = ?",
                       item_id, session["user_id"])
            print(f"DEBUG: Soft deleted item {item_id} (preserved for history)")
        else:
            # HARD DELETE: It's never been worn, so remove it entirely
            item = db.execute("SELECT image_file FROM wardrobe WHERE id = ? AND user_id = ?",
                              item_id, session["user_id"])
            if item:
                # Delete the physical file
                file_path = os.path.join(app.root_path, "static/uploads", item[0]["image_file"])
                if os.path.exists(file_path):
                    os.remove(file_path)

                # Delete from database
                db.execute("DELETE FROM wardrobe WHERE id = ? AND user_id = ?", item_id, session["user_id"])
                print(f"DEBUG: Hard deleted item {item_id} (never worn)")

    flash(f"Processed {len(item_ids)} items.")
    return jsonify({"success": True})

#upload saved outfits to mannequin
@app.route("/upload_mannequin", methods=["POST"])
@login_required
def upload_mannequin():
    file = request.files.get("mannequin_photo")
    # Check if the user wants to remove the background
    process_rembg = request.form.get("remove_bg") == "on"

    if file:
        input_image = Image.open(file.stream)

        if process_rembg:
            # Process with rembg
            output_image = remove(input_image).convert("RGBA")
        else:
            # Load as is
            output_image = input_image.convert("RGBA")

        filename = f"user_{session['user_id']}_head_{int(time.time())}.png"
        filepath = os.path.join(app.root_path, "static/uploads", filename)
        output_image.save(filepath, "PNG")

        db.execute("UPDATE users SET mannequin_head = ? WHERE id = ?", filename, session["user_id"])
        flash("Mannequin head updated!")

    return redirect("/settings")


#clear mannequin
@app.route("/reset_mannequin", methods=["POST"])
@login_required
def reset_mannequin():
    # Set the mannequin_head back to NULL to use the default profile.jpeg
    db.execute("UPDATE users SET mannequin_head = NULL WHERE id = ?", session["user_id"])
    flash("Mannequin reset to default.")
    return redirect("/settings")

#delete profile picture
@app.route("/delete_profile_pic", methods=["POST"])
@login_required
def delete_profile_pic():
    # Get the current filename from the database
    user_id = session["user_id"]
    user = db.execute("SELECT profile_image FROM users WHERE id = ?", user_id)

    if user and user[0]["profile_image"]:
        filename = user[0]["profile_image"]

        # Delete the physical file from the static/uploads folder
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            os.remove(file_path)

        # Reset the database field to NULL
        db.execute("UPDATE users SET profile_image = NULL WHERE id = ?", user_id)

        flash("Profile picture removed successfully.")
    else:
        flash("No profile picture to delete.")

    return redirect("/settings")

if __name__ == "__main__":
    app.run(debug=True)
