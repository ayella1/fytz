Video implementation: https://youtu.be/brg1SU7Ab54

fytz: Your Personal Wardrobe & Outfit Simulator

Table of Contents
Description
Requirements
Installation & Setup
Running the App
Creating an Account
Features Walkthrough
Adding Clothes to Your Closet
The Virtual Closet (Home Page)
Outfit Recommendations
Outfit History
Settings
Notes & Known Limitations

Description
fytz is a web-based virtual wardrobe application that lets you upload, organize, and style your clothing digitally. You can take pictures of your clothing items and add them to your fytz wardrobe as either shirts/tops, dresses, pants/skirts/shorts, shoes, and sunglasses. You can then use your interactive mannequin/outfit vision board to look at different clothing combinations. You can do this by either choosing your clothes straight from your digital wardrobe or getting AI-powered outfit recommendations based on real-time weather. You can then save the outfit to your history and even choose past outfits from your history to look at on your mannequin again.
Requirements
Before running FYTZ, make sure you have the following installed on your machine/virtual workspace:
Python 3.10+
pip (Python package manager) → helps with Flask, Pillow, rembg, cs50, etc.
A terminal / command prompt
The fytz webpage runs entirely locally which means there is no external database server or cloud service is required. However, internet access is needed for live weather data (pulled from weather.gov) to provide outfit recommendations and the Bootstrap/Font Awesome CDN links used for webpage styling.

Installation & Setup
1. Unzip the project by typing the following in your terminal:
unzip fytz.zip
rm -f fytz.zip
cd fytz
2. (Optional) Create a virtual environment
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows
3. Install any dependencies
pip install -r requirements.txt
This will install Flask, Flask-Session, the CS50 SQL library, Pillow, rembg (AI background removal), Werkzeug, and Requests. It is also important to know that rembg downloads a small AI model on first use, so this may take a moment the first time you upload a clothing item or photo. The zip file already contains a requirements.txt, but, just in case you can run the line of the code above.
4. Verify the database
The zipped project folder already contains fytz.db (a pre-configured SQLite database), so no additional setup is needed as the schema is already in place. If you ever need to reset the database from scratch, the tables are:
users — stores accounts, preferences, and profile images
wardrobe — stores individual clothing items per user
outfits — stores saved outfit combinations with weather context
And to view the schema:
(venv) fytz/$ sqlite3 fytz.db
sqlite3> .schema

Running the App
From inside the fytz/ directory, run:
flask run
And click the link provided. The app will be running locally on port 5000. You should see the fytz login screen. You don’t need to download flask individually, because the requirement.txt or the pip install command from before should have all the required parts.

Creating an Account
For demonstration purposes and to test functionality, you can log into this account:
Username: ay
Password: abc
You can create a new account or “Join fytz.” by either clicking the Register in the top navigation bar or clicking the Register button on the Login page where it says “Don't have an account?”. You enter a new username and a password (which is protected but you can use the eye icon next to each password field to toggle visibility while typing), confirm the password, and click CREATE ACCOUNT. Usernames must be unique, and if the username is already taken, you will see an error message stating “Username already exists”. After registering, you are automatically logged in and redirected to your (empty) fytz closet.
Once you have created your account, you are saved as a new user with a unique user_id, and so when you want to login again, your can simply visit the “Log In” page and type in your username and password, click LOG IN, and you will be taken to your fytz closet.

Features Walkthrough
Adding Clothes to Your Closet
Navigate to your Closet via the top navigation bar where you will see a button Add Item and once you click that button you will be taken to the Upload page. You will see a form where you can do the following:
Choose a category for the clothing you are about to upload — Shirts/tops, Pants/skirts/shorts, Shoes, or Shades(Sunglasses).
Optionally add tags — e.g., "jeans, casual, blue" — to help the recommendation engine find relevant items and you can also search through your closet based on these tags
And finally, upload an image of the clothing item (JPG, PNG, or similar formats).
❗MAKE SURE THE FILE NAME IS DESCRIPTIVE (ex. Your formal dress pants should be named formal_pants). This helps the outfit recommender understand what to recommend based on your STYLE VIBE (Casual, Formal, or Sporty) and also current temperature❗
When you click the save button, ftyz uses an AI background removal tool (rembg) to strip the background from your photo, leaving just the clothing item on a transparent background. This is what makes items look clean when being used on the mannequin and outfit vision board. The processed image is stored in static/uploads/ and the file's name is saved in the database with the associated user’s user_id.
⭐Tip: For best results, photograph clothing on a plain, contrasting background (e.g., a white wall). The AI model handles most backgrounds well, but complex or cluttered backgrounds may produce imperfect cutouts.⭐
If you decide you no longer want to add an item you can always hit the cancel button at the very bottom of the upload panel and you will be taken back to the homepage/closet.

Home Page: The Virtual Closet & Outfit Simulator
The home page is the heart of fytz. It consists of three main panels:
Left panel — Your Closet: Your uploaded items are displayed here in a tabbed grid: All, Shirts, Pants, Shoes, and Shades. The items are shown on multiple pages depending on how many items you have, you can toggle through the pages using the buttons at the bottom of the panel. You can:
Click any item and it will be added to the right panel that serves as an outfit vision board and a mannequin of sorts.
Click on the categories to only show items of that certain category (ex. Click on Shoes to only see pairs of shoes)
Click the heart icon (♡) on a card to mark an item as a favorite (turns ❤️) and you can toggle to only show favorited items.
Use the search bar to filter items by tag keywords (e.g., searching "jeans" will show pants tagged with “jeans” by the user, however, there is no AI/automatic tagging).
Select multiple items using the checkboxes, and either use the Select All button (to select all the items) or the Delete Selected button to delete the selected items in bulk.
Right panel — The Mannequin/Outfit Vision Board: A virtual mannequin displays your selected outfit in real time. The panel is interactive, so you can move each piece of clothing by grabbing, moving, and clicking to place. Each clothing category layers independently and you can have one of each clothing category on your mannequin at all times, so you can mix and match freely. Once you're happy with a look:
Click finalize fit. to save the outfit to your history along with the current weather data (this log can be used later to re-wear the same outfit)
Click clear to reset the mannequin and remove all the items from the mannequin
Grab a piece of clothing and drag it to the bottom right of the panel to the “🗑️” icon to remove that item from the mannequin.
Grab each piece of clothing and reposition them for a better visual fit.
Weather Banner A weather strip in the navigation bar shows your current temperature, forecast, and any active weather alerts. This is pulled live from the National Weather Service and cached in your browser for 30 minutes to avoid unnecessarily frequent API calls.

Outfit Recommendations
Click the “WHAT SHOULD I WEAR?" button (magic wand icon ✨) in the navigation bar in the top left corner at any time. fytz will automatically pick one item from each category — filtered by the current temperature and your saved style preference (as indicated by the weather API and the settings you set) and dress the mannequin with the suggested combination.
Also, you can toggle "Favorites Only" on the home page to limit recommendations to items you have hearted. Or you can use the search bar to search for specific tags you added to the items (ex. Search “summer” and the sundress you tagged with “summer” will show in your closet when you are on the shirts/tops or all tab).
The fytz recommendation follows this logic and filters items by:
Temperature — cold weather (below 45℉) → jackets, boots, and jeans; hot weather  (above 90℉) → shorts, sandals, and shades, normal weather (between 45℉ and 90℉) → random (mainly based on style preference)
Style Vibe — Formal → suits, dress shirts, and boots; Sporty → gym wear, sneakers, and spandex; Casual → jeans, t-shirt, and sandals.

Outfit History
Navigate to History using the nav bar at the top of the page to see every outfit you have saved, displayed in reverse chronological order. Each card shows:
Thumbnail images of the mannequin with the shirt, pants, shoes, and shades worn.
The temperature and weather forecast at the time the outfit was saved.
A heart button to favorite an outfit in your History.
The cards are clickable, so when you click on the card it sends the outfit directly back to the home page mannequin so you can “re-wear” it.
A delete log button to permanently remove the history entry.

Settings
Navigate to Settings (/settings) to manage your account and personalize FYTZ.
Profile Picture — Upload a photo of your face. FYTZ will use it as the profile picture for the profile image in the top right corner at all times, and also as your profile picture on the settings page. You can optionally Remove current photo to reset your profile image back to the default profile image.
Mannequin Head — Separate from your profile picture, you can upload a specific headshot for the mannequin. This replaces the generic mannequin head with your likeness (the generic mannequin head is based on gender).
Personal Info — Set your gender (used for default mannequin head selection), your home address (used to localize weather data), and your style preference (Casual, Formal, or Sporty) which dictates what fytz will recommend for an outfit).
Username & Password — Update your username or change your password. Changing your password requires entering your current password first. You can also use the eye icon to view the password fields as necessary.
Wardrobe Stats — At the bottom of Settings, you can see a summary of how many items you have in your closet, how many outfits you have saved, and a breakdown by category.

Notes & Limitations
Weather is US-only. The app uses the National Weather Service API (api.weather.gov), which only covers US locations. If you set a non-US address, the app will fall back to Cambridge, MA weather data.


Background removal takes a few seconds. The first upload after starting the server will be slowest because rembg loads its AI model into memory. Subsequent uploads are faster.


Image formats. fytz processes all uploads through Pillow and saves them as .png with transparency. The original uploaded file format does not matter.


Deleting wardrobe items uses a soft/hard delete strategy. If an item has been worn in a saved outfit, it is only hidden from your closet (soft delete) so that your history remains accurate. Items that have never been worn are permanently deleted along with their image file.


Sessions are stored on the filesystem in the flask_session/ folder. Clearing this folder will log out all active users.



