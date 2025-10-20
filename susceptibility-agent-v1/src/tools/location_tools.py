import os
import requests
from typing import Optional, Tuple, Dict, Type
from crewai.tools import BaseTool
from geopy.geocoders import Nominatim
from pydantic import BaseModel, Field


class LocationContextInput(BaseModel):
    """Input schema for location context tool."""
    location_input: Optional[str] = Field(
        default=None,
        description="Location name, coordinates (e.g., '40.4168, -3.7038'), or None for IP-based detection"
    )

class LocationContextTool(BaseTool):
    """Retrieves current location and provides tactical geographic context"""
    name: str = "Location Context Tool"
    description: str = (
        "Determines current geographic location and provides tactical context including "
        "coordinates, terrain type, and nearby strategic points. "
        "Input: location_input (optional string - location name, coordinates, or None for IP detection)"
    )
    args_schema: Type[BaseModel] = LocationContextInput

    def _get_geolocator(self):
        """Get geolocator instance"""
        return Nominatim(user_agent="tactical_crew_location")
    
    def _run(self, location_input: Optional[str] = None) -> str:
        try:
            # Try to get location from multiple sources
            coordinates = self._get_location(location_input)
            
            if not coordinates:
                return """
                LOCATION CONTEXT REPORT:
                =======================
                Status: Unable to determine location
                Recommendation: Provide manual coordinates or location name
                =======================
                """
            
            lat, lon = coordinates
            
            # Get detailed location information
            location_details = self._get_location_details(lat, lon)
            terrain_info = self._analyze_terrain_context(lat, lon)
            strategic_context = self._get_strategic_context(lat, lon)
            
            formatted_output = f"""
            LOCATION CONTEXT REPORT:
            =======================
            Coordinates: {lat:.6f}, {lon:.6f}
            Location: {location_details.get('address', 'Unknown')}
            Country: {location_details.get('country', 'Unknown')}
            Region: {location_details.get('state', 'Unknown')}
            City: {location_details.get('city', 'Unknown')}
            
            TERRAIN ANALYSIS:
            {terrain_info}
            
            STRATEGIC CONTEXT:{strategic_context}
            
            TACTICAL IMPLICATIONS:
            - Elevation and terrain affect line of sight
            - Urban areas provide cover but limit movement
            - Proximity to infrastructure affects logistics
            - Border regions may have increased security presence
            =======================
            """
            return formatted_output.strip()
            
        except Exception as e:
            return f"Error retrieving location context: {str(e)}"
    
    def _get_location(self, location_input: Optional[str] = None) -> Optional[Tuple[float, float]]:
        """Get location coordinates from various sources"""
        
        # Method 1: If specific location provided, geocode it
        if location_input and not self._is_coordinates(location_input):
            try:
                geolocator = self._get_geolocator()
                location = geolocator.geocode(location_input)
                if location:
                    return (location.latitude, location.longitude)
            except Exception:
                pass
        
        # Method 2: If coordinates provided directly
        if location_input and self._is_coordinates(location_input):
            try:
                coords = location_input.replace('°', '').replace('N', '').replace('W', '').replace('E', '').replace('S', '')
                lat, lon = map(float, coords.split(','))
                return (lat, lon)
            except Exception:
                pass
        
        # Method 3: IP-based geolocation (approximate)
        try:
            response = requests.get('http://ip-api.com/json/', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'success':
                    return (data['lat'], data['lon'])
        except Exception:
            pass
        
        return None
    
    def _is_coordinates(self, text: str) -> bool:
        """Check if text contains coordinate-like format"""
        return '°' in text or (',' in text and any(c.isdigit() for c in text))
    
    def _get_location_details(self, lat: float, lon: float) -> Dict[str, str]:
        """Get detailed location information with multiple fallback methods"""
        
        # Method 1: Try Nominatim geocoder
        try:
            geolocator = self._get_geolocator()
            location = geolocator.reverse(f"{lat}, {lon}", timeout=10)
            
            if location:
                if hasattr(location, 'raw') and location.raw:
                    address_data = location.raw.get('address', {})
                    
                    country = (address_data.get('country') or 
                             address_data.get('country_code', '').upper() or 
                             'Unknown')
                    
                    state = (address_data.get('state') or 
                            address_data.get('province') or 
                            address_data.get('region') or 
                            'Unknown')
                    
                    city = (address_data.get('city') or 
                           address_data.get('town') or 
                           address_data.get('village') or 
                           address_data.get('municipality') or 
                           'Unknown')
                    
                    if country != 'Unknown' or state != 'Unknown' or city != 'Unknown':
                        return {
                            'address': location.address or 'Address unavailable',
                            'country': country,
                            'state': state,
                            'city': city
                        }
                
        except Exception as e:
            print(f"Nominatim geocoding failed: {e}")
        
        # Method 2: Try online geocoding service as fallback
        try:
            response = requests.get(
                f'http://api.openweathermap.org/geo/1.0/reverse?lat={lat}&lon={lon}&limit=1&appid=demo',
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if data:
                    location_data = data[0]
                    return {
                        'address': f"{location_data.get('name', 'Unknown')}, {location_data.get('country', 'Unknown')}",
                        'country': location_data.get('country', 'Unknown'),
                        'state': location_data.get('state', 'Unknown'),
                        'city': location_data.get('name', 'Unknown')
                    }
        except Exception:
            pass
        
        return {'address': 'Location details unavailable', 'country': 'Unknown', 'state': 'Unknown', 'city': 'Unknown'}
    
    def _analyze_terrain_context(self, lat: float, lon: float) -> str:
        """Analyze terrain and geographic context"""
        try:
            terrain_type = "Mixed terrain"
            
            # Simple heuristics (you could enhance with elevation APIs)
            if abs(lat) > 60:
                terrain_type = "Arctic/Subarctic region"
            elif abs(lat) < 23.5:
                terrain_type = "Tropical region"
            elif -120 < lon < -60 and 25 < lat < 50:
                terrain_type = "North American continental"
            elif -10 < lon < 50 and 35 < lat < 70:
                terrain_type = "European region"
            
            return f"Terrain Type: {terrain_type}"
            
        except Exception:
            return "Terrain analysis unavailable"
    
    def _get_strategic_context(self, lat: float, lon: float) -> str:
        """Provide strategic context for the location"""
        try:
            context_string = (
                "\n"
                "            - Assess proximity to major urban centers\n"
                "            - Consider transportation infrastructure access\n"
                "            - Evaluate communication coverage in area\n"
                "            - Check for restricted or sensitive zones nearby"
            )
        
            return context_string
            
        except Exception:
            return "Strategic context analysis unavailable"

def add_location_context_to_input(mission_input: str, location: Optional[str] = None) -> str:
    """
    Utility function to enhance mission input with location context
    """
    location_tool = LocationContextTool()
    location_context = location_tool._run(location)
    
    enhanced_input = f"""
    MISSION INPUT:
    ===================================

    ORIGINAL MISSION DATA:
    =====================
    {mission_input}

    LOCATION CONTEXT:
    =====================
    {location_context}
    """
    return enhanced_input