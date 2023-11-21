import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config():
    DEBUG = False
    FLIGHT_API_KEY = '6544ef5e489b8a8d9e655a27'
    OPENAI_API_KEY = "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"

class LocalDevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False