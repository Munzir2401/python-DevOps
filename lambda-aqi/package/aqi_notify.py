import requests
import os
import smtplib
from email.message import EmailMessage


def lambda_handler(event, context):

    # Load environment variables
    API_KEY = os.getenv("WAQI_API_KEY")
    EMAIL_ADDRESS = os.getenv("EMAIL_USER")
    EMAIL_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")

    if not API_KEY or not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        return " Missing environment variables!"

    # Build AQI Report
    BASE_URL = "https://api.waqi.info/feed"
    cities = ["sydney", "delhi", "mumbai"]

    report = "Daily Air Quality Report\n\n"

    for city in cities:
        try:
            url = f"{BASE_URL}/{city}/?token={API_KEY}"
            res = requests.get(url, timeout=10).json()

            if res.get("status") == "ok":
                aqi = res["data"].get("aqi", "N/A")
                report += f" {city.title()}: AQI {aqi}\n"
            else:
                report += f" {city.title()}: Data not available\n"

        except Exception as e:
            report += f" {city.title()}: Error fetching data\n"
            print(f"Error for {city}: {e}")

    print(report)

    # ---------- Send Email ----------
    try:
        email = EmailMessage()
        email['Subject'] = "Daily AQI Report"
        email['From'] = EMAIL_ADDRESS
        email['To'] = EMAIL_ADDRESS
        email.set_content(report)

        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.starttls()
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(email)

        print(" Email sent successfully!")
        return " Lambda execution successful!"

    except Exception as mail_error:
        print(" Email failed:", mail_error)
        return f" Email failed: {mail_error}"

