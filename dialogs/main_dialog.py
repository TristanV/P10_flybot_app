# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from botbuilder.dialogs import (
    ComponentDialog,
    WaterfallDialog,
    WaterfallStepContext,
    DialogTurnResult,
)
from botbuilder.dialogs.prompts import TextPrompt, PromptOptions
from botbuilder.core import (
    MessageFactory,
    TurnContext,
    BotTelemetryClient,
    NullTelemetryClient,
)
from botbuilder.schema import InputHints, Attachment

from booking_details import BookingDetails
from flight_booking_recognizer import FlightBookingRecognizer
from helpers.luis_helper import LuisHelper, Intent
from .booking_dialog import BookingDialog

import json,re

class MainDialog(ComponentDialog):
    def __init__(
        self,
        luis_recognizer: FlightBookingRecognizer,
        booking_dialog: BookingDialog,
        telemetry_client: BotTelemetryClient = None,
    ):
        super(MainDialog, self).__init__(MainDialog.__name__)
        self.telemetry_client = telemetry_client or NullTelemetryClient()

        text_prompt = TextPrompt(TextPrompt.__name__)
        text_prompt.telemetry_client = self.telemetry_client

        booking_dialog.telemetry_client = self.telemetry_client

        wf_dialog = WaterfallDialog(
            "WFDialog", [self.intro_step, self.act_step, self.final_step]
        )
        wf_dialog.telemetry_client = self.telemetry_client

        self._luis_recognizer = luis_recognizer
        self._booking_dialog_id = booking_dialog.id

        self.add_dialog(text_prompt)
        self.add_dialog(booking_dialog)
        self.add_dialog(wf_dialog)

        self.initial_dialog_id = "WFDialog"

    async def intro_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        if not self._luis_recognizer.is_configured:
            await step_context.context.send_activity(
                MessageFactory.text(
                    "NOTE: LUIS is not configured. To enable all capabilities, add 'LuisAppId', 'LuisAPIKey' and "
                    "'LuisAPIHostName' to the appsettings.json file.",
                    input_hint=InputHints.ignoring_input,
                )
            )

            return await step_context.next(None)
        message_text = (
            str(step_context.options)
            if step_context.options
            else "Hello, I'm here to help you find the best flight for your next vacations! \r\n What kind of flight are you looking for?"
        )
        prompt_message = MessageFactory.text(
            message_text, message_text, InputHints.expecting_input
        )

        return await step_context.prompt(
            TextPrompt.__name__, PromptOptions(prompt=prompt_message)
        )

    async def act_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        if not self._luis_recognizer.is_configured:
            # LUIS is not configured, we just run the BookingDialog path with an empty BookingDetailsInstance.
            return await step_context.begin_dialog(
                self._booking_dialog_id, BookingDetails()
            )
 
        # Call LUIS and gather any potential booking details. (Note the TurnContext has the response to the prompt.)
        intent, luis_result = await LuisHelper.execute_luis_query(
            self._luis_recognizer, step_context.context
        ) 

        if intent == Intent.BOOK_FLIGHT.value and luis_result:
            # Show a warning for Origin and Destination if we can't resolve them.
            # await MainDialog._show_warning_for_unsupported_cities(
            #     step_context.context, luis_result
            # )

            # Run the BookingDialog giving it whatever details we have from the LUIS call.
            return await step_context.begin_dialog(self._booking_dialog_id, luis_result)

        # if intent == Intent.GET_WEATHER.value:
        #     get_weather_text = "TODO: get weather flow here"
        #     get_weather_message = MessageFactory.text(
        #         get_weather_text, get_weather_text, InputHints.ignoring_input
        #     )
        #     await step_context.context.send_activity(get_weather_message)

        else:
            didnt_understand_text = (
                "Sorry, I didn't get your demand. Please try asking in a different way"
            )
            didnt_understand_message = MessageFactory.text(
                didnt_understand_text, didnt_understand_text, InputHints.ignoring_input
            )
            await step_context.context.send_activity(didnt_understand_message)

        return await step_context.next(None)

    async def final_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        # If the child dialog ("BookingDialog") was cancelled or the user failed to confirm,
        # the Result here will be null.
        if step_context.result is not None:
            result = step_context.result

            # Now we have all the booking details call the booking service.

            # # If the call to the booking service was successful tell the user.
            # # time_property = Timex(result.travel_date)
            # # travel_date_msg = time_property.to_natural_language(datetime.now())
            # msg_txt = f"To satisfy your demand, I have you booked a flight to {result.destination} from {result.origin}, departure date is {result.start_date} and return date is {result.end_date}, your budget is : {result.budget}"
            # message = MessageFactory.text(msg_txt, msg_txt, InputHints.ignoring_input)
            # await step_context.context.send_activity(message)
            card = self.create_flight_ticket_attachment(result)
            response = MessageFactory.attachment(card)
            await step_context.context.send_activity(response)

        prompt_message = "Thanks for using this service. \r\n What else can I do for you?"
        return await step_context.replace_dialog(self.id, prompt_message)

    # @staticmethod
    # async def _show_warning_for_unsupported_cities(
    #     context: TurnContext, luis_result: BookingDetails
    # ) -> None:
    #     """
    #     Shows a warning if the requested From or To cities are recognized as entities but they are not in the Airport entity list.
    #     In some cases LUIS will recognize the From and To composite entities as a valid cities but the From and To Airport values
    #     will be empty if those entity values can't be mapped to a canonical item in the Airport.
    #     """
    #     if luis_result.unsupported_airports:
    #         message_text = (
    #             f"Sorry but the following airports are not supported:"
    #             f" {', '.join(luis_result.unsupported_airports)}"
    #         )
    #         message = MessageFactory.text(
    #             message_text, message_text, InputHints.ignoring_input
    #         )
    #         await context.send_activity(message)
 
     
    def replaceTemplateKeys(self, templateCard: dict, data: dict):
        """Replace keys in a template (card) by their values provided in the data set."""
        string_temp = str(templateCard)
        for key in data:
            pattern = "\${" + key + "}"
            string_temp = re.sub(pattern, str(data[key]), string_temp)
        return eval(string_temp)

    def create_flight_ticket_attachment(self, result):
        """Create an adaptive card."""
        # see https://messagecardplayground.azurewebsites.net/

        path =  "./bots/resources/bookedFlightCard.json"
        with open(path) as card_file:
            card = json.load(card_file)
        
        origin = result.origin
        destination = result.destination
        start_date = result.start_date
        end_date = result.end_date
        budget = result.budget

        templateCard = {
            "origin": origin, 
            "destination": destination,
            "start_date": start_date,
            "end_date": end_date,
            "budget": budget}

        flightCard = self.replaceTemplateKeys(card, templateCard)

        return Attachment(
            content_type="application/vnd.microsoft.card.adaptive", content=flightCard)