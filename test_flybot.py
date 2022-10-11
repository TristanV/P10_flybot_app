import asyncio
import pytest
# launch the current test with
# pytest test_flybot.py --asyncio-mode=strict --disable-warnings

from botbuilder.ai.luis import LuisApplication, LuisRecognizer, LuisPredictionOptions

from botbuilder.core import TurnContext 
from botbuilder.core.adapters import TestAdapter 

from config import DefaultConfig

from flight_booking_recognizer import FlightBookingRecognizer
from booking_details import BookingDetails
from helpers.luis_helper import LuisHelper, Intent

import json

CONFIG = DefaultConfig()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
def check_pytest_asyncio_installed():
    import os
    from importlib import util
    if not util.find_spec("pytest_asyncio"):
        print("You need to install pytest-asyncio first!",file=sys.stderr)
        sys.exit(os.EX_SOFTWARE)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
async def return_after_sleep(res):
    return await asyncio.sleep(2, result=res)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
def test_luis_configured():
    """Check LUIS configuration
    """ 
    luis_is_configured = (
        CONFIG.LUIS_APP_ID
        and CONFIG.LUIS_API_KEY
        and CONFIG.LUIS_API_HOST_NAME
    )
    # Set the recognizer options depending on which endpoint version you want to use e.g v2 or v3.
    # More details can be found in https://docs.microsoft.com/azure/cognitive-services/luis/luis-migration-api-v3
    luis_application = LuisApplication(
        CONFIG.LUIS_APP_ID,
        CONFIG.LUIS_API_KEY,
        "https://" + CONFIG.LUIS_API_HOST_NAME,
    )

    options = LuisPredictionOptions() 

    recognizer = LuisRecognizer(luis_application, prediction_options=options)
    assert recognizer is not None

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #  
@pytest.mark.asyncio
async def test_luis_results():
    """Check LUIS *Top intent* and some utterances
    """ 

    luis_is_configured = (
        CONFIG.LUIS_APP_ID
        and CONFIG.LUIS_API_KEY
        and CONFIG.LUIS_API_HOST_NAME
    )
    

    assert luis_is_configured

    if luis_is_configured:  

        # Set the recognizer options depending on which endpoint version you want to use e.g v2 or v3.
        # More details can be found in https://docs.microsoft.com/azure/cognitive-services/luis/luis-migration-api-v3
        luis_application = LuisApplication(
            CONFIG.LUIS_APP_ID,
            CONFIG.LUIS_API_KEY,
            "https://" + CONFIG.LUIS_API_HOST_NAME,
        )

        recognizer = FlightBookingRecognizer(CONFIG)

        async def exec_test(turn_context: TurnContext):
            intent, result = await LuisHelper.execute_luis_query(recognizer, turn_context)
            json_activity = json.dumps(
                    {
                        "intent": intent,
                        "booking_details": None if not hasattr(result, "__dict__") else result.__dict__,
                    }
                )
            # print("activity",json_activity)
            await turn_context.send_activity(
                json_activity
            )

        adapter = TestAdapter(exec_test)

        query ="I want to Book a flight from Marseille to Paris starting 12 october 2022 and returning 19 october 2022 with a budget of 500" 
        expected_top_intent =  Intent.BOOK_FLIGHT.value
        expected_booking_details=BookingDetails(
                        initial_prompt = query,
                        destination = "Paris",
                        origin = "Marseille",
                        start_date = "2022-10-12",
                        end_date = "2022-10-19",
                        budget = 500
                    ).__dict__
        # print("expected activity",expected_booking_details)

        await adapter.test(
            query,
            json.dumps(
                {
                    "intent": expected_top_intent,
                    "booking_details": expected_booking_details,
                }
            ),
        )


