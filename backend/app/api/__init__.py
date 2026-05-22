def register_blueprints(app):
    from app.api.plans import plans_bp
    from app.api.records import records_bp
    from app.api.hermes import hermes_bp
    from app.api.baselines import baselines_bp
    from app.api.data import data_bp
    from app.api.stats import stats_bp

    app.register_blueprint(plans_bp, url_prefix="/api/v1/plans")
    app.register_blueprint(records_bp, url_prefix="/api/v1/records")
    app.register_blueprint(hermes_bp, url_prefix="/api/v1/hermes")
    app.register_blueprint(baselines_bp, url_prefix="/api/v1/baselines")
    app.register_blueprint(data_bp, url_prefix="/api/v1/data")
    app.register_blueprint(stats_bp, url_prefix="/api/v1/stats")
