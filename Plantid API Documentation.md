# Plantid API Documentation

## Overview
The Plantid API provides access to plant identification, medicinal plant information, traditional knowledge, and research tools. This documentation covers the available endpoints, request/response formats, and authentication requirements.

## Authentication
All API endpoints require JWT authentication. Include the JWT token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

To obtain a token, use the authentication endpoints described below.

## Rate Limiting
Most endpoints are rate-limited to prevent abuse. Current limits:
- Plant recognition: 10 requests per minute
- Chatbot: 30 requests per minute
- Other endpoints: 60 requests per minute

## Endpoints

### Authentication

#### POST /auth/login
Authenticate user and receive JWT token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "username": "botanist1",
    "preferred_language": "en",
    "expertise_level": "expert"
  }
}
```

### Plant Recognition

#### POST /api/recognize
Identify a plant from an uploaded image.

**Request:**
- Content-Type: multipart/form-data
- Body: image file (supported formats: PNG, JPEG)

**Response:**
```json
{
  "recognized_plants": [
    {
      "confidence": 0.95,
      "plant": {
        "id": 1,
        "scientific_name": "Artemisia annua",
        "common_names": {
          "en": ["Sweet wormwood", "Annual wormwood"],
          "fr": ["Armoise annuelle"]
        },
        "medicinal_uses": {
          "en": ["Traditional antimalarial", "Fever reduction"],
          "fr": ["Antipaludique traditionnel", "Réduction de la fièvre"]
        }
      }
    }
  ]
}
```

### Chatbot

#### POST /api/chat
Interact with the AI chatbot about medicinal plants.

**Request Body:**
```json
{
  "message": "What are the medicinal uses of chamomile?"
}
```

**Response:**
```json
{
  "response": "Chamomile (Matricaria chamomilla) has several traditional medicinal uses...",
  "detected_language": "en"
}
```

### Research Tools

#### GET /research/publications/search
Search scientific publications about medicinal plants.

**Query Parameters:**
- query (optional): Search term
- plant_id (optional): Filter by specific plant
- compound (optional): Filter by chemical compound

**Response:**
```json
{
  "publications": [
    {
      "id": 1,
      "title": "Antimalarial activity of Artemisia annua",
      "authors": ["Smith, J.", "Johnson, M."],
      "abstract": "This study explores...",
      "doi": "10.1234/journal.article.2024"
    }
  ]
}
```

#### POST /research/chemical-similarity
Find chemically similar compounds.

**Request Body:**
```json
{
  "compound": "artemisinin"
}
```

**Response:**
```json
{
  "similar_compounds": [
    {
      "name": "artemether",
      "similarity_score": 0.85,
      "structure": "CC1CCC2C(C)(C)C(=O)OC3OC4(C)CCC1C32OO4"
    }
  ]
}
```

#### POST /research/field-data
Submit field research data.

**Request Body:**
```json
{
  "plant_id": 1,
  "location": {
    "latitude": 6.5244,
    "longitude": 3.3792,
    "name": "Lagos Herbarium"
  },
  "environmental_conditions": {
    "soil_type": "loamy",
    "altitude": 39,
    "weather": "sunny"
  },
  "samples_collected": ["leaves", "roots"],
  "observations": "Plant found in clusters near water source"
}
```

**Response:**
```json
{
  "message": "Field data submitted successfully",
  "field_data_id": 123
}
```

### Traditional Knowledge

#### POST /knowledge/traditional-knowledge
Submit traditional medicinal knowledge.

**Request Body:**
```json
{
  "plant_id": 1,
  "knowledge": {
    "en": "This plant is traditionally used to treat fever",
    "fr": "Cette plante est traditionnellement utilisée pour traiter la fièvre"
  },
  "region": "West Africa",
  "consent_info": {
    "provider_name": "Dr. Aisha Mohammed",
    "community": "Yoruba healers association",
    "consent_type": "written",
    "consent_date": "2024-03-15"
  }
}
```

**Response:**
```json
{
  "message": "Traditional knowledge submitted successfully",
  "knowledge_id": 456
}
```

### Educational Features

#### GET /learn/quizzes
Get available quizzes based on user's expertise level.

**Query Parameters:**
- difficulty (optional): beginner, intermediate, or expert

**Response:**
```json
{
  "quizzes": [
    {
      "id": 1,
      "title": {
        "en": "Medicinal Plants of West Africa",
        "fr": "Plantes Médicinales d'Afrique de l'Ouest"
      },
      "difficulty": "intermediate",
      "question_count": 10
    }
  ]
}
```

## Error Handling
The API uses standard HTTP status codes and returns error messages in a consistent format:

```json
{
  "error": "Detailed error message"
}
```

Common status codes:
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 429: Too Many Requests
- 500: Internal Server Error

## Multilingual Support
The API supports multiple languages for both input and output. Specify the preferred language in the user profile or per request using the `Accept-Language` header.

## Best Practices
1. Always handle rate limiting gracefully
2. Cache responses when appropriate
3. Use appropriate content types for requests
4. Handle errors gracefully and provide user-friendly messages

## Support
For API support, contact: api-support@plantid.example.com