# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
from enum import Enum
from typing import Dict
from botbuilder.ai.luis import LuisRecognizer
from botbuilder.core import IntentScore, TopIntent, TurnContext

from booking_details import BookingDetails


luis_bot_entities_mapping = {'or_city': 'origin', 'dst_city':'destination', 'str_date': 'start_date', 'end_date': 'end_date', 'budget': 'budget'}

luis_entities_type = {'or_city': 'geographyV2_city', 'dst_city':'geographyV2_city', 'str_date': 'datetime', 'end_date': 'datetime', 'budget': 'number'}


class Intent(Enum):
    BOOK_FLIGHT = "Book"
    CANCEL = "Cancel"
    NONE_INTENT = "None"


def top_intent(intents: Dict[Intent, dict]) -> TopIntent:
    max_intent = Intent.NONE_INTENT
    max_value = 0.0

    for intent, value in intents:
        intent_score = IntentScore(value)
        if intent_score.score > max_value:
            max_intent, max_value = intent, intent_score.score

    return TopIntent(max_intent, max_value)


class LuisHelper:
    @staticmethod
    async def execute_luis_query(
        luis_recognizer: LuisRecognizer, turn_context: TurnContext
    ) -> (Intent, object):
        """
        Returns an object with preformatted LUIS results for the bot's dialogs to consume.
        """
        result = None
        intent = None

        try:
            recognizer_result = await luis_recognizer.recognize(turn_context)
            intent = recognizer_result.get_top_scoring_intent().intent
            # intent = (
            #     sorted(
            #         recognizer_result.intents,
            #         key=recognizer_result.intents.get,
            #         reverse=True,
            #     )[:1][0]
            #     if recognizer_result.intents
            #     else None
            # )

            if intent == Intent.BOOK_FLIGHT.value:       
                # print("Book flight intent recognized",recognizer_result)         
                # print("Your prompt was",recognizer_result['text'])
                # print("---")
                result = BookingDetails()
                
                result.initial_prompt = recognizer_result.text  

                for (key, type) in luis_entities_type.items():
                    # print("--- fetching entity item ",key,type)
                    entity = LuisHelper._get_entity(recognizer_result, key, type)
                # # We need to get the result from the LUIS JSON which at every level returns an array.
                # to_entities = recognizer_result.entities.get("$instance", {}).get(
                #     "To", []
                # )
                # if len(to_entities) > 0:
                #     if recognizer_result.entities.get("To", [{"$instance": {}}])[0][
                #         "$instance"
                #     ]:
                #         result.destination = to_entities[0]["text"].capitalize()
                #     else:
                #         result.unsupported_airports.append(
                #             to_entities[0]["text"].capitalize()
                #         )

                # from_entities = recognizer_result.entities.get("$instance", {}).get(
                #     "From", []
                # )
                # if len(from_entities) > 0:
                #     if recognizer_result.entities.get("From", [{"$instance": {}}])[0][
                #         "$instance"
                #     ]:
                #         result.origin = from_entities[0]["text"].capitalize()
                #     else:
                #         result.unsupported_airports.append(
                #             from_entities[0]["text"].capitalize()
                #         )

                # # This value will be a TIMEX. And we are only interested in a Date so grab the first result and drop
                # # the Time part. TIMEX is a format that represents DateTime expressions that include some ambiguity.
                # # e.g. missing a Year.
                # date_entities = recognizer_result.entities.get("datetime", [])
                # if date_entities:
                #     timex = date_entities[0]["timex"]

                #     if timex:
                #         datetime = timex[0].split("T")[0]

                #         result.travel_date = datetime

                # else:
                #     result.travel_date = None

                    if entity is not None:
                        setattr(result, luis_bot_entities_mapping[key], entity)
                     
        except Exception as exception:
            print(exception)

        return intent, result
 
    def _get_entity(recognizer_result, key, type):
        """
        Returns the entity value for a given key and its corresponding type, extracted from the LUIS result.
        """
         
        # entity "key" not found
        if (recognizer_result.entities.get("$instance") is None
            or recognizer_result.entities.get(key) is None
            or len(recognizer_result.entities.get(key)) == 0) :
            return None

        score = 0
        index = None 
        # get the index of the entity "key" having the best score in the recognizer results
        for i, entity in enumerate(recognizer_result.entities.get("$instance").get(key)):
            if entity['score'] > score:
                score = entity['score']
                index = i

        selected_entity = recognizer_result.entities.get("$instance").get(key)[index]

        score = 100
        index = None
 

        # if the entity type is absent, let's consider the entity missing
        if recognizer_result.entities.get(type) is None:
            return None

        # among the types in the recognizer results, let's find the one now that minimizes the overlap between the selected entity
        for i, entity in enumerate(recognizer_result.entities.get("$instance").get(type)):
            s = abs(entity['startIndex'] - selected_entity['startIndex']) + abs(entity['endIndex'] - selected_entity['endIndex'])
            if s < score:
                score = s
                index = i


        # if the entity type was not found in the recognized result, let's consider this entity as missing
        if (index is None
            or len(recognizer_result.entities.get(type)) <= index):
            return None
         
        # finally convert the result and return the entity value
        # TODO : handle datetime ranges and resolutions
        return (
            recognizer_result.entities.get(type)[index].capitalize()
            if type == 'geographyV2_city'
            else recognizer_result.entities.get(type)[index]["timex"][0]
            if type == 'datetime'
            else recognizer_result.entities.get(type)[index]
            if type == 'number'
            else None
        )