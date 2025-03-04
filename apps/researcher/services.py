

class ResearcherService:
    def retrieve_tools(self):
        tools = [
                    {
                        "type": "function",
                        "function": {
                            "name": "get_rain_probability",
                            "description": "Get the probability of rain for a specific location",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "location": {
                                        "type": "string",
                                        "description": "The city and state, e.g., San Francisco, CA"
                                    }
                                },
                                "required": [
                                    "location"
                                ]
                            }
                        }
                    }
                ]
        
        available_functions = {
            "get_rain_probability": get_rain_probability
        }

        system_prompt = "You are a helpful assistant. You can provide information about the weather, news, or any other topic. Be chatty and friendly. Your name is NAIA. About the images on each input you just need to say nice comments about the user clothes or the background."


        return tools, available_functions, system_prompt
            

def get_rain_probability(location):
    import random
    random_temp = random.randint(0, 100)
    print("Función get_rain_probability ejecutada")
    return "The probability of rain in {} is {}%".format(location, random_temp)

