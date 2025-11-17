from dotenv import load_dotenv
import os

load_dotenv()

print("ID =", os.getenv("GOOGLE_CLIENT_ID"))
print("SECRET =", os.getenv("GOOGLE_CLIENT_SECRET"))
