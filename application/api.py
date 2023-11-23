import os
from datetime import datetime
import json
import requests
from flask_restful import Resource
from flask_restful import fields, marshal_with
from application.validation import NotFoundError
from application.config import LocalDevelopmentConfig
#from ...static import *

from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.llms import OpenAI
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.schema import (
    HumanMessage,
)

from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field, validator
from typing import List, Optional

import random
from datetime import time, datetime, timedelta

os.environ["OPENAI_API_KEY"] = "Insert OpenAI Key"
date_format = "%Y-%m-%d"
class FlightsAPI(Resource):
    #function to get iata code for the departure and arrival cities
    def map_to_iata_code(self,departure_city,arrival_city):
        with open('static/iata.json') as file:
            airport_data = json.load(file)
        departure_airport_code = ""
        arrival_airport_code = ""
        for obj in airport_data:
            if arrival_airport_code != "" and departure_airport_code != "":
                break
            if obj['city'] == departure_city:
                departure_airport_code = obj['iata']
                continue
            if obj['city'] == arrival_city:
                arrival_airport_code=obj['iata']
        return departure_airport_code,arrival_airport_code

    def map_to_airport(self, airport_code):
        with open('static/airports.json') as airports:
	        airport_data = json.load(airports)
        for a in airport_data:
            if a['iata'] == airport_code:
                return a['name']

    def map_to_airline(self, airline_code):
        with open('static/airlines.json') as airlines:
	        airline_data = json.load(airlines)
        for a in airline_data:
            if a['iata'] == airline_code:
                return a['name']
        
    def get_airlines_code(self, city):
        with open('static/airlines.json') as airlines:
	        airline_data = json.load(airlines)
        with open('static/airports.json') as airports:
	        airport_data = json.load(airports)
        country = ""
        for a in airport_data:
            if a['city'] == city:
                country = a['country']
        options = []
        for a in airline_data:
            if len(options) >=5:
                break
            if a['iata'] != "" and a['country'] == country:
                options.append(a['iata'])
        return options[random.randint(0,len(options)-1)]


    def get(self,departure_city,arrival_city,departure_date,arrival_date,number_of_adults,number_of_children,cabin_class):
        response = None
        flight_api_key = LocalDevelopmentConfig.FLIGHT_API_KEY
        departure_airport_code, arrival_airport_code = self.map_to_iata_code(departure_city,arrival_city)
        get_flights_endpoint = 'https://api.flightapi.io/roundtrip'
        get_flights_endpoint+=f'/{flight_api_key}/{departure_airport_code}/{arrival_airport_code}/{departure_date}/{arrival_date}/{number_of_adults}/{number_of_children}/0/{cabin_class}/INR'
        print(get_flights_endpoint)
        try:
            response = requests.get(get_flights_endpoint).json()
            print(response)

            trip_ids = []
            fares = []
            for fare in response['fares']:
                if len(fares) >= 5:
                    break
                trip_ids.append(fare["tripId"])
                fares.append(fare["price"]["totalAmount"])

            flight_legIds = []
            for trip_id in trip_ids:
                for trip in response['trips']:
                    if trip['id'] == trip_id:
                        flight_legIds.append(trip['legIds'])
                        break

            flights = []
            count = 0
            switch = 0
            for flight in flight_legIds:
                flight_deets = []
                for legId in flight:
                    for leg in response['legs']:
                        temp = {}
                        if legId == leg['id']:
                            temp
                            temp['deptAirportCode'] = departure_airport_code if switch == 0 else arrival_airport_code
                            temp['arrivalAirportCode'] = arrival_airport_code if switch == 0 else departure_airport_code
                            temp['departureAirportName'] = self.map_to_airport(temp['deptAirportCode'])
                            temp['arrivalAirportName'] = self.map_to_airport(temp['arrivalAirportCode'])
                            temp['deptTime'] = leg['departureDateTime']
                            temp['arrivalTime'] = leg['arrivalDateTime']
                            temp['duration'] = leg['duration']
                            temp['airlineCodes'] = leg['airlineCodes']
                            airlines = []
                            for a in leg['airlineCodes']:
                                airlines.append(self.map_to_airline(a))
                            temp['airlineNames'] = airlines
                            temp['stopoverAirportCodes'] = leg['stopoverAirportCodes']
                            temp['nonStop'] = "true"if len(temp['stopoverAirportCodes']) == 0 else "false"
                            airports = []
                            for a in leg['stopoverAirportCodes']:
                                airports.append(self.map_to_airport(a))
                            temp['stopoverAirports'] = airports
                            flight_deets.append(temp)
                            switch = not switch
                            break
                flights.append({"flightDetails":flight_deets, "totalAmount":fares[count]})
                count+=1
        except:
            departure_airport_code, arrival_airport_code = self.map_to_iata_code(departure_city,arrival_city)
            flights = []
            for i in range(5):
                temp = {}
                first_trip = {}
                second_trip = {}

                first_trip['deptAirportCode'] = departure_airport_code
                first_trip['arrivalAirportCode'] = arrival_airport_code
                first_trip['departureAirportName'] = self.map_to_airport(departure_airport_code)
                first_trip['arrivalAirportName'] = self.map_to_airport(arrival_airport_code)
                first_trip["deptTime"] = departure_date+"T12:55:00.000+05:30"
                first_trip["arrivalTime"] = departure_date+"T19:25:00.000+05:30"
                first_trip["duration"] = "06h 30m"
                first_trip["airlineCodes"] = [self.get_airlines_code(departure_city)]
                first_trip["airlineNames"] = [self.map_to_airline(first_trip['airlineCodes'][0])]
                first_trip['nonStop'] = "true"
                first_trip["stopoverAirportCodes"] = []
                first_trip["stopoverAirports"] = []
                    
                    
                second_trip['deptAirportCode'] = arrival_airport_code
                second_trip['arrivalAirportCode'] = departure_airport_code
                second_trip['departureAirportName'] = self.map_to_airport(arrival_airport_code)
                second_trip['arrivalAirportName'] = self.map_to_airport(departure_airport_code)
                second_trip["deptTime"] = arrival_date+"T12:55:00.000+05:30"
                second_trip["arrivalTime"] = arrival_date+"T19:25:00.000+05:30"
                second_trip["duration"] = "06h 30m"
                second_trip["airlineCodes"] = [self.get_airlines_code(arrival_city)]
                second_trip["airlineNames"] = [self.map_to_airline(second_trip['airlineCodes'][0])]
                second_trip['nonStop'] = "true"
                second_trip["stopoverAirportCodes"] = []
                second_trip["stopoverAirports"] = []

                flight_details = [first_trip, second_trip]
                temp["flightDetails"] = flight_details
                temp["totalAmount"] = random.randint(4500, 13000) * (int(number_of_adults) + int(number_of_children))
                flights.append(temp)
        print(flights)

        return flights
        
    
class TrainAPI(Resource):
    def get(self, departure_city, arrival_city, departure_date, arrival_date, number_of_adults, number_of_children,class_type):
        #need to generate some data
        trains = []
        for i in range(5):
            temp = {}
            train_details = []
            start_time = time(1,0)
            end_time = time(12,0)
            random_hour = random.randint(start_time.hour, end_time.hour)
            reandom_minute = random.randint(0,59)
            random_dept_time = time(random_hour,reandom_minute)
            hours_to_add = random.randint(8,48)
            new_hour = (random_dept_time.hour + hours_to_add)%24
            new_arrival_time = time(new_hour, random_dept_time.minute)

            first_trip = {}
            second_trip = {}

            first_trip["deptStationName"] = departure_city+" Juncton"
            first_trip["arrivalStationName"] = arrival_city+" Central Railway Station"
            first_trip["deptDate"] = datetime.strptime(departure_date, date_format).date()
            first_trip["deptTime"] = random_dept_time
            first_trip["arrivalDate"] = datetime.strftime(first_trip["deptDate"],date_format) if random_dept_time.hour+hours_to_add > 24 else datetime.strftime(first_trip["deptDate"] + timedelta(days = 1),date_format)
            first_trip["arrivalTime"] = new_arrival_time.strftime("%H:%M")
            first_trip["deptDate"] = datetime.strftime(first_trip["deptDate"],date_format)
            first_trip["deptTime"] = first_trip["deptTime"].strftime("%H:%M")
            first_trip["trainCode"] = random.randint(1111,9999)
            first_trip["trainName"] = departure_city+" Express"
            first_trip["duration"] = str(random_hour)+"h 00m"
            
            second_trip["deptStationName"] = arrival_city+" Central Railway Station"
            second_trip["arrivalStationName"] = departure_city+" Juncton"
            second_trip["deptDate"] = datetime.strptime(arrival_date, date_format).date()
            second_trip["deptTime"] = random_dept_time
            second_trip["arrivalDate"] = datetime.strftime(second_trip["deptDate"],date_format) if random_dept_time.hour+hours_to_add > 24 else datetime.strftime(second_trip["deptDate"] + timedelta(days = 1),date_format)
            second_trip["arrivalTime"] = new_arrival_time.strftime("%H:%M")
            second_trip["deptDate"] = datetime.strftime(second_trip["deptDate"],date_format)
            second_trip["deptTime"] = second_trip["deptTime"].strftime("%H:%M")
            second_trip["trainCode"] = random.randint(1111,9999)
            second_trip["trainName"] = arrival_city+" Express"
            second_trip["duration"] = str(random_hour)+"h 00m"

            train_details = [first_trip, second_trip]
            temp["train_details"] = train_details
            temp["total_amount"] = random.randint(800, 2000) * (int(number_of_adults) + int(number_of_children))
            trains.append(temp)
        return trains

class BusAPI(Resource):
    def get(self, departure_city, arrival_city, departure_date, arrival_date, number_of_adults, number_of_children,class_type):
        #need to generate some data
        buses = []
        for i in range(5):
            temp = {}
            bus_details = []
            start_time = time(1,0)
            end_time = time(18,0)
            random_hour = random.randint(start_time.hour, end_time.hour)
            reandom_minute = random.randint(0,59)
            random_dept_time = time(random_hour,reandom_minute)
            hours_to_add = random.randint(10,48)
            new_hour = (random_dept_time.hour + hours_to_add)%24
            new_arrival_time = time(new_hour, random_dept_time.minute)

            generic_bus_names = ["S R S Travels", "V R L Travels", "Jabbar Travels", "Orange Tours & Travels", "CSM Travels", "Volvo Buses", "Bharat Benz"]

            first_trip = {}
            second_trip = {}

            first_trip["deptStationName"] = departure_city+" Bus Stand"
            first_trip["arrivalStationName"] = arrival_city+" Bus Stand"
            first_trip["deptDate"] = datetime.strptime(departure_date, date_format).date()
            first_trip["deptTime"] = random_dept_time
            first_trip["arrivalDate"] = datetime.strftime(first_trip["deptDate"],date_format) if random_dept_time.hour+hours_to_add > 24 else datetime.strftime(first_trip["deptDate"] + timedelta(days = 1),date_format)
            first_trip["arrivalTime"] = new_arrival_time.strftime("%H:%M")
            first_trip["deptDate"] = datetime.strftime(first_trip["deptDate"],date_format)
            first_trip["deptTime"] = first_trip["deptTime"].strftime("%H:%M")
            first_trip["busCode"] = random.randint(1111,9999)
            first_trip["busName"] = generic_bus_names[random.randint(0,len(generic_bus_names)-1)]
            first_trip["duration"] = str(random_hour)+"h 00m"
            
            second_trip["deptStationName"] = arrival_city+" Bus Stand"
            second_trip["arrivalStationName"] = departure_city+" Bus Stand"
            second_trip["deptDate"] = datetime.strptime(arrival_date, date_format).date()
            second_trip["deptTime"] = random_dept_time
            second_trip["arrivalDate"] = datetime.strftime(second_trip["deptDate"],date_format) if random_dept_time.hour+hours_to_add > 24 else datetime.strftime(second_trip["deptDate"] + timedelta(days = 1),date_format)
            second_trip["arrivalTime"] = new_arrival_time.strftime("%H:%M")
            second_trip["deptDate"] = datetime.strftime(second_trip["deptDate"],date_format)
            second_trip["deptTime"] = second_trip["deptTime"].strftime("%H:%M")
            second_trip["busCode"] = random.randint(1111,9999)
            second_trip["busName"] = generic_bus_names[random.randint(0,len(generic_bus_names)-1)]
            second_trip["duration"] = str(random_hour)+"h 00m"

            bus_details = [first_trip, second_trip]
            temp["bus_details"] = bus_details
            temp["total_amount"] = random.randint(900, 2000) * (int(number_of_adults) + int(number_of_children))
            buses.append(temp)
        print(buses)
        return buses

class HotelAPI(Resource):
    def get(self, location, from_date, to_date, number_of_adults, number_of_children):
        meals = ["Breakfast", "Breakfast, Dinner"]
        perks = ["Parking","Gym","Free WiFi", "Gym, Free Wifi", "Free Wifi, Swimming Pool", "Gym, Swimming Pool, Free WiFi", "Parking, Free Wifi"]
        hotel_chains = ["Novotel", "Sheraton Hotels and Resorts", "Radisson Hotel Group", "Crowne Plaza", "Hyatt Hotels Corporation"]
        hotels = []
        address = ["Central Spot, ", "East Town, ", "West Side, ", "South City, ", "All Blue, "]
        num = 0
        for i in range(5):
            hotel = {}
            hotel["hotelName"] = hotel_chains[num]
            hotel["hotelLocation"] = address[num]+location
            hotel["perks"] = perks[random.randint(0, len(perks)-1)].split(", ")
            hotel["meals"] = meals[random.randint(0, len(meals)-1)].split(", ")
            hotel["rating"] = random.randint(2,5)
            hotel["totalAmount"] = random.randint(1500,2500) * (int(number_of_adults) + int(number_of_children)) * (datetime.strptime(to_date, date_format) - datetime.strptime(from_date, date_format)).days
            hotels.append(hotel)
            num+=1
        print(hotels)
        return hotels

class ResortAPI(Resource):
    def get(self, location, from_date, to_date, number_of_adults, number_of_children):
        meals = ["Breakfast", "Breakfast, Dinner", "Breakfast, Lunch, Dinner", "Breakfast, Lunch, Dinner, Snacks"]
        perks = ["Parking, Spa, Doctor on Call, Beach","Gym, Beach, Children Parks, Spa, Laundry","Free WiFi, Beach, Doctor on Call, Game Room, Spa", "Gym, Free Wifi, Beach, Spa, Laundry", "Free Wifi, Swimming Pool, Spa, Beach, Children Parks", "Gym, Swimming Pool, Free WiFi, Spa, Laundary", "Parking, Free Wifi, Laundry, Spa, Beach, Game Room"]
        resort_chains = ["Banyan Tree Hotels & Resorts","COMO Hotels and Resorts","Meliá Hotels & Resorts","JW Marriott Resorts & Hotels","Four Seasons Resorts and Hotels","Shangri-La Hotels and Resorts"]
        resorts = []
        num = 0
        address = ["Central Spot, ", "East Town, ", "West Side, ", "South City, ", "All Blue, "]
        for i in range(5):
            resort = {}
            resort["resortName"] = resort_chains[num]
            resort["resortLocation"] = address[num]+location
            resort["perks"] = perks[random.randint(0, len(perks)-1)].split(", ")
            resort["meals"] = meals[random.randint(0, len(meals)-1)].split(", ")
            resort["rating"] = random.randint(2,5)
            resort["totalAmount"] = random.randint(2000,4500) * (int(number_of_adults) + int(number_of_children)) * (datetime.strptime(to_date, date_format) - datetime.strptime(from_date, date_format)).days
            resorts.append(resort)
            num+=1
        return resorts

class HostelAPI(Resource):
    def get(self, location, from_date, to_date, number_of_adults, number_of_children):
        meals = ["Breakfast", "Breakfast, Dinner", "Breakfast, Lunch, Dinner"]
        hostel_chains = ["Backpacker's Haven Hostel", "Wanderlust Inn", "Explorer's Lodge", "Nomadic Nest Hostel", "Cityscape Hostel", "The Traveler's Respite", "Urban Bunkhouse", "Basecamp Hostel"]
        hostels = []
        address = ["Central Spot, ", "East Town, ", "West Side, ", "South City, ", "All Blue, "]
        num = 0
        for i in range(5):
            hostel = {}
            hostel["hostelName"] = hostel_chains[num]
            hostel["hostelLocation"] = address[num]+location
            hostel["meals"] = meals[random.randint(0, len(meals)-1)].split(", ")
            hostel["rating"] = random.randint(2,5)
            hostel["totalAmount"] = random.randint(700,1500) * (int(number_of_adults) + int(number_of_children)) * (datetime.strptime(to_date, date_format) - datetime.strptime(from_date, date_format)).days
            hostels.append(hostel)
            num+=1
        return hostels

class ItineraryAPI(Resource):
    def get(self, city, interests, num_of_days, num_of_people, group_type):
        interests = interests.split(',')
        number_of_activities = str(int(num_of_days)*3+5)
        llm = ChatOpenAI(temperature=0.0)
        class Activity(BaseModel):
            activity_place: str = Field(description="the name of the exact place where the activity takes place pertaining to the mentioned city")
            activity_description: str = Field(description="a short description highlighting activity and the place")
            activity_category: str = Field(description="only one category that best describes the activity falling under the list of interests given by the user")
        class Itinerary(BaseModel):
            activities: List[Activity] = Field(description="list of activities to do in the given city")
        pydantic_parser = PydanticOutputParser(pydantic_object=Itinerary)
        format_instructions = pydantic_parser.get_format_instructions()
        template_string = """List top {number_of_activities} activities to do in {city} including authentic food options (you can also suggest some authentic food items), with a focus on the following interests: {interests}, for {people_num} people and group type {group_type}. Take care not to repeat any suggestions.
        {format_instructions}
        """
        prompt = ChatPromptTemplate.from_template(template=template_string)
        messages = prompt.format_messages(city=city,
                                            number_of_activities= number_of_activities,
                                            interests = " ".join(interests),
                                            people_num = num_of_people,
                                            group_type=group_type,
                                        format_instructions=format_instructions)
        print(messages)
        output = llm(messages)
        print(output.content)
        #final = pydantic_parser.parse(output.content)
        #print(final)
        json_string = output.content.replace("\t", " ").replace("\n", "")
        res = json.loads(json_string)
        #print(res)
        return res
