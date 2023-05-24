import uuid
from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from schemas import StoreSchema, TagSchema
import uuid
from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from models import StoreModel, TagModel
from db import db
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

blp = Blueprint("Tags", "tags", description="operations on tags")

@blp.route("/store/<int:store_id>/tag")
class TagInStore(MethodView):
    @blp.response(200, TagSchema(many = True))
    def get(self, store_id):
        store = StoreModel.query.get_or_404(store_id)
        return store.tags.all()

    @blp.arguments(TagSchema)
    @blp.response(201, TagSchema)
    def post(self, tag_data, store_id):

        tag = TagModel(**tag_data, store_id = store_id)

        try:
            db.session.add(tag)
            db.session.commit()

        except SQLAlchemyError as e:
            abort(500, message = str(e))

        return tag

    @blp.route("/tag/<int:tag_id>")
    class Tag(MethodView):
        @blp.response(200, TagSchema)
        def get(self, tag_id):
            tag = TagModel.query.get_or_404(tag_id)
            return tag