# Lambda AQI Notification

This project automates the process of fetching Air Quality Index (AQI) data for selected cities using the World Air Quality Index (WAQI) API and sends the report via email at scheduled intervals. The script runs as an AWS Lambda function and can also be executed manually from a local or server environment.

---

## Project Overview

The purpose of this project is to demonstrate environment variable management, API integration, and event-based automation using AWS Lambda and EventBridge.

**Core features include:**
- Fetching AQI data for multiple cities via the WAQI API.
- Parsing and formatting the API response into a clean report.
- Sending the report as an email using SMTP (Gmail in this case).
- Automating execution using AWS EventBridge (cron schedule).

---

## Directory Structure

```
lambda-aqi/
├── aqi_notify.py # Main Lambda script
├── requirements.txt # Python dependencies
└── README.md # Project documentation
└── lambda-aqi.zip # The code to be uploaded to lambda as .zip
```


---

## Prerequisites

1. **AWS Account**  
   - Required to create and configure Lambda and EventBridge.

2. **Environment Variables**  
   Configure the following environment variables in your Lambda function or `.env` file (if running locally):

   | Variable Name         | Description |
   |------------------------|-------------|
   | `WAQI_API_KEY`         | Your API token from [WAQI API](https://aqicn.org/api/) |
   | `EMAIL_USER`           | Sender email address |
   | `EMAIL_APP_PASSWORD`   | Application-specific password for the sender email |

3. **Libraries**
   - Python 3.9 or higher
   - Install required dependencies:
     ```bash
     pip install -r requirements.txt
     ```

---

## How It Works

1. The script retrieves the AQI data for predefined cities (`Sydney`, `Delhi`, and `Mumbai`) using the WAQI API.
2. The data is parsed and formatted into a readable report.
3. An email is sent to the configured recipient address with the AQI summary.
4. In AWS Lambda, the function is triggered automatically based on the EventBridge schedule.

---

## Example Output

**Email Subject:** `Daily AQI Report`

**Email Body:**

 Daily Air Quality Report

 Sydney: AQI 21
 Delhi: AQI 229
 Mumbai: AQI 122


---

## Deployment Instructions

```
### Step 1: Package the Code
Create a zip file for Lambda deployment:

zip -r lambda_aqi.zip aqi_notify.py requirements.txt

Step 2: Upload to AWS Lambda

Go to AWS Lambda Console → Create Function

Choose Python 3.9 as the runtime

Upload the lambda_aqi.zip package under Code source

Configure handler:
aqi_notify.lambda_handler

Add environment variables under Configuration → Environment Variables

Step 3: Add Trigger with EventBridge

Create a rule under EventBridge → Rules → Create Rule:

Choose Schedule pattern

Use cron syntax to set run times (example: cron(0 8,13,18,23 * * ? *))

Select your Lambda function as the target. 
```

Local Testing

To test locally:

```bash
python3 aqi_notify.py

```

Expected console output:

 Daily Air Quality Report

 Sydney: AQI 21
 Delhi: AQI 229
 Mumbai: AQI 122

 Email sent successfully!


## Maintenance and Improvements

Extend city list or make it configurable through environment variables.

Add error handling and retry logic for API failures.

Log outputs to CloudWatch for monitoring.

Integrate with additional channels (e.g., Slack notifications). 
