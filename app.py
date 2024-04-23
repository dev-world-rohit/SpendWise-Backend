import json
import random
import time
from flask import Flask, request, jsonify
from datetime import datetime, timedelta, timezone
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, unset_jwt_cookies, jwt_required, JWTManager
from flask_bcrypt import Bcrypt
from flask_cors import CORS

from models import db, User, OtpRequests, Expense
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
            return jsonify({"error": "Error occured. Please try again later."})

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
                new_user = User(email=email, name=name, phone=phone, password=hashed_password)
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

# Functionality to Add Expense-----------------------------------#
@api.route("/add_expense", methods=["POST"])
@jwt_required()
def add_expense():
    print("hello")
    try:
        email = get_jwt_identity()
        print(email)
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        expense_data = request.json
        expense_name = expense_data.get("expense_name")
        price = expense_data.get("price")
        tag = expense_data.get("tag")
        mode = expense_data.get("mode")
        description = expense_data.get("description")
        print(expense_data)
        # Validate the required fields
        if not expense_name or not price or not tag or not mode:
            return jsonify({"error": "Missing required fields"}), 400

        # Store the expense data
        new_expense = Expense(
            email=email,
            expense_name=expense_name,
            price=price,
            tag=tag,
            mode=mode,
            description=description
        )
        db.session.add(new_expense)
        db.session.commit()

        return jsonify({"message": "Expense added successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    api.run(debug=True)