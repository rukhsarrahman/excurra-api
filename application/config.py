import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config():
    DEBUG = False
    FLIGHT_API_KEY = 'Insert FlightAI key'
    OPENAI_API_KEY = "Insert OpenAI key"

class LocalDevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
