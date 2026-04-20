# ISL Connect v2 — Complete Setup, Run & Training Guide

---

## PROJECT FILE STRUCTURE

```
PD/
├── app.py                  ← Flask backend (all routes + logic)
├── train_model.py          ← ML training script
├── users.json              ← User database (auto-created)
├── requirements.txt        ← All pip dependencies
├── SETUP_GUIDE.md          ← This file
│
├── templates/
│   ├── login.html          ← Login page
│   ├── signup.html         ← Signup (with email field)
│   ├── verify_otp.html     ← OTP verification page
│   ├── admin.html          ← Admin panel (approve users + SMTP)
│   ├── home.html           ← Main dashboard (contacts/fav/emergency)
│   ├── settings.html       ← Settings page
│   └── call.html           ← Call screen (STT + TTS + ISL Signs)
│
├── static/
│   ├── css/style.css
│   ├── js/main.js
│   └── signs/
│       ├── alphabet/       ← Put a.jpg, b.jpg ... z.jpg here
│       │                      (auto-filled by train_model.py)
│       └── words/          ← Put hello.jpg, help.jpg etc. here
│
├── model/                  ← Created after training
│   ├── isl_model.h5        ← Trained model weights
│   ├── class_names.json    ← Class labels
│   ├── model_info.json     ← Accuracy report
│   └── training_plot.png   ← Accuracy/Loss graphs
│
└── dataset/                ← You create this (Kaggle download)
    ├── train/
    │   ├── A/  (images of hand sign A)
    │   ├── B/
    │   └── ... Z/
    └── test/
        ├── A/
        └── ... Z/
```

---

## PART 1: RUN THE APP (No ML needed)

### Step 1: Open VS Code
- Open VS Code → File → Open Folder → Select the "PD" folder

### Step 2: Open Terminal
- Press `Ctrl + `` ` (backtick) to open terminal

### Step 3: Install Flask (minimum requirement)
```bash
pip install flask
```

### Step 4: Run the App
```bash
python app.py
```

You'll see:
```
🚀 ISL Connect v2 running!
🌐 http://127.0.0.1:5000
🔑 Admin: admin / admin123
```

### Step 5: Open Browser
Open **Google Chrome** → go to: `http://127.0.0.1:5000`

---

## PART 2: FIRST TIME USAGE FLOW

### A. Admin Login
- User ID: `admin`
- Password: `admin123`
- Go to Admin Panel → configure SMTP (optional, for real OTP emails)

### B. Create New User
1. Click "Sign Up" on login page
2. Fill in: Name, User ID, Email, Password
3. Click "Send OTP & Continue"
4. **If SMTP not configured**: OTP prints in terminal — check VS Code terminal!
   Look for: `📧 [DEV MODE] OTP for user@email.com is: 123456`
5. Enter OTP on the verification page
6. Account created (pending admin approval)

### C. Approve New User
1. Login as admin
2. Go to Admin Panel → click "✓ Approve"

### D. Login as New User
- Use your User ID and password

### E. Test Call Features
1. Go to Contacts → Search → add another user
2. Click "📞 Call"
3. On call screen:
   - 🎙️ Speech-to-Text: Click mic, speak → text appears (Chrome only)
   - 🔊 Text-to-Speech: Type text → click "Speak Aloud"
   - 🤟 ISL Signs: Type any word/sentence → click "Convert 🤟"
     - Signs appear as hand gesture SVGs (or images if dataset is loaded)

---

## PART 3: SETUP EMAIL OTP (Gmail)

### In Admin Panel → Email/SMTP Settings:
1. Enter your Gmail address
2. Enter your Gmail **App Password** (NOT your regular password)

### How to get Gmail App Password:
1. Go to Gmail → click your profile → "Manage your Google Account"
2. Go to: Security tab
3. Enable "2-Step Verification" if not already on
4. Search for "App passwords" in the search bar
5. Create new → Select "Mail" and "Windows Computer"
6. Click Generate → copy the 16-character password
7. Paste it in Admin Panel → SMTP settings → Save

---

## PART 4: TRAIN THE ML MODEL

### Step 1: Install ML libraries
```bash
pip install tensorflow numpy matplotlib pillow
```

### Step 2: Download ISL Dataset from Kaggle

**Option A (Recommended):**
1. Go to: https://www.kaggle.com/datasets/prathumarikeri/indian-sign-language-isl
2. Create free Kaggle account if needed
3. Click "Download" button
4. Extract the ZIP file

**Option B:**
1. Go to: https://www.kaggle.com/datasets/lexset/synthetic-asl-alphabet
2. Download and extract

### Step 3: Place Dataset in Project

After extracting, you'll see folders like A/, B/, C/ ... Z/

Copy them into your project like this:
```
PD/
└── dataset/
    └── train/
        ├── A/
        │   ├── img_001.jpg
        │   ├── img_002.jpg
        │   └── ...
        ├── B/
        ├── C/
        └── ... Z/
```

Optionally create test set:
```
PD/
└── dataset/
    └── test/
        ├── A/
        ├── B/
        └── ... Z/
```

### Step 4: Run Training
```bash
python train_model.py
```

Training will:
- Load images from dataset/train/
- Train a CNN model for ~15 epochs
- Save best model to model/isl_model.h5
- Copy one image per letter to static/signs/alphabet/
- Show accuracy graph

Training takes ~5-30 minutes depending on dataset size and your PC.

### Step 5: After Training
Run the app normally:
```bash
python app.py
```

Now the call screen will show **real hand gesture images** from the dataset instead of SVG drawings!

---

## PART 5: ADD WORD IMAGES (Optional)

For word signs (hello, help, thank you, etc.):
1. Find ISL word gesture images online
2. Name them: `hello.jpg`, `help.jpg`, `thank_you.jpg`, `yes.jpg`, `no.jpg`, etc.
3. Place in: `PD/static/signs/words/`

---

## TROUBLESHOOTING

| Problem | Solution |
|---------|----------|
| `TemplateNotFound: contacts.html` | ✅ Fixed in v2! contacts are in home.html |
| OTP not received by email | Check terminal for DEV MODE OTP, or set up Gmail SMTP in Admin |
| Speech recognition not working | Must use Google Chrome; allow microphone access |
| `ModuleNotFoundError: flask` | `pip install flask` |
| `ModuleNotFoundError: tensorflow` | `pip install tensorflow` |
| Port 5000 in use | Change to `app.run(port=5001)` in app.py, then open :5001 |
| Training fails: dataset not found | Follow Part 4 exactly, check folder names are A/, B/ (capital) |

---

## QUICK COMMANDS SUMMARY

```bash
# Install everything
pip install flask tensorflow numpy matplotlib pillow

# Run the web app
python app.py

# Train the ISL model (after dataset setup)
python train_model.py

# Open in browser
http://127.0.0.1:5000
```

---

## FEATURES CHECKLIST

- ✅ Login / Signup with email
- ✅ OTP email verification (1 email = 1 account)
- ✅ Admin approval system
- ✅ Admin SMTP settings panel
- ✅ Contacts: Add / Remove contacts
- ✅ Favourites: Star contacts
- ✅ Emergency contacts
- ✅ Search by User ID
- ✅ Settings page (profile, password, appearance)
- ✅ Call simulation (2.5s ring → connected)
- ✅ Speech-to-Text (Chrome Web Speech API)
- ✅ Text-to-Speech (SpeechSynthesis API)
- ✅ Text-to-ISL Signs (letter-by-letter SVG hand gestures)
- ✅ Real dataset images when available
- ✅ NLP pipeline (lowercase, split, trim)
- ✅ ML training script for Kaggle dataset