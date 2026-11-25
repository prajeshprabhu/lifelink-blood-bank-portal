import os
from flask import Flask, redirect, send_from_directory
from flask_jwt_extended.exceptions import JWTExtendedException
from config import Config
from extensions import cors, jwt, limiter
from database import initialize_schema
from utils.authentication import initialize_admin
from routes.auth_routes import auth_bp
from routes.dashboard_routes import dashboard_bp
from routes.inventory_routes import inventory_bp
from routes.api_routes import api_bp
from routes.profile_routes import profile_bp
from utils.decorators import jwt_required_dashboard


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    cors.init_app(
        app,
        resources={r"/api/*": {"origins": Config.CORS_ALLOWED_ORIGINS or "*"}},
        supports_credentials=True,
    )
    jwt.init_app(app)
    limiter.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(profile_bp)

    initialize_schema()
    initialize_admin()

    @app.get("/favicon.ico")
    def favicon():
        return send_from_directory(
            app.static_folder,
            "images/favicon.svg",
            mimetype="image/svg+xml",
        )

    @app.get("/api/docs")
    def api_docs_redirect():
        return redirect("/api-documentation")

    @app.get("/api-documentation")
    @jwt_required_dashboard
    def api_documentation():
        from flask import render_template
        return render_template("api_documentation.html")

    @jwt.unauthorized_loader
    def unauthorized(reason):
        from flask import jsonify
        return jsonify(success=False, error="Authentication required"), 401

    @jwt.invalid_token_loader
    def invalid_token(reason):
        from flask import jsonify
        return jsonify(success=False, error="Invalid or expired token"), 401

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5001")), debug=False)
