import json
import random
import time
from calendar import month_name
from flask import Flask, request, jsonify
from datetime import datetime, timedelta, timezone
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, unset_jwt_cookies, jwt_required, \
    JWTManager
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from sqlalchemy import extract
from sqlalchemy import func
from apscheduler.schedulers.background import BackgroundScheduler
from models import db, User, OtpRequests, Expense, Reminder, RemindFriend, ErrorSendingMail
from email_sender import send_mail
from sqlalchemy.exc import IntegrityError
from email_message_generator import *

app = Flask(__name__)
CORS(app, origins='*')

app.config['SECRET_KEY'] = 'camcorders-endian'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=100)
jwt = JWTManager(app)

SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = True

bcrypt = Bcrypt(app)
db.init_app(app)

with app.app_context():
    db.create_all()


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route('/login', methods=["POST"])
def create_token():
    email = request.json["email"]
    password = request.json["password"]

    user = User.query.filter_by(email=email).first()

    if user:
        if bcrypt.check_password_hash(user.password, password):
            access_token = create_access_token(identity=email)

            return jsonify({
                "email": email,
                "access_token": access_token
            })
        else:
            return jsonify({"error": "Incorrect Password."})
    else:
        return jsonify({"error": "Email does not exits."})


def send_mail_person(email, name, reciver, price, description):
    message = person_reminder_message(name, reciver, price, description)
    send_mail(email, message)


def send_otp(email):
    otp = random.randint(100000, 999999)
    message = otp_generator(otp)
    send_mail(email, message)
    current_time = int(time.time())
    presave = OtpRequests(email=email, otp=otp, time=current_time)
    db.session.add(presave)
    db.session.commit()


@app.route("/otp", methods=['POST'])
def generate_otp():
    email = request.json["email"]

    try:
        otp_request = OtpRequests.query.filter_by(email=email).first()
        if otp_request:
            raise ValueError("OTP already sent.")
    except (TypeError, ValueError) as e:
        return jsonify({"error": str(e)})

    user = User.query.filter_by(email=email).first()
    if user:
        return jsonify("User already exists")
    else:
        try:
            send_otp(email)
            return jsonify("success")
        except:
            return jsonify({"error": "Error occurred. Please try again later."})


@app.route("/signup", methods=["POST"])
def signup():
    name = request.json['name']
    phone = request.json['phone']
    email = request.json["email"]
    password = request.json['password']
    otp = request.json["otp"]
    current_time = int(time.time())
    otp_request = OtpRequests.query.filter_by(email=email).first()
    if otp_request:
        if str(otp) == str(otp_request.otp):
            if current_time - otp_request.time < 600:
                hashed_password = bcrypt.generate_password_hash(password)
                new_user = User(email=email, name=name,
                                phone=phone, password=hashed_password)
                db.session.add(new_user)
                db.session.commit()
                access_token = create_access_token(identity=email)

                otp_request = OtpRequests.query.filter_by(email=email).first()

                if otp_request:
                    db.session.delete(otp_request)
                    db.session.commit()

                return jsonify({
                    "email": email,
                    "access_token": access_token
                })

            else:
                otp_request = OtpRequests.query.filter_by(email=email).first()

                if otp_request:
                    db.session.delete(otp_request)
                    db.session.commit()

                send_otp(email)
                return jsonify({"error": "OTP expired. OTP Sent again."})
        else:
            return jsonify({"error": "Invalid OTP"})

    else:
        return jsonify({"error": "No User found."})


@app.after_request
def refresh_expiring_jwts(response):
    try:
        exp_timestamp = get_jwt()["exp"]
        now = datetime.now(timezone.utc)
        target_timestamp = datetime.timestamp(now + timedelta(minutes=30))
        if target_timestamp > exp_timestamp:
            access_token = create_access_token(identity=get_jwt_identity())
            data = response.get_json()
            if type(data) is dict:
                data["access_token"] = access_token
                response.data = json.dumps(data)
        return response
    except (RuntimeError, KeyError):
        return response


@app.route("/logout", methods=["POST"])
def logout():
    response = jsonify({"msg": "logout successful"})
    unset_jwt_cookies(response)
    return response


# Forget Password
@app.route("/forget_password_otp", methods=['POST'])
def forget_generate_otp():
    email = request.json["email"]
    current_time = int(time.time())
    try:
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"})

        otp_request = OtpRequests.query.filter_by(email=email).first()
        if otp_request:
            if current_time - otp_request.time < 600:
                return jsonify({"error": "Otp already sent."})
            else:
                if otp_request:
                    db.session.delete(otp_request)
                    db.session.commit()

        try:
            send_otp(email)
            return jsonify("success")
        except:
            return jsonify({"error": "Error occurred. Please try again later."})

    except:
        return jsonify({"error": "Error occured"})


@app.route("/forget_password_login", methods=["POST"])
def forget_password_login():
    email = request.json["email"]
    password = request.json['password']
    otp = request.json["otp"]
    current_time = int(time.time())
    otp_request = OtpRequests.query.filter_by(email=email).first()
    if otp_request:
        if str(otp) == str(otp_request.otp):
            if current_time - otp_request.time < 600:
                hashed_password = bcrypt.generate_password_hash(password)
                user = User.query.filter_by(email=email).first()
                user.password = hashed_password
                db.session.commit()
                access_token = create_access_token(identity=email)

                otp_request = OtpRequests.query.filter_by(email=email).first()

                if otp_request:
                    db.session.delete(otp_request)
                    db.session.commit()

                return jsonify({
                    "email": email,
                    "access_token": access_token
                })

            else:
                otp_request = OtpRequests.query.filter_by(email=email).first()

                if otp_request:
                    db.session.delete(otp_request)
                    db.session.commit()

                send_otp(email)
                return jsonify({"error": "OTP expired. OTP Sent again."})
        else:
            return jsonify({"error": "Invalid OTP"})
    else:
        return jsonify({"error": "No User found."})


@app.route("/delete_account", methods=["GET"])
@jwt_required()
def delete_account():
    try:
        email = get_jwt_identity()
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        expenses = Expense.query.filter_by(email=user.email).all()
        for expense in expenses:
            db.session.delete(expense)

        reminders = Reminder.query.filter_by(email=user.email).all()
        for reminder in reminders:
            db.session.delete(reminder)

        db.session.delete(user)
        db.session.commit()

        return jsonify({"message": "Account Deleted Successfully."})

    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"error": "Database Integrity Error"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# @app.route('/<getemail>')
# @jwt_required()
# def my_profile(getemail):
#     if not getemail:
#         return jsonify({"error": "Unauthorized Access"}), 401
#
#     user = User.query.filter_by(email=getemail).first()
#     response_body = {
#         "id": user.id,
#         "name": user.name,
#         "email": user.email,
#     }
#
#     return response_body


# Dashboard Routes-----------------------------------------------------------------------------#
# Get Error Log is the Reminder for Friend Failed
@app.route("/get_failed_emails", methods=["GET"])
@jwt_required()
def get_failed_emails():
    try:
        email = get_jwt_identity()
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        reminders = ErrorSendingMail.query.filter_by(email=email).all()
        if reminders:
            delete_reminders = []
            error_reminders = ""
            for reminder in reminders:
                error_reminders += reminder.reminder_name + ", "
                delete_reminders.append(reminder)

            for reminder in delete_reminders:
                db.session.delete(reminder)

            return jsonify({"error_logs": error_reminders}), 200
        return jsonify({"message": "Nothing to Share"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Getting name of the User
@app.route("/name", methods=["GET"])
@jwt_required()
def get_name():
    try:
        email = get_jwt_identity()
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        name = user.name.split(" ")[0]
        return jsonify({"name": str(name)}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Get the total Expense of the month and year
@app.route("/total_expense", methods=["GET"])
@jwt_required()
def get_total_expense():
    try:
        email = get_jwt_identity()
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        current_month_expense = db.session.query(func.sum(Expense.price)).filter(
            extract('year', Expense.date) == datetime.utcnow().year,
            extract('month', Expense.date) == datetime.utcnow().month,
            Expense.email == email
        ).scalar() or 0

        current_year_expense = db.session.query(func.sum(Expense.price)).filter(
            extract('year', Expense.date) == datetime.utcnow().year,
            Expense.email == email
        ).scalar() or 0

        return jsonify({
            "monthly": current_month_expense,
            "yearly": current_year_expense
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Get the tag based Expenses
# Define the tags
tags = [
    "Housing",
    "Transportation",
    "Food",
    "Health Care",
    "Personal Care",
    "Debt",
    "Entertainment",
    "Lend",
    "Miscellaneous"
]


@app.route("/tag_based_expenses", methods=["GET"])
@jwt_required()
def get_tag_based_expenses():
    try:
        email = get_jwt_identity()
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Get current month and year
        current_month = datetime.utcnow().month
        current_year = datetime.utcnow().year

        # Get current month expenses for each tag
        current_month_expenses = {}
        for tag in tags:
            tag_expense = db.session.query(func.sum(Expense.price)).filter(
                extract('year', Expense.date) == current_year,
                extract('month', Expense.date) == current_month,
                Expense.tag == tag,
                Expense.email == email
            ).scalar() or 0
            current_month_expenses[tag] = tag_expense

        # Get previous month expenses for each tag
        previous_month = current_month - 1 if current_month > 1 else 12
        previous_year = current_year if current_month > 1 else current_year - 1
        previous_month_expenses = {}
        for tag in tags:
            tag_expense = db.session.query(func.sum(Expense.price)).filter(
                extract('year', Expense.date) == previous_year,
                extract('month', Expense.date) == previous_month,
                Expense.tag == tag,
                Expense.email == email
            ).scalar() or 0
            previous_month_expenses[tag] = tag_expense

        # Calculate increase/decrease for each tag
        comparison = {}
        for tag in tags:
            if current_month_expenses[tag] > previous_month_expenses[tag]:
                comparison[tag] = "increase"
            elif current_month_expenses[tag] < previous_month_expenses[tag]:
                comparison[tag] = "decrease"
            else:
                comparison[tag] = "no change"

        return jsonify({
            "current_month_expenses": current_month_expenses,
            "previous_month_expenses": previous_month_expenses,
            "comparison": comparison
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/get_reminder_dashboard", methods=["GET"])
@jwt_required()
def get_upcoming_reminders():
    try:
        email = get_jwt_identity()
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        current_datetime = datetime.utcnow()

        upcoming_reminders = (
            Reminder.query
            .filter(Reminder.date >= current_datetime, Reminder.email == email)
            .order_by(Reminder.date.asc())
            .limit(3)
            .all()
        )

        upcoming_reminders_data = []
        for reminder in upcoming_reminders:
            reminder_data = {
                "id": reminder.id,
                "date": reminder.date.strftime("%Y-%m-%d"),
                "reminder_name": reminder.reminder_name,
                "description": reminder.description,
                "price": reminder.price,
                "repeat": reminder.repeat_type
            }
            upcoming_reminders_data.append(reminder_data)

        return jsonify({"data": upcoming_reminders_data, "length": len(upcoming_reminders_data)})

    except Exception as e:
        return {"error": str(e)}


# Functionality to Add Expense
@app.route("/add_expense", methods=["POST"])
@jwt_required()
def add_expense():
    try:
        email = get_jwt_identity()
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        expense_data = request.json
        expense_name = expense_data.get("expense_name")
        price = expense_data.get("price")
        tag = expense_data.get("tag")
        date = expense_data.get("date")
        print(date)
        description = expense_data.get("description")

        # Validate the required fields
        if not expense_name or not price or not tag or not date:
            return jsonify({"error": "Missing required fields"}), 400

        try:
            date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Invalid date format"}), 400

        new_expense = Expense(
            email=email,
            expense_name=expense_name,
            price=price,
            tag=tag,
            date=date,
            description=description
        )
        db.session.add(new_expense)
        db.session.commit()

        return jsonify({"message": "Expense added successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/expenses", methods=["GET"])
@jwt_required()
def get_all_expenses():
    try:
        email = get_jwt_identity()
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        expenses = Expense.query.filter_by(email=email).all()
        if not expenses:
            return jsonify({"message": "No expenses found"}), 200

        # Serialize the expenses data
        serialized_expenses = []
        for expense in expenses:
            serialized_expense = {
                "id": expense.id,
                "expense_name": expense.expense_name,
                "price": expense.price,
                "tag": expense.tag,
                "description": expense.description,
                "date": expense.date.strftime("%Y-%m-%d") if expense.date else None
            }
            serialized_expenses.append(serialized_expense)

        return jsonify(serialized_expenses), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Analysis Page---------------------------------------------------------------#
# Getting the Tag Based Data
@app.route("/tag_based_expenses_analysis", methods=["GET"])
@jwt_required()
def get_tag_based_expenses_analysis():
    try:
        email = get_jwt_identity()
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        current_month = datetime.utcnow().month
        current_year = datetime.utcnow().year

        current_month_expenses = {}
        for tag in tags:
            tag_expense = db.session.query(func.sum(Expense.price)).filter(
                extract('year', Expense.date) == current_year,
                extract('month', Expense.date) == current_month,
                Expense.tag == tag,
                Expense.email == email
            ).scalar() or 0
            current_month_expenses[tag] = tag_expense

        return jsonify({
            "current_month_expenses": current_month_expenses
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Getting the Month wise Expense
def get_expenses_by_month(email):
    try:
        current_year = datetime.utcnow().year

        months = range(1, 13)
        expenses_by_month = {month_name[month]: 0 for month in months}

        expenses = (
            db.session.query(func.sum(Expense.price), extract('month', Expense.date))
            .filter(extract('year', Expense.date) == current_year, Expense.email == email)
            .group_by(extract('month', Expense.date))
            .all()
        )

        for expense_sum, month_number in expenses:
            month_name_str = month_name[month_number]
            expenses_by_month[month_name_str] = float(expense_sum) if expense_sum else 0

        response_data = expenses_by_month

        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Define a route to handle the expenses by month request
@app.route("/expenses_by_month", methods=["GET"])
@jwt_required()
def expenses_by_month_route():
    try:
        email = get_jwt_identity()
        if not email:
            return jsonify({"error": "Unauthorized"}), 401

        return get_expenses_by_month(email)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Route to get monthly expenses for the current year and previous year
def get_monthly_expenses_for_year(year):
    monthly_expenses = {}
    for month_number in range(1, 13):
        month_name_str = month_name[month_number]
        total_expense = calculate_total_expense_for_month(year, month_number)
        monthly_expenses[month_name_str] = total_expense

    return monthly_expenses


def calculate_total_expense_for_month(year, month):
    total_expense = db.session.query(func.sum(Expense.price)).filter(
        extract('year', Expense.date) == year,
        extract('month', Expense.date) == month
    ).scalar() or 0

    return total_expense


@app.route("/monthly_expenses", methods=["GET"])
def get_monthly_expenses():
    try:
        current_year = datetime.utcnow().year
        previous_year = current_year - 1

        current_year_expenses = get_monthly_expenses_for_year(current_year)
        previous_year_expenses = get_monthly_expenses_for_year(previous_year)

        return jsonify({
            "current_year": current_year_expenses,
            "previous_year": previous_year_expenses
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/get_current_month_expenses", methods=["GET"])
@jwt_required()
def get_current_month_expenses():
    try:
        email = get_jwt_identity()
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Get the first and last day of the current month
        today = datetime.today()
        first_day = today.replace(day=1)
        next_month = first_day.replace(day=28) + timedelta(days=4)  # this will never fail
        last_day = next_month - timedelta(days=next_month.day)

        # Query expenses for the current month
        expenses_data = db.session.query(Expense).filter(
            Expense.email == email,
            Expense.date.between(first_day, last_day)
        ).all()

        # Initialize the days list with zeros
        days_in_month = (last_day - first_day).days + 1
        daily_expenses = [0] * days_in_month

        # Sum up the expenses for each day
        for expense in expenses_data:
            day_index = expense.date.day - 1  # to make it zero-based index
            daily_expenses[day_index] += expense.price

        return jsonify({"expenses": daily_expenses})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Reminder Section----------------------------------------------------------#
# Send Emails to Person
def send_reminders():
    today = datetime.utcnow().date()
    reminders = RemindFriend.query.filter_by(date=today).all()
    delete_reminders = []
    for reminder in reminders:
        try:
            message = person_reminder_message(reminder.email, reminder.reminder_name, reminder.price, reminder.description)
            send_mail(reminder.email, message)
            delete_reminders.append(reminder)

        except Exception as e:
            error_log = ErrorSendingMail(
                email=reminder.email,
                reminder_name=reminder.reminder_name
            )
            db.session.add(error_log)
            db.session.commit()

    for reminder in delete_reminders:
        db.session.delete(reminder)
        db.session.commit()


# get all reminders
def get_all_reminders(email):
    reminders = Reminder.query.filter_by(email=email).all()
    person_reminders = RemindFriend.query.filter_by(email=email).all()

    reminders_data = []
    for reminder in reminders:
        reminder_data = {
            "id": reminder.id,
            "date": reminder.date.strftime("%Y-%m-%d"),
            "reminder_name": reminder.reminder_name.split(" ")[0],
            "description": reminder.description,
            "price": reminder.price,
            "repeat": reminder.repeat_type
        }
        reminders_data.append(reminder_data)

    for reminder in person_reminders:
        reminder_data = {
            "id": reminder.id,
            "date": reminder.date.strftime("%Y-%m-%d"),
            "reminder_name": reminder.reminder_name.split(" ")[0],
            "description": reminder.description,
            "price": reminder.price,
            "person_email": reminder.person_email
        }
        reminders_data.append(reminder_data)

    return sorted(reminders_data, key=lambda x: x["date"])


# Adding reminder form
@app.route("/reminders", methods=["POST"])
@jwt_required()
def add_reminder():
    try:
        email = get_jwt_identity()
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        data = request.json
        reminder_name = data.get("reminder_name")
        description = data.get("description")
        date = data.get("date")
        price = data.get("price")
        repeat = data.get("repeat")

        new_reminder = Reminder(
            email=email,
            reminder_name=reminder_name,
            description=description,
            price=price,
            repeat_type=repeat,
            date=datetime.strptime(date, "%Y-%m-%d")
        )

        db.session.add(new_reminder)
        db.session.commit()

        reminders_data = get_all_reminders(email)

        return jsonify({"reminders": reminders_data}), 201

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Adding reminder form
@app.route("/reminders_friend", methods=["POST"])
@jwt_required()
def add_reminder_to_person():
    try:
        email = get_jwt_identity()
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        data = request.json
        reminder_name = data["reminder_name"]
        description = data["description"]
        date = data["date"]
        price = data["price"]
        person_email = data["person_email"]

        new_reminder = RemindFriend(
            email=email,
            reminder_name=reminder_name,
            description=description,
            price=price,
            person_email=person_email,
            date=datetime.strptime(date, "%Y-%m-%d")
        )

        db.session.add(new_reminder)
        db.session.commit()

        reminders_data = get_all_reminders(email)

        return jsonify({"reminders": reminders_data}), 201

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/get_reminders", methods=["GET"])
@jwt_required()
def get_reminders():
    try:
        email = get_jwt_identity()
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        reminders_data = get_all_reminders(email)

        return jsonify({"reminders": reminders_data}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/delete_reminders", methods=["POST"])
@jwt_required()
def delete_reminder():
    try:
        email = get_jwt_identity()
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        data = request.json
        reminder_id = data["id"]

        reminder = False
        if Reminder.query.filter_by(id=reminder_id, email=email).first():
            reminder = Reminder.query.filter_by(id=reminder_id, email=email).first()
        if RemindFriend.query.filter_by(id=reminder_id, email=email).first():
            reminder = RemindFriend.query.filter_by(id=reminder_id, email=email).first()

        if not reminder:
            return jsonify({"error": "Reminder not found"}), 404

        db.session.delete(reminder)
        db.session.commit()

        return jsonify({"message": "Reminder deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Setting --------------------------------------------------------------#
@app.route("/get_name_phone", methods=["GET"])
@jwt_required()
def get_name_phone():
    try:
        email = get_jwt_identity()
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        name = user.name
        phone = user.phone

        data = {
            "name": str(name),
            "phone": str(phone)
        }

        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/change_name_phone", methods=["POST"])
@jwt_required()
def change_name_phone():
    try:
        name = request.json["name"]
        phone = request.json["phone"]

        email = get_jwt_identity()
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        user.name = name
        user.phone = phone

        db.session.commit()

        return jsonify({"message": "success"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Renewing the reminders----------------------------------------------------------------#
def renew_reminders():
    try:
        email = get_jwt_identity()
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        reminders = Reminder.query.filter_by(email=email).all()

        for reminder in reminders:
            if reminder.repeat_type == "One Time":
                if reminder.date < datetime.utcnow():
                    db.session.delete(reminder)
                else:
                    continue
            elif reminder.repeat_type == "Every Day" and reminder.date < datetime.utcnow():
                reminder.date += timedelta(days=1)
            elif reminder.repeat_type == "Every Week" and reminder.date < datetime.utcnow():
                reminder.date += timedelta(weeks=1)
            elif reminder.repeat_type == "Every Month" and reminder.date < datetime.utcnow():
                next_month_date = reminder.date.replace(day=1) + timedelta(days=32)
                reminder.date = next_month_date.replace(day=min(reminder.date.day, next_month_date.day))
            elif reminder.repeat_type == "Every Year" and reminder.date < datetime.utcnow():
                reminder.date = reminder.date.replace(year=reminder.date.year + 1)

        db.session.commit()

        return {"message": "Reminder dates updated successfully"}

    except Exception as e:
        return {"error": str(e)}


# Get all expenses based on the date------------------------#
@app.route("/get_all_expenses", methods=["POST"])
@jwt_required()
def get_expense_datewise():
    try:
        email = get_jwt_identity()
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        data = request.json
        start_date = datetime.strptime(data["start_date"], "%Y-%m-%d")
        end_date = datetime.strptime(data["end_date"], "%Y-%m-%d")

        expenses_data = db.session.query(Expense).filter(
            Expense.email == email,
            Expense.date.between(start_date, end_date)
        ).order_by(Expense.date.desc()).all()

        data = []
        for expense in expenses_data:
                data.append({
                    "id": expense.id,
                    "expense_name": expense.expense_name,
                    "price": expense.price,
                    "tag": expense.tag,
                    "description": expense.description,
                    "date": expense.date.strftime("%Y-%m-%d") if expense.date else None
                })
        return {"expenses": data}
    except Exception as e:
        return {"error": str(e)}


@app.route("/delete_expense", methods=["POST"])
@jwt_required()
def delete_expense():
    try:
        email = get_jwt_identity()
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        data = request.json
        expense_id = data["id"]

        expense = False
        if Expense.query.filter_by(id=expense_id, email=email).first():
            expense = Expense.query.filter_by(id=expense_id, email=email).first()

        if not expense:
            return jsonify({"error": "Reminder not found"}), 404

        db.session.delete(expense)
        db.session.commit()

        return jsonify({"message": "Expense deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/update_expense", methods=["POST"])
@jwt_required()
def update_expense():
    try:
        email = get_jwt_identity()
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        expense_data = request.json
        expense_id = expense_data.get("id")
        expense_name = expense_data.get("expense_name")
        price = expense_data.get("price")
        tag = expense_data.get("tag")
        date = expense_data.get("date")
        description = expense_data.get("description")

        if not expense_id or not expense_name or not price or not tag or not date:
            return jsonify({"error": "Missing required fields"}), 400

        try:
            date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Invalid date format"}), 400

        expense = Expense.query.filter_by(id=expense_id, email=email).first()
        if not expense:
            return jsonify({"error": "Expense not found"}), 404

        expense.expense_name = expense_name
        expense.price = price
        expense.tag = tag
        expense.date = date
        expense.description = description

        db.session.commit()

        return jsonify({"message": "Expense updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


scheduler = BackgroundScheduler()
# For presave database----------------#
# scheduler.add_job(renew_reminders, 'interval', seconds=1)
scheduler.add_job(renew_reminders, 'cron', hour=0, minute=0)
scheduler.add_job(send_reminders, 'cron', hour=0, minute=0)
scheduler.start()

# if __name__ == "__main__":
#     app.run(debug=True)
