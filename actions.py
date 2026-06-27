"""
actions.py - Actions personnalisées pour le chatbot de l'agence de voyage
Utilise l'API Amadeus pour rechercher des vols et des hôtels
"""

import logging
import json
import random
from typing import Any, Dict, List, Optional, Text
from datetime import datetime, timedelta

from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, AllSlotsReset, ConversationPaused
from rasa_sdk.types import DomainDict

logger = logging.getLogger(__name__)

# ─── Configuration API Amadeus ─────────────────────────────────────────────────
# Pour utiliser l'API réelle, inscrivez-vous sur https://developers.amadeus.com/
# et remplacez ces valeurs par vos vraies clés
AMADEUS_API_KEY = "YOUR_AMADEUS_API_KEY"
AMADEUS_API_SECRET = "YOUR_AMADEUS_API_SECRET"
AMADEUS_BASE_URL = "https://test.api.amadeus.com"

# Correspondances codes IATA pour les villes arabes courantes
CITY_TO_IATA = {
    "الدار البيضاء": "CMN",
    "مراكش": "RAK",
    "الرباط": "RBA",
    "أكادير": "AGA",
    "فاس": "FEZ",
    "طنجة": "TNG",
    "باريس": "CDG",
    "لندن": "LHR",
    "مدريد": "MAD",
    "روما": "FCO",
    "برلين": "BER",
    "أمستردام": "AMS",
    "إسطنبول": "IST",
    "دبي": "DXB",
    "الرياض": "RUH",
    "القاهرة": "CAI",
    "تونس": "TUN",
    "الجزائر": "ALG",
    "نيويورك": "JFK",
    "بيروت": "BEY",
    "أبوظبي": "AUH",
    "الكويت": "KWI",
    "عمّان": "AMM",
    "الدوحة": "DOH",
}

CLASSE_MAPPING = {
    "اقتصادية": "ECONOMY",
    "رجال أعمال": "BUSINESS",
    "أولى": "FIRST",
    "سياحية": "ECONOMY",
}


def get_amadeus_token() -> Optional[str]:
    """Récupère le token d'accès Amadeus OAuth2"""
    try:
        import requests
        response = requests.post(
            f"{AMADEUS_BASE_URL}/v1/security/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": AMADEUS_API_KEY,
                "client_secret": AMADEUS_API_SECRET,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10,
        )
        if response.status_code == 200:
            return response.json().get("access_token")
    except Exception as e:
        logger.error(f"Erreur lors de l'obtention du token Amadeus: {e}")
    return None


def search_flights_api(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str] = None,
    travel_class: str = "ECONOMY",
    adults: int = 1,
) -> List[Dict]:
    """Recherche de vols via l'API Amadeus Flight Offers"""
    try:
        import requests
        token = get_amadeus_token()
        if not token:
            raise ValueError("Token API non disponible")

        params = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": departure_date,
            "adults": adults,
            "travelClass": travel_class,
            "max": 3,
            "currencyCode": "MAD",
        }
        if return_date:
            params["returnDate"] = return_date

        response = requests.get(
            f"{AMADEUS_BASE_URL}/v2/shopping/flight-offers",
            headers={"Authorization": f"Bearer {token}"},
            params=params,
            timeout=15,
        )
        if response.status_code == 200:
            return response.json().get("data", [])[:3]
    except Exception as e:
        logger.error(f"Erreur API vols: {e}")
    return []


def search_hotels_api(city_code: str, adults: int = 1, rating: str = "4,5") -> List[Dict]:
    """Recherche d'hôtels via l'API Amadeus Hotel List"""
    try:
        import requests
        token = get_amadeus_token()
        if not token:
            raise ValueError("Token API non disponible")

        response = requests.get(
            f"{AMADEUS_BASE_URL}/v1/reference-data/locations/hotels/by-city",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "cityCode": city_code,
                "ratings": rating,
                "amenities": "SWIMMING_POOL,SPA,RESTAURANT",
            },
            timeout=15,
        )
        if response.status_code == 200:
            return response.json().get("data", [])[:3]
    except Exception as e:
        logger.error(f"Erreur API hôtels: {e}")
    return []


def generate_mock_flights(
    ville_depart: str,
    ville_destination: str,
    date_depart: str,
    classe: str,
    type_vol: str,
) -> List[Dict]:
    """Génère des données de vols simulées si l'API n'est pas disponible"""
    airlines = [
        {"name": "Royal Air Maroc", "code": "AT"},
        {"name": "Air Arabia Maroc", "code": "3O"},
        {"name": "Transavia", "code": "TO"},
    ]
    flights = []
    base_price = {"اقتصادية": 2500, "رجال أعمال": 8000, "أولى": 15000}.get(classe, 2500)

    for i, airline in enumerate(airlines):
        price = base_price + random.randint(-500, 2000)
        departure_hour = 6 + (i * 5)
        duration = random.randint(2, 14)
        flight = {
            "id": i + 1,
            "airline": airline["name"],
            "flight_number": f"{airline['code']}{random.randint(100, 999)}",
            "origin": ville_depart,
            "destination": ville_destination,
            "departure": f"{date_depart} {departure_hour:02d}:00",
            "arrival": f"{date_depart} {(departure_hour + duration):02d}:30",
            "duration": f"{duration}h 30min",
            "class": classe,
            "type": type_vol,
            "price": price,
            "currency": "درهم مغربي",
            "seats_available": random.randint(5, 30),
        }
        flights.append(flight)
    return flights


def generate_mock_hotels(
    ville: str,
    categorie: str,
    quartier: Optional[str],
    nombre_personnes: int,
) -> List[Dict]:
    """Génère des données d'hôtels simulées si l'API n'est pas disponible"""
    stars_count = {"3 نجوم": 3, "4 نجوم": 4, "5 نجوم": 5, "فاخر": 5}.get(categorie, 4)
    base_price = {3: 400, 4: 700, 5: 1200}.get(stars_count, 700)
    hotel_names = [
        f"فندق {ville} الدولي",
        f"فندق بلازا {ville}",
        f"فندق ريجنسي {ville}",
    ]
    hotels = []
    for i, name in enumerate(hotel_names):
        price_per_night = base_price + random.randint(-100, 300)
        hotel = {
            "id": i + 1,
            "name": name,
            "city": ville,
            "district": quartier or "المركز",
            "category": categorie,
            "stars": stars_count,
            "capacity": nombre_personnes,
            "price_per_night": price_per_night * nombre_personnes,
            "currency": "درهم مغربي",
            "amenities": ["واي فاي مجاني", "مسبح", "مطعم", "موقف سيارات"][:stars_count - 1],
            "rating": round(random.uniform(7.5, 9.8), 1),
            "available": True,
        }
        hotels.append(hotel)
    return hotels


def format_flight_message(flights: List[Dict]) -> str:
    """Formate les résultats de vol en message arabe"""
    if not flights:
        return "عذراً، لم يتم العثور على رحلات متاحة لهذا المسار."

    message = "✈️ **وجدنا لك الرحلات التالية:**\n\n"
    for flight in flights:
        message += (
            f"🔹 **الخيار {flight['id']}**: {flight['airline']}\n"
            f"   رقم الرحلة: {flight['flight_number']}\n"
            f"   المغادرة: {flight['departure']} ← {flight['arrival']}\n"
            f"   المدة: {flight['duration']}\n"
            f"   الدرجة: {flight['class']}\n"
            f"   السعر: {flight['price']:,} {flight['currency']}\n"
            f"   المقاعد المتاحة: {flight['seats_available']}\n\n"
        )
    message += "💡 اختر الخيار الذي يناسبك (1، 2 أو 3)"
    return message


def format_hotel_message(hotels: List[Dict]) -> str:
    """Formate les résultats d'hôtel en message arabe"""
    if not hotels:
        return "عذراً، لم يتم العثور على فنادق متاحة."

    message = "🏨 **وجدنا لك الفنادق التالية:**\n\n"
    for hotel in hotels:
        stars_str = "⭐" * hotel["stars"]
        amenities_str = " | ".join(hotel["amenities"])
        message += (
            f"🔹 **الخيار {hotel['id']}**: {hotel['name']}\n"
            f"   التصنيف: {stars_str} ({hotel['category']})\n"
            f"   الموقع: {hotel['city']} - {hotel['district']}\n"
            f"   الطاقة: {hotel['capacity']} أشخاص\n"
            f"   السعر: {hotel['price_per_night']:,} {hotel['currency']} / ليلة\n"
            f"   التقييم: {hotel['rating']}/10\n"
            f"   الخدمات: {amenities_str}\n\n"
        )
    message += "💡 اختر الخيار الذي يناسبك (1، 2 أو 3)"
    return message


# ─── ACTIONS RASA ──────────────────────────────────────────────────────────────

class ActionSearchFlights(Action):
    """Recherche des vols selon les critères fournis par l'utilisateur"""

    def name(self) -> Text:
        return "action_search_flights"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[Dict[Text, Any]]:
        ville_depart = tracker.get_slot("ville_depart") or "الدار البيضاء"
        ville_destination = tracker.get_slot("ville_destination") or "باريس"
        date_depart = tracker.get_slot("date_depart") or str(datetime.now().date() + timedelta(days=30))
        date_retour = tracker.get_slot("date_retour")
        classe = tracker.get_slot("classe") or "اقتصادية"
        type_vol = tracker.get_slot("type_vol") or "ذهاب فقط"

        dispatcher.utter_message(
            text=f"🔍 أبحث عن رحلات من {ville_depart} إلى {ville_destination}..."
        )

        # Essayer l'API réelle, sinon utiliser les données simulées
        origin_code = CITY_TO_IATA.get(ville_depart)
        destination_code = CITY_TO_IATA.get(ville_destination)
        api_flights = []

        if origin_code and destination_code:
            travel_class = CLASSE_MAPPING.get(classe, "ECONOMY")
            api_flights = search_flights_api(
                origin=origin_code,
                destination=destination_code,
                departure_date=date_depart,
                return_date=date_retour if type_vol == "ذهاب وعودة" else None,
                travel_class=travel_class,
            )

        # Fallback sur les données simulées
        if not api_flights:
            logger.info("Utilisation des données simulées pour les vols")
            flights = generate_mock_flights(
                ville_depart, ville_destination, date_depart, classe, type_vol
            )
        else:
            # Formater les données API
            flights = []
            for i, offer in enumerate(api_flights[:3]):
                itinerary = offer.get("itineraries", [{}])[0]
                segment = itinerary.get("segments", [{}])[0]
                price = offer.get("price", {})
                flights.append({
                    "id": i + 1,
                    "airline": segment.get("carrierCode", "غير معروف"),
                    "flight_number": f"{segment.get('carrierCode','')}{segment.get('number','')}",
                    "origin": segment.get("departure", {}).get("iataCode", ville_depart),
                    "destination": segment.get("arrival", {}).get("iataCode", ville_destination),
                    "departure": segment.get("departure", {}).get("at", date_depart),
                    "arrival": segment.get("arrival", {}).get("at", ""),
                    "duration": itinerary.get("duration", ""),
                    "class": classe,
                    "type": type_vol,
                    "price": float(price.get("total", 0)),
                    "currency": price.get("currency", "MAD"),
                    "seats_available": offer.get("numberOfBookableSeats", 1),
                })

        message = format_flight_message(flights)
        dispatcher.utter_message(text=message)

        # Stocker les offres dans le slot pour la sélection
        return [
            SlotSet("current_offer", json.dumps(flights, ensure_ascii=False)),
            SlotSet("reservation_type", "flight"),
        ]


class ActionSearchHotels(Action):
    """Recherche des hôtels selon les critères fournis par l'utilisateur"""

    def name(self) -> Text:
        return "action_search_hotels"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[Dict[Text, Any]]:
        ville_hotel = tracker.get_slot("ville_hotel") or "باريس"
        categorie_hotel = tracker.get_slot("categorie_hotel") or "4 نجوم"
        quartier = tracker.get_slot("quartier")
        nombre_personnes_str = tracker.get_slot("nombre_personnes") or "1"
        nombre_personnes = int("".join(filter(str.isdigit, nombre_personnes_str)) or "1")

        dispatcher.utter_message(
            text=f"🔍 أبحث عن فنادق {categorie_hotel} في {ville_hotel}..."
        )

        # Essayer l'API réelle
        city_code = CITY_TO_IATA.get(ville_hotel)
        api_hotels = []
        if city_code:
            stars_map = {"3 نجوم": "3", "4 نجوم": "4", "5 نجوم": "5", "فاخر": "5"}
            rating = stars_map.get(categorie_hotel, "4")
            api_hotels = search_hotels_api(city_code=city_code, adults=nombre_personnes, rating=rating)

        # Fallback simulé
        if not api_hotels:
            logger.info("Utilisation des données simulées pour les hôtels")
            hotels = generate_mock_hotels(ville_hotel, categorie_hotel, quartier, nombre_personnes)
        else:
            hotels = []
            for i, hotel in enumerate(api_hotels[:3]):
                hotels.append({
                    "id": i + 1,
                    "name": hotel.get("name", f"فندق {i+1}"),
                    "city": ville_hotel,
                    "district": quartier or hotel.get("address", {}).get("cityName", "المركز"),
                    "category": categorie_hotel,
                    "stars": int(hotel.get("rating", 4)),
                    "capacity": nombre_personnes,
                    "price_per_night": random.randint(500, 2000),
                    "currency": "درهم مغربي",
                    "amenities": ["واي فاي مجاني", "مسبح"],
                    "rating": round(random.uniform(7.5, 9.5), 1),
                    "available": True,
                })

        message = format_hotel_message(hotels)
        dispatcher.utter_message(text=message)

        return [
            SlotSet("current_offer", json.dumps(hotels, ensure_ascii=False)),
            SlotSet("reservation_type", "hotel"),
        ]


class ActionSelectOption(Action):
    """Permet à l'utilisateur de sélectionner une option parmi les offres proposées"""

    def name(self) -> Text:
        return "action_select_option"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[Dict[Text, Any]]:
        option_id = tracker.get_slot("option_id")
        current_offer_str = tracker.get_slot("current_offer")
        reservation_type = tracker.get_slot("reservation_type")

        if not option_id or not current_offer_str:
            dispatcher.utter_message(text="عذراً، لم أفهم اختيارك. هل يمكنك تحديد رقم الخيار؟")
            return []

        try:
            offers = json.loads(current_offer_str)
            # Normaliser l'ID
            num_map = {"الأول": "1", "الثاني": "2", "الثالث": "3", "الاول": "1"}
            option_num = int(num_map.get(str(option_id), str(option_id)))
            selected = next((o for o in offers if o["id"] == option_num), None)

            if not selected:
                dispatcher.utter_message(
                    text=f"عذراً، الخيار {option_id} غير متوفر. يرجى اختيار رقم بين 1 و {len(offers)}"
                )
                return []

            if reservation_type == "flight":
                message = (
                    f"✅ **لقد اخترت:**\n\n"
                    f"✈️ رحلة {selected['airline']} - {selected['flight_number']}\n"
                    f"من {selected['origin']} إلى {selected['destination']}\n"
                    f"المغادرة: {selected['departure']}\n"
                    f"الدرجة: {selected['class']}\n"
                    f"السعر الإجمالي: **{selected['price']:,} {selected['currency']}**\n\n"
                    f"هل تريد تأكيد هذا الحجز؟"
                )
            else:
                message = (
                    f"✅ **لقد اخترت:**\n\n"
                    f"🏨 {selected['name']}\n"
                    f"التصنيف: {'⭐' * selected['stars']}\n"
                    f"الموقع: {selected['city']} - {selected['district']}\n"
                    f"للـ {selected['capacity']} أشخاص\n"
                    f"السعر: **{selected['price_per_night']:,} {selected['currency']} / ليلة**\n\n"
                    f"هل تريد تأكيد هذا الحجز؟"
                )

            dispatcher.utter_message(text=message)

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.error(f"Erreur lors de la sélection: {e}")
            dispatcher.utter_message(text="عذراً، حدث خطأ. يرجى المحاولة مرة أخرى.")

        return []


class ActionChangeOption(Action):
    """Met à jour les critères et propose de nouvelles options"""

    def name(self) -> Text:
        return "action_change_option"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[Dict[Text, Any]]:
        reservation_type = tracker.get_slot("reservation_type")

        dispatcher.utter_message(
            text=(
                "بالتأكيد! يمكنني تعديل بحثك. ما الذي تريد تغييره؟\n\n"
                + (
                    "- تاريخ المغادرة\n- تاريخ العودة\n- الدرجة (اقتصادية/رجال أعمال/أولى)\n- المدينة"
                    if reservation_type == "flight"
                    else "- فئة الفندق (3/4/5 نجوم)\n- الحي أو المنطقة\n- عدد الأشخاص\n- المدينة"
                )
            )
        )

        # Réinitialiser les slots selon le type
        events = []
        if reservation_type == "flight":
            events = [
                SlotSet("date_depart", None),
                SlotSet("date_retour", None),
                SlotSet("classe", None),
                SlotSet("current_offer", None),
            ]
        else:
            events = [
                SlotSet("categorie_hotel", None),
                SlotSet("quartier", None),
                SlotSet("nombre_personnes", None),
                SlotSet("current_offer", None),
            ]

        return events


class ActionConfirmReservation(Action):
    """Confirme la réservation, remercie le client et termine la conversation"""

    def name(self) -> Text:
        return "action_confirm_reservation"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[Dict[Text, Any]]:
        reservation_type = tracker.get_slot("reservation_type")

        # Générer un numéro de confirmation unique
        import random, string
        ref_num = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

        if reservation_type == "flight":
            confirmation_msg = (
                f"🎉 **تم تأكيد حجزك بنجاح!**\n\n"
                f"رقم المرجع: **{ref_num}**\n"
                f"تاريخ الحجز: {current_time}\n\n"
                f"✈️ تفاصيل رحلتك:\n"
                f"من: {tracker.get_slot('ville_depart')}\n"
                f"إلى: {tracker.get_slot('ville_destination')}\n"
                f"تاريخ المغادرة: {tracker.get_slot('date_depart')}\n"
                f"الدرجة: {tracker.get_slot('classe')}\n\n"
                f"📧 سيتم إرسال تفاصيل التذكرة إلى بريدك الإلكتروني قريباً.\n\n"
                f"شكراً جزيلاً لثقتك في وكالتنا! نتمنى لك رحلة موفقة وممتعة! ✈️🌍"
            )
        else:
            confirmation_msg = (
                f"🎉 **تم تأكيد حجزك بنجاح!**\n\n"
                f"رقم المرجع: **{ref_num}**\n"
                f"تاريخ الحجز: {current_time}\n\n"
                f"🏨 تفاصيل إقامتك:\n"
                f"المدينة: {tracker.get_slot('ville_hotel')}\n"
                f"فئة الفندق: {tracker.get_slot('categorie_hotel')}\n"
                f"عدد الأشخاص: {tracker.get_slot('nombre_personnes')}\n\n"
                f"📧 سيتم إرسال تأكيد الحجز إلى بريدك الإلكتروني قريباً.\n\n"
                f"شكراً جزيلاً لثقتك في وكالتنا! نتمنى لك إقامة موفقة ومريحة! 🏨🌟"
            )

        dispatcher.utter_message(text=confirmation_msg)

        # Réinitialiser tous les slots après confirmation
        return [AllSlotsReset()]


# ─── VALIDATION DES FORMULAIRES ────────────────────────────────────────────────

class ValidateFlightForm(FormValidationAction):
    """Valide les données du formulaire de réservation de vol"""

    def name(self) -> Text:
        return "validate_flight_form"

    def validate_ville_depart(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        if slot_value and len(str(slot_value).strip()) > 1:
            return {"ville_depart": slot_value}
        dispatcher.utter_message(text="عذراً، لم أفهم مدينة المغادرة. هل يمكنك إعادة ذكرها؟")
        return {"ville_depart": None}

    def validate_ville_destination(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        if slot_value and len(str(slot_value).strip()) > 1:
            return {"ville_destination": slot_value}
        dispatcher.utter_message(text="عذراً، لم أفهم مدينة الوصول. هل يمكنك إعادة ذكرها؟")
        return {"ville_destination": None}

    def validate_classe(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        valid_classes = ["اقتصادية", "رجال أعمال", "أولى", "سياحية"]
        if slot_value in valid_classes:
            return {"classe": slot_value}
        dispatcher.utter_message(
            text="يرجى اختيار درجة صحيحة: اقتصادية، رجال أعمال، أو أولى"
        )
        return {"classe": None}

    def validate_type_vol(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        if slot_value and ("ذهاب" in str(slot_value) or "عودة" in str(slot_value)):
            return {"type_vol": slot_value}
        dispatcher.utter_message(
            text="يرجى تحديد نوع الرحلة: ذهاب فقط أم ذهاب وعودة؟"
        )
        return {"type_vol": None}


class ValidateHotelForm(FormValidationAction):
    """Valide les données du formulaire de réservation d'hôtel"""

    def name(self) -> Text:
        return "validate_hotel_form"

    def validate_ville_hotel(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        if slot_value and len(str(slot_value).strip()) > 1:
            return {"ville_hotel": slot_value}
        dispatcher.utter_message(text="عذراً، لم أفهم اسم المدينة. هل يمكنك إعادة ذكرها؟")
        return {"ville_hotel": None}

    def validate_nombre_personnes(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        if slot_value:
            return {"nombre_personnes": str(slot_value)}
        dispatcher.utter_message(text="يرجى تحديد عدد الأشخاص.")
        return {"nombre_personnes": None}
