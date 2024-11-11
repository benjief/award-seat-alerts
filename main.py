import requests
import json
from config import API_KEY
from typing import List, Dict, Optional

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
        if flight.get("JAvailable") and flight.get("JMileageCost"):
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

def main() -> None:
    """Main function to execute the flight search and filtering."""
    params = {
        "origin_airport": "YUL,YYZ,IAD,ORD,EWR,YVR,IAH,LAX,SFO",
        "destination_airport": "GRU,EZE",
        "cabin": "business",
        "start_date": "2024-11-12",
        "end_date": "2024-12-10",
        "take": 500,
        "order_by": "lowest_mileage"
    }
    mileage_threshold = 90000  # Define your mileage threshold
    
    # Fetch and parse flight data
    response_text = fetch_flights(params)
    if response_text:
        data = parse_json(response_text)
        flights_list = data.get("data", [])
        
        if isinstance(flights_list, list):
            filtered_flights = filter_flights(flights_list, mileage_threshold)
            display_flights(filtered_flights)
        else:
            print("Unexpected response structure. No flights found.")

if __name__ == "__main__":
    main()
