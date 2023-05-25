import os
import uuid
from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from schemas import UserSchema,UserRegisterSchema
from passlib.hash import pbkdf2_sha256
from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from models import UserModel
from db import db
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from flask_jwt_extended import create_access_token, jwt_required, get_jwt
from blocklist import BLOCKLIST
import requests

blp = Blueprint("Users", "users", description="operations on users")

def send_simple_message(to, subject, body):
    domain = os.getenv("MAILGUN_DOMAIN")
    return requests.post(
		f"https://api.mailgun.net/v3/{domain}/messages",
		auth=("api", os.getenv("MAILGUN_API_KEY")),
		data={"from": f"Excited User <mailgun@{domain}>",
			"to": [to],
			"subject": subject,
			"text": body})

@blp.route("/register")
class UserRegister(MethodView):
    @blp.arguments(UserRegisterSchema)
    def post(self, user_data):
        if UserModel.query.filter(
                or_(UserModel.username == user_data["username"],
                    UserModel.email == user_data["email"])).first():
            abort(409, message = "A user with that username already exists")
        user = UserModel(
            username = user_data["username"],
            email = user_data["email"],
            password = pbkdf2_sha256.hash(user_data["password"])
        )
        db.session.add(user)
        db.session.commit()

        send_simple_message(
            to = user.email,
            subject= "Successfully signed up",
            body= f"Hi {user.username}! You have succesfully signed up to the Stores Rest API"
        )


        return {"message": "user has been created successfully"}

@blp.route("/login")
class UserLogin(MethodView):
    @blp.arguments(UserSchema)
    def post(self, user_data):
        user = UserModel.query.filter(
            UserModel.username == user_data["username"]
        ).first()
        if user and pbkdf2_sha256.verify(user_data["password"], user.password):
            access_token = create_access_token(identity=user.id)
            return {"access token": access_token}

        abort(401, message = "Invalid Credentials")

@blp.route("/logout")
class UserLogout(MethodView):
    @jwt_required()
    def post(self):
        jti = get_jwt()["jti"]
        BLOCKLIST.add(jti)
        return {"message": "successfully logged out"}



@blp.route("/user/<int:user_id>")
class User(MethodView):
    @blp.response(200, UserSchema)
    def get(self, user_id):
        user = UserModel.query.get_or_404(user_id)
        return user

    def delete(self, user_id):
        user = UserModel.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return{"message": "user deleted"}, 200