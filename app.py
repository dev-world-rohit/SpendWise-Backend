from datetime import datetime
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
from datetime import datetime, timedelta
from sqlalchemy import func
from apscheduler.schedulers.background import BackgroundScheduler
from models import db, User, OtpRequests, Expense, Reminder
from email_sender import send_mail

api = Flask(__name__)
CORS(api, origins='*')

api.config['SECRET_KEY'] = 'cairocoders-ednalan'
api.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

api.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=100)
jwt = JWTManager(api)

SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = True

bcrypt = Bcrypt(api)
db.init_app(api)

with api.app_context():
    db.create_all()


@api.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@api.route('/login', methods=["POST"])
def create_token():
    if request.method == 'POST':
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()
        if user:
            if bcrypt.check_password_hash(user.password, password):
                access_token = create_access_token(identity=email)

                return jsonify({
                    "email": email,
                    "access_token": access_token
                })
                # session["user_id"] = user.id
                # login_user(user, remember=True)
                # return jsonify("Login Successful.")
            else:
                return jsonify("Incorrect Password.")
        else:
            return jsonify("Email does not exist.")

    email = request.json.get("email", None)
    password = request.json.get("password", None)

    user = User.query.filter_by(email=email).first()
    if user is None:
        return jsonify({"error": "Wrong email or passwords"}), 401

    if not bcrypt.check_password_hash(user.password, password):
        return jsonify({"error": "Unauthorized"}), 401


def send_otp(email):
    otp = random.randint(100000, 999999)
    send_mail(email, otp)
    current_time = int(time.time())
    presave = OtpRequests(email=email, otp=otp, time=current_time)
    db.session.add(presave)
    db.session.commit()


@api.route("/otp", methods=['POST'])
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


@api.route("/signup", methods=["POST"])
def signup():
    name = request.json['name']
    phone = request.json['phone']
    email = request.json["email"]
    password = request.json['password']
    otp = request.json["otp"]
    current_time = int(time.time())
    otp_request = OtpRequests.query.filter_by(email=email).first()
    if otp_request:
        otp_request_otp = str(otp_request.otp).strip()
        otp_stripped = str(otp).strip()
        # print(str(otp_request.otp)==str(otp),  otp, otp_request.otp, end='\n\n\n\n\n\n')
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
                return jsonify("OTP expired. OTP Sent again.")
        else:
            return jsonify("Invalid OTP. Please try again.")
    else:
        return jsonify("No user found. Please SignUp First.")


@api.after_request
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


@api.route("/logout", methods=["POST"])
def logout():
    response = jsonify({"msg": "logout successful"})
    unset_jwt_cookies(response)
    return response


@api.route('/<getemail>')
@jwt_required()
def my_profile(getemail):
    if not getemail:
        return jsonify({"error": "Unauthorized Access"}), 401

    user = User.query.filter_by(email=getemail).first()
    response_body = {
        "id": user.id,
        "name": user.name,
        "email": user.email,
    }

    return response_body


# Dashboard Routes-----------------------------------------------------------------------------#
# Getting name of the User
@api.route("/name", methods=["GET"])
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
@api.route("/total_expense", methods=["GET"])
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


@api.route("/tag_based_expenses", methods=["GET"])
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


@api.route("/get_reminder_dashboard", methods=["GET"])
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

        return upcoming_reminders_data

    except Exception as e:
        return {"error": str(e)}


# Functionality to Add Expense
@api.route("/add_expense", methods=["POST"])
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


@api.route("/expenses", methods=["GET"])
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
@api.route("/tag_based_expenses_analysis", methods=["GET"])
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
@api.route("/expenses_by_month", methods=["GET"])
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


@api.route("/monthly_expenses", methods=["GET"])
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


# Reminder Section----------------------------------------------------------#
# Adding reminder form
@api.route("/reminders", methods=["POST"])
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

        # Create a new reminder object
        new_reminder = Reminder(
            email=email,
            reminder_name=reminder_name,
            description=description,
            price=price,
            repeat_type=repeat,
            date=datetime.strptime(date, "%Y-%m-%d")  # Assuming date is in YYYY-MM-DD format
        )

        # Save the new reminder to the database
        db.session.add(new_reminder)
        db.session.commit()

        # Retrieve all reminders for the logged-in user after adding the new reminder
        reminders = Reminder.query.filter_by(email=email).all()

        # Prepare response data
        reminders_data = []
        for reminder in reminders:
            reminder_data = {
                "id": reminder.id,
                "date": reminder.date.strftime("%Y-%m-%d"),
                "reminder_name": reminder.reminder_name,
                "description": reminder.description,
                "price": reminder.price,
                "repeat": reminder.repeat_type
            }
            reminders_data.append(reminder_data)

        return jsonify(reminders_data), 201

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400  # Bad request if date format is invalid

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Internal server error for other exceptions


@api.route("/get_reminders", methods=["GET"])
@jwt_required()
def get_reminders_by_date():
    try:
        email = get_jwt_identity()
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Retrieve all reminders for the logged-in user
        reminders = Reminder.query.filter_by(email=email).all()

        # Group reminders by date
        reminders_by_date = {}
        for reminder in reminders:
            reminder_date_str = reminder.date.strftime("%Y-%m-%d")
            if reminder_date_str not in reminders_by_date:
                reminders_by_date[reminder_date_str] = []
            reminders_by_date[reminder_date_str].append({
                "id": reminder.id,
                "date": reminder_date_str,
                "reminder_name": reminder.reminder_name,
                "description": reminder.description,
                "price": reminder.price,
                "repeat": reminder.repeat_type
            })

        # Extract reminders grouped by date into a flat list
        reminders_list = []
        for reminders_on_date in reminders_by_date.values():
            reminders_list.extend(reminders_on_date)

        return jsonify(reminders_list), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/delete_reminders", methods=["POST"])
@jwt_required()
def delete_reminder():
    try:
        email = get_jwt_identity()
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        data = request.json
        reminder_id = data.get("id")
        # Retrieve the reminder to delete
        print(reminder_id, email)
        reminder = Reminder.query.filter_by(id=reminder_id, email=email).first()
        if not reminder:
            return jsonify({"error": "Reminder not found"}), 404

        # Delete the reminder from the database
        db.session.delete(reminder)
        db.session.commit()

        return jsonify({"message": "Reminder deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Renewinig the reminders----------------------------------------------------------------#
def renew_reminders():
    print("hello")
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
            elif reminder.repeat_type == "Every Day":
                reminder.date += timedelta(days=1)
            elif reminder.repeat_type == "Every Week":
                reminder.date += timedelta(weeks=1)
            elif reminder.repeat_type == "Every Month":
                next_month_date = reminder.date.replace(day=1) + timedelta(days=32)
                reminder.date = next_month_date.replace(day=min(reminder.date.day, next_month_date.day))
            elif reminder.repeat_type == "Every Year":
                reminder.date = reminder.date.replace(year=reminder.date.year + 1)

        db.session.commit()

        return {"message": "Reminder dates updated successfully"}

    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(renew_reminders, 'interval', hours=1)
    scheduler.start()
    api.run(debug=True)
