IMAGE_GENERATION_PHRASES = [
    "Can you create an image of",
    "I'd like to see a picture of",
    "Generate an image showing",
    "Please make an image that depicts",
    "Could you draw",
    "Can you paint",
    "I want to see a picture of",
    "Create a visual representation of",
    "Show me an image of",
    "Make me a picture of",
    "Imagine an image of",
    "Visualize and create an image of",
]
IMAGE_GENERATION_SIMILARITY_THRESHOLD = 0.7
CONFIRMATION_PHRASES = [
    "Is there anything else I can help you with?",
    "Do you have any other questions?",
    "Anything else I can assist you with today?",
]
CONFIRMATION_SIMILARITY_THRESHOLD = 0.8
SHORT_RESPONSE_THRESHOLD = 3
SHORT_RESPONSE_LENGTH = 50
DIALOGUE_STATES = {
    "greeting": "greeting",
    "conversing": "conversing",
    "confirming": "confirming",
    "generating_image": "generating_image",
    "end": "end",
}
