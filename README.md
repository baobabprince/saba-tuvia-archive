📜 Yad Vashem Document Processor (AI-Powered)
מערכת אוטומטית מבוססת Gemini 3.0 Flash לעיבוד, תמלול ותרגום מסמכים היסטוריים מארכיון יד ושם. המערכת רצה באופן יומי, מושכת תמונות ישירות מהשרת, ומפיקה פלט הכולל תמלול מקורי ותרגום לעברית.

🚀 תכונות עיקריות (Speed Optimizations)
Zero-Storage Build: הפרויקט לא שומר תמונות ב-Git. התמונות מורדות בזמן אמת לזיכרון ה-Runner, מה ששומר על Repository קל ו-Checkout מהיר (פחות מ-2 שניות).

Parallel Downloading: שימוש ב-ThreadPoolExecutor להורדת תמונות במקביל, מה שמקצר את זמן הכנת הנתונים ב-80%.

Batch Processing: עיבוד של מספר מסמכים בבת אחת מול ה-API של Google GenAI לחיסכון בזמן תקשורת.

Incremental Updates: מנגנון מעקב (processed_files.txt) המבטיח שכל תמונה תעובד פעם אחת בלבד.

🛠 טכנולוגיות
Language: Python 3.11

AI Model: Gemini 2.0 Flash (via google-genai)

Automation: GitHub Actions

Data Source: Yad Vashem Online Assets

📂 מבנה הפרויקט
script.py: הסקריפט המרכזי האחראי על ההורדה, הפנייה ל-AI ושמירת התוצאות.

processed_files.txt: קובץ מעקב המכיל רשימת קבצים שכבר עובדו.

outputs/: תיקייה המכילה את קבצי הטקסט המעובדים (תמלול + תרגום + URL).

.github/workflows/main.yml: הגדרות האוטומציה להרצה יומית.

⚙️ הגדרות והרצה
1. דרישות מוקדמות
יש להגדיר Secret ב-GitHub בשם GEMINI_API_KEY עם מפתח ה-API שלך מ-Google AI Studio.

2. הרצה מקומית
אם ברצונך להריץ את הסקריפט ידנית על המחשב:

Bash

# התקנת ספריות
pip install google-genai requests

# הגדרת משתנה סביבה (בטרמינל)
export GEMINI_API_KEY="your_api_key_here"

# הרצה
python script.py
📝 פורמט הפלט
כל קובץ בתיקיית outputs ייראה כך:

Markdown

Source URL for the following image: https://assets.yadvashem.org/.../00001.JPG
### Transcription (Original)
[Original Text from Image]

### Translation (Hebrew)
[Hebrew Translation]
---
📊 סטטוס הפרויקט
הפרויקט מוגדר לעבד 4 תמונות בכל הרצה (Batch Size), ורץ באופן אוטומטי פעם ביום עד להשלמת כל 700 המסמכים בסדרה.
