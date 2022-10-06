#!/usr/bin/env python
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Configuration for the bot."""

import os


class DefaultConfig:
    """Configuration for the bot."""

    PORT = 3978
    #note that the user managed identity has no password (blank) but the environment variable cannot be blank, so we use a single space that needs to be removed
    #we also want to test the bot before registering it on azure. in this case the MicrosoftAppId must remain blank too in the environment variables 
    APP_ID = os.environ.get("MicrosoftAppId", "").strip()  
    # APP_ID = ""
    APP_PASSWORD = os.environ.get("MicrosoftAppPassword", "").strip()
    # APP_PASSWORD = ""
    LUIS_APP_ID = os.environ.get("LuisAppId", "")
    LUIS_API_KEY = os.environ.get("LuisAPIKey", "")
    # LUIS endpoint host name, ie "westus.api.cognitive.microsoft.com"
    LUIS_API_HOST_NAME = os.environ.get("LuisAPIHostName", "")
    APPINSIGHTS_INSTRUMENTATION_KEY = os.environ.get(
        "AppInsightsInstrumentationKey", ""
    )
