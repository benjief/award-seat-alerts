import requests
import json
import os
from typing import List, Dict, Optional
from twilio.rest import Client
# from config import API_KEY, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER, MY_PHONE_NUMBER

API_KEY = os.environ.get("API_KEY")
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")
MY_PHONE_NUMBER = os.environ.get("MY_PHONE_NUMBER")

def fetch_flights(params: Dict[str, str]) -> Optional[str]:
    """Fetch flights from the Seats.aero API."""
    url = "https://seats.aero/partnerapi/search"
    headers = {
        "accept": "application/json",
        "Partner-Authorization": f"Bearer {API_KEY}"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def parse_json(response_text: str) -> Dict:
    """Parse the JSON response text into a dictionary."""
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        print("Error decoding JSON response.")
        return {}

def filter_flights(flights: List[Dict], threshold: int) -> List[Dict]:
    """Filter flights based on business class availability and mileage cost."""
    filtered_flights = []
    for flight in flights:
        if flight.get("JAvailable") and flight.get("JMileageCost") and flight.get("Source") == "aeroplan":
            try:
                mileage_cost = int(flight["JMileageCost"])
                if mileage_cost < threshold:
                    filtered_flights.append({
                        "RouteID": flight.get("RouteID"),
                        "Origin": flight["Route"].get("OriginAirport"),
                        "Destination": flight["Route"].get("DestinationAirport"),
                        "Date": flight.get("Date"),
                        "MileageCost": mileage_cost,
                        "Airlines": flight.get("JAirlines"),
                        "DirectFlight": flight.get("JDirect"),
                        "RemainingSeats": flight.get("JRemainingSeats")
                    })
            except ValueError:
                print(f"Error converting mileage cost to integer for flight ID: {flight.get('ID')}")
    return filtered_flights

def display_flights(flights: List[Dict]) -> None:
    """Display filtered flight results."""
    if flights:
        print("Flights below the threshold:")
        for flight in flights:
            print(f"Route: {flight['Origin']} -> {flight['Destination']} on {flight['Date']}")
            print(f"  Mileage Cost: {flight['MileageCost']}")
            print(f"  Airlines: {flight['Airlines']}")
            print(f"  Direct Flight: {flight['DirectFlight']}")
            print(f"  Remaining Seats: {flight['RemainingSeats']}\n")
    else:
        print("No flights found below the threshold.")

def send_sms_notification(flights: List[Dict]) -> None:
    """Send an SMS notification with the details of the five least expensive flights."""
    if not flights:
        print("No flights to send.")
        return
    
    # Sort the flights by mileage cost in ascending order
    flights = sorted(flights, key=lambda x: x["MileageCost"])[:10]
    
    # Prepare the message content
    message_body = "Top 10 Cheapest Flights:\n"
    for flight in flights:
        message_body += (
            f"Route: {flight['Origin']} -> {flight['Destination']} on {flight['Date']}\n"
            f"  Mileage Cost: {flight['MileageCost']}\n"
            f"  Airlines: {flight['Airlines']}\n"
            f"  Direct Flight: {flight['DirectFlight']}\n"
            f"  Remaining Seats: {flight['RemainingSeats']}\n\n"
        )
    
    # Initialize Twilio client
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    
    try:
        # Send the SMS
        message = client.messages.create(
            body=message_body,
            from_= TWILIO_PHONE_NUMBER,
            to=MY_PHONE_NUMBER
        )
        print(f"SMS sent successfully! Message SID: {message.sid}")
    except Exception as e:
        print(f"Error sending SMS: {e}")

def main() -> None:
    """Main function to execute the flight search, filtering, and notifications."""
    # Define multiple parameter sets
    parameter_sets = [
        {
            "origin_airport": "EZE, SCL",
            "destination_airport": "YYZ, YUL, IAD, IAH, ORD",
            "cabin": "business",
            "start_date": "2024-12-31",
            "end_date": "2025-01-18",
            "take": 500,
            "order_by": "lowest_mileage"
        },
        {
            "origin_airport": "YUL, YYZ",
            "destination_airport": "EZE",
            "cabin": "business",
            "start_date": "2024-12-10",
            "end_date": "2024-12-11",
            "take": 500,
            "order_by": "lowest_mileage"
        },
        # {
        #     "origin_airport": "YVR, YUL, YYZ, YYC",
        #     "destination_airport": "CDG, ORY",
        #     "cabin": "business",
        #     "start_date": "2025-06-27",
        #     "end_date": "2025-07-15",
        #     "take": 500,
        #     "order_by": "lowest_mileage"
        # },
        #         {
        #     "origin_airport": "CDG, ORY",
        #     "destination_airport": "YVR, YYZ, YUL, YYC",
        #     "cabin": "business",
        #     "start_date": "2025-07-15",
        #     "end_date": "2025-08-01",
        #     "take": 500,
        #     "order_by": "lowest_mileage"
        # },
        {
            "origin_airport": "YVR, SFO, SEA, LAX",
            "destination_airport": "BKK, SIN",
            "cabin": "business",
            "start_date": "2024-12-31",
            "end_date": "2024-01-05",
            "take": 500,
            "order_by": "lowest_mileage"
        },
    ]

    mileage_threshold = 115000

    for idx, params in enumerate(parameter_sets, start=1):
        print(f"\nProcessing parameter set {idx}...\n")
        
        # Fetch and parse flight data
        response_text = fetch_flights(params)
        if response_text:
            data = parse_json(response_text)
            flights_list = data.get("data", [])
            
            if isinstance(flights_list, list):
                filtered_flights = filter_flights(flights_list, mileage_threshold)
                display_flights(filtered_flights)
                
                # Only send SMS if there are flights that meet my criteria
                if filtered_flights:
                    print("Flights found. Sending SMS notification...")
                    # send_sms_notification(filtered_flights)
                else:
                    print("No flights meet the criteria. SMS not sent.")
            else:
                print("Unexpected response structure. No flights found.")
        else:
            print("Failed to fetch data for this parameter set.")

if __name__ == "__main__":
    main()
