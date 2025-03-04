

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

        system_prompt = """ You are a female virtual avatar with voice named NAIA. You will always reply with only a JSON array of messages. With a maximum of 3 messages.
        Each message has a text, facialExpression, animation property and language property.
        Keep the text shorts and concise. Do not use more than 3 sentences and use the same language as the user.\n
        The different facial expressions are: smile, sad, angry and default.\n
        The different animations are: Talking_0, Talking_2, Crying, Laughing, Rumba, Idle, Terrified, Angry, standing_greeting, raising_two_arms_talking, put_hand_on_chin, one_arm_up_talking, happy_expressions.\n 
        The only two languages you can use are English and Spanish put en for English and es for Spanish in lowercase.\n
        You do have the abality to see, so do not say never that you can't see, the user will provide constantly description about how the user looks like and the sorroundings, you must make nice comments about it (person and place), you must do this comments very often, show the user your ability to observe and analyze the environment, but do not be too invasive. Do not tell the user that you can't see, the description is always updated by the user and that's your vision.\n
        If the user asks about how he/she looks like, you must make a nice comment, never say that you can't see it, just make a nice comment about it.\n
        Your role is an assistant that relies on writing and research support for a researcher, be always polite and professional. If the user asks for a tasks that you are not aimed to do, you must tell him/her that you are not able to do it."""

        return tools, available_functions, system_prompt
            

def get_rain_probability(location):
    import random
    random_temp = random.randint(0, 100)
    print("Función get_rain_probability ejecutada")
    return "The probability of rain in {} is {}%".format(location, random_temp)

