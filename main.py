import os
from flask import Flask
from flask_restful import Resource, Api
from application import config
from application.config import LocalDevelopmentConfig

app = None
api = None
def create_app():
    app = Flask(__name__)
    app.config.from_object(LocalDevelopmentConfig)
    api = Api(app)
    app.app_context().push()
    return app,api

app, api = create_app()


from application.controllers import *
from application.api import FlightsAPI, TrainAPI, BusAPI, HotelAPI, ResortAPI, HostelAPI, ItineraryAPI
api.add_resource(FlightsAPI, "/excurra/flights/<string:departure_city>/<string:arrival_city>/<string:departure_date>/<string:arrival_date>/<string:number_of_adults>/<string:number_of_children>/<string:cabin_class>")
api.add_resource(TrainAPI, "/excurra/trains/<string:departure_city>/<string:arrival_city>/<string:departure_date>/<string:arrival_date>/<string:number_of_adults>/<string:number_of_children>/<string:class_type>")
api.add_resource(BusAPI, "/excurra/buses/<string:departure_city>/<string:arrival_city>/<string:departure_date>/<string:arrival_date>/<string:number_of_adults>/<string:number_of_children>/<string:class_type>")
api.add_resource(HotelAPI, "/excurra/hotels/<string:location>/<string:from_date>/<string:to_date>/<string:number_of_adults>/<string:number_of_children>")
api.add_resource(ResortAPI, "/excurra/resorts/<string:location>/<string:from_date>/<string:to_date>/<string:number_of_adults>/<string:number_of_children>")
api.add_resource(HostelAPI, "/excurra/hostels/<string:location>/<string:from_date>/<string:to_date>/<string:number_of_adults>/<string:number_of_children>")
api.add_resource(ItineraryAPI, "/excurra/itinerary/<string:city>/<interests>/<string:num_of_days>/<string:num_of_people>/<string:group_type>")
if __name__=='__main__':
    app.run()