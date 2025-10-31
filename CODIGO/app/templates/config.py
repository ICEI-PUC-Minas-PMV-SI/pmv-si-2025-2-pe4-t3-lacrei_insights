import os

class Config:
    FLASK_ENV = os.getenv("FLASK_ENV", "production")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DATABASE_URL = os.getenv("DATABASE_URL")

class ProductionConfig(Config):
    DEBUG = False

class DevelopmentConfig(Config):
    DEBUG = True

config_by_name = {
    'production': ProductionConfig,
    'development': DevelopmentConfig
}
