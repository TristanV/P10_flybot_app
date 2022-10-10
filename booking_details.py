# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.


class BookingDetails:
    def __init__(
        self,
        initial_prompt: str = None,
        destination: str = None,
        origin: str = None,
        start_date: str = None,
        end_date: str = None,
        budget: int = None
    ):    
#        if unsupported_airports is None:
#            unsupported_airports = []
        self.initial_prompt = initial_prompt
        self.destination = destination
        self.origin = origin
        self.start_date = start_date
        self.end_date = end_date
        self.budget = budget

