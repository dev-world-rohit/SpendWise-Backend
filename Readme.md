# SpendWise Backend
`SpendWise` is a advance tool for handling the modern day expenses by providing the functionality to store, retrieve, and analyze the 
expenses.

## Backend Functionalities
1. User Authentication using JWT
2. Expense Management Operations
3. Advance Reminder System
4. Mailer System

## Application Setup

This repository contains a Flask application that includes various routes and functionalities. Follow the instructions below to set up the environment and run the application.

## Prerequisites

- Python 3.x installed on your system
- `pip` package manager

## Getting Started

### 1. Clone the Repository

Clone this repository to your local machine:

```bash
git clone <repository_url>
cd <repository_name>
```

### 2. Set Up Virtual Environment

### For Windows:

Open a command prompt and execute the following commands to create and activate a virtual environment:

```bash
python -m venv venv
venv\Scripts\activate
```

### For macOS/Linux:
Open a terminal and execute the following commands to create and activate a virtual environment:
```commandline
python3 -m venv venv
source venv/bin/activate
```

### 3. Installing Packages

While in the activated virtual environment, install the required packages listed in requirements.txt:

```bash
pip install -r requirements.txt
```

### 4. Creating `.env` File

Create the .env  file using the command prompt in the main directory.

### For Windows:
Create the .env file by using the following command:

```commandline
ni .env
```

### For macOS/Linux:

Create the .env file using the following commands:

```commandline
nano .env
```

### 5. Setup `.env` File
Write down email address and password of the email to send the mail using the SMTP(Simple Mail Transfer Protocol).

```commandline
EMAIL = "your_email_address@gmail.com"
PASSWORD = "password"
```

### 6. Set Up Environment Variables

### For Windows:

Set the Flask app environment variables to specify the application entry point (app.py) and environment (development):
```bash
set FLASK_APP=app.py
set FLASK_ENV=development 
```

### For macOS/Linux:

Set the Flask app environment variables using the following commands:

```commandline
export FLASK_APP=app.py
export FLASK_ENV=development
```

### 7. Run the Application

Start the Flask application by running the following command:

```commandline
flask run
```

The application will start running on the url http://localhost:5000/.

---

## Routes
### Login Route
#### 1. Login
**URL:** /login

**Method:** POST

**Request Body**
```commandline
{
"email": "abc@gmail.com",
"password": "123abc@"
}
```

**Response**
```commandline
{
"access_token": "sshsodfh45907fgkgpfg498t9rfg",
"email": "abc@gmail.com"
}
```

---

### Registration Route
#### 1. OPT
**URL:** /opt

**Method:** POST

**Request Body**
```commandline
{
"email": "abc@gmail.com"
}
```

**Response**
```commandline
{
"success"
}
```

---


#### 2. Registration
**URL:** /signup

**Method:** POST

**Request Body**
```commandline
{
"email": "abc@gmail.com"
"phone": "1234567890",
"name": "abc",
"password": "123abc@"
"otp": 123456
}
```

**Response**
```commandline
{
"access_token": "sshsodfh45907fgkgpfg498t9rfg",
"email": "abc@gmail.com"
}
```

---


### DashBoard Routes
#### 1. Getting UserName
**URL:** /name

**Method:** GET

**Request Body**
```commandline
{}
```

**Response**
```commandline
{
    "name": "abc"
}
```

---


#### 2. Getting Current Month and Current Year Total Expenses
**URL:** /total_expense

**Method:** GET

**Request Body**
```commandline
{}
```

**Response**
```commandline
{
    "monthly": 44.0,
    "yearly": 78.0
}
```

---


#### 3. Getting Total of Tag Based Categorization of Expenses
**URL:** /tag_based_expenses

**Method:** GET

**Request Body**
```commandline
{}
```

---


**Response**
```commandline
{
    "comparison": {
        "Debt": "no change",
        "Entertainment": "no change",
        "Food": "increase",
        "Health Care": "no change",
        "Housing": "no change",
        "Lend": "no change",
        "Miscellaneous": "no change",
        "Personal Care": "no change",
        "Transportation": "increase"
    },
    "current_month_expenses": {
        "Debt": 0,
        "Entertainment": 0,
        "Food": 10.0,
        "Health Care": 0,
        "Housing": 0,
        "Lend": 0,
        "Miscellaneous": 0,
        "Personal Care": 0,
        "Transportation": 34.0
    },
    "previous_month_expenses": {
        "Debt": 0,
        "Entertainment": 0,
        "Food": 0,
        "Health Care": 0,
        "Housing": 0,
        "Lend": 0,
        "Miscellaneous": 0,
        "Personal Care": 0,
        "Transportation": 0
    }
}
```

---


#### 4. Getting Upcoming 3 Reminders
**URL:** /get_reminder_dashboard

**Method:** GET

**Request Body**
```commandline
{}
```

**Response**
```commandline
[
    {
        "date": "2024-05-10",
        "description": "Udemy Subscription",
        "id": "478c52ff0f51480d9f6d4f5fdb10d133",
        "price": 700.0,
        "reminder_name": "Udemy",
        "repeat": "Every Month"
    },
    {
        "date": "2024-05-10",
        "description": "Pay the electricity bill before the 10th of the month.",
        "id": "318a2d1874774db4a358c3e8d4e1ad2a",
        "price": 100.0,
        "reminder_name": "Electricity Bill",
        "repeat": "Every Month"
    },
    {
        "date": "2024-05-18",
        "description": "Pay the electricity bill before the 10th of the month.",
        "id": "3ae4d731a4074559b2bfee4933d633e2",
        "price": 100.0,
        "reminder_name": "Electricity Bill",
        "repeat": "Every Month"
    }
]
```

---


#### 5. Adding Expenses
**URL:** /add_expense

**Method:** POST

**Request Body**
```commandline
{
    "expense_name": "abx",
    "price": 34,
    "tag": "Housing",
    "date":"2024-02-24",
    "description":"hello"
}
```

**Response**
```commandline
{
    "message": "Expense added successfully"
}
```

---


### Analysis Route
#### 1. Getting Tag Based Categorization Expenses of Current Month
**URL:** /tag_based_expenses_analysis

**Method:** GET

**Request Body**
```commandline
{
}
```

**Response**
```commandline
{
    "current_month_expenses": {
        "Debt": 0,
        "Entertainment": 0,
        "Food": 10.0,
        "Health Care": 0,
        "Housing": 0,
        "Lend": 0,
        "Miscellaneous": 0,
        "Personal Care": 0,
        "Transportation": 34.0
    }
}
```

#### 2. Getting the Month wise Expense of All months of Current Year
**URL:** /expenses_by_month

**Method:** GET

**Request Body**
```commandline
{
}
```

**Response**
```commandline
{
    "April": 0,
    "August": 0,
    "December": 0,
    "February": 34.0,
    "January": 0,
    "July": 0,
    "June": 0,
    "March": 0,
    "May": 44.0,
    "November": 0,
    "October": 0,
    "September": 0
}
```

---


#### 3. Getting Monthly Expenses for the Current year and Previous year
**URL:** /monthly_expenses

**Method:** GET

**Request Body**
```commandline
{
}
```

**Response**
```commandline
{
    "current_year": {
        "April": 0,
        "August": 0,
        "December": 0,
        "February": 34.0,
        "January": 0,
        "July": 0,
        "June": 0,
        "March": 0,
        "May": 44.0,
        "November": 0,
        "October": 0,
        "September": 0
    },
    "previous_year": {
        "April": 0,
        "August": 0,
        "December": 0,
        "February": 0,
        "January": 0,
        "July": 0,
        "June": 0,
        "March": 0,
        "May": 0,
        "November": 0,
        "October": 0,
        "September": 0
    }
}
```

---


### Reminder Routes
#### 1. Adding Simple Reminders to Ourselves
**URL:** /reminders

**Method:** POST

**Request Body**
```commandline
{
        "date": "2024-05-18",
        "description": "Pay the electricity bill before the 10th of the month.",
        "id": "3ae4d731a4074559b2bfee4933d633e2",
        "price": 100.0,
        "reminder_name": "Electricity Bill",
        "repeat": "Every Month"
}
```

---


**Response**
```commandline
[
    {
        "date": "2024-05-10",
        "description": "Pay the electricity bill before the 10th of the month.",
        "id": "318a2d1874774db4a358c3e8d4e1ad2a",
        "price": 100.0,
        "reminder_name": "Electricity Bill",
        "repeat": "Every Month"
    },
    {
        "date": "2024-05-18",
        "description": "Pay the electricity bill before the 10th of the month.",
        "id": "3ae4d731a4074559b2bfee4933d633e2",
        "price": 100.0,
        "reminder_name": "Electricity Bill",
        "repeat": "Every Month"
    }
]
```

---


#### 1. Getting All Reminders
**URL:** /get_reminders

**Method:** GET

**Request Body**
```commandline
{
}
```

**Response**
```commandline
[
    {
        "date": "2024-05-10",
        "description": "Pay the electricity bill before the 10th of the month.",
        "id": "318a2d1874774db4a358c3e8d4e1ad2a",
        "price": 100.0,
        "reminder_name": "Electricity Bill",
        "repeat": "Every Month"
    },
    {
        "date": "2024-05-18",
        "description": "Pay the electricity bill before the 10th of the month.",
        "id": "3ae4d731a4074559b2bfee4933d633e2",
        "price": 100.0,
        "reminder_name": "Electricity Bill",
        "repeat": "Every Month"
    }
]
```

---


#### 1. Deleting Reminder
**URL:** /delete_reminders

**Method:** POST

**Request Body**
```commandline
{
    "id":"3ae4d731a4074559b2bfee4933d633e2"
}
```

**Response**
```commandline
{
    "message": "Reminder deleted successfully"
}
```
