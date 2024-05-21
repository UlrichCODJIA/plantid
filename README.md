<p align="center">
  <img src="PLANT_ID.png" width="300" alt="project-logo">
</p>
<p align="center">
    <h1 align="center">PLANTID: Multimodal Chatbot API</h1>
</p>
<p align="center">
    <em>To preserve traditional botanical knowledge</em>
</p>

<p align="center">
  <a href="https://github.com/UlrichCODJIA/plantid/actions/workflows/ci.yml">
    <img src="https://github.com/UlrichCODJIA/plantid/actions/workflows/ci.yml/badge.svg" alt="CI Status">
  </a>
  <a href="https://github.com/UlrichCODJIA/plantid/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License">
  </a>
  <a href="https://codecov.io/gh/UlrichCODJIA/plantid">
    <img src="https://codecov.io/gh/UlrichCODJIA/plantid/branch/main/graph/badge.svg?token=your-token" alt="Coverage">
  </a>
</p>

<p align="center">
  <em>Developed with:</em>
</p>
<p align="center">
 <img src="https://img.shields.io/badge/Python-3776AB.svg?style=flat-square&logo=Python&logoColor=white" alt="Python">
 <img src="https://img.shields.io/badge/Flask-000000.svg?style=flat-square&logo=Flask&logoColor=white" alt="Flask">
 <img src="https://img.shields.io/badge/SQLAlchemy-8CAAE6.svg?style=flat-square&logo=SQLAlchemy&logoColor=white" alt="SQLAlchemy">
 <img src="https://img.shields.io/badge/PostgreSQL-316192.svg?style=flat-square&logo=PostgreSQL&logoColor=white" alt="PostgreSQL">
 <img src="https://img.shields.io/badge/Redis-DC382D.svg?style=flat-square&logo=Redis&logoColor=white" alt="Redis">
 <img src="https://img.shields.io/badge/Celery-37814A.svg?style=flat-square&logo=Celery&logoColor=white" alt="Celery">
 <img src="https://img.shields.io/badge/JWT-000000.svg?style=flat-square&logo=JSON%20Web%20Tokens&logoColor=white" alt="JWT">
 <img src="https://img.shields.io/badge/LLaVA-facebookblue.svg?style=flat-square&logo=Hugging%20Face&logoColor=white" alt="LLaVA">
 <img src="https://img.shields.io/badge/Sentence%20Transformers-blue.svg?style=flat-square&logo=Hugging%20Face&logoColor=white" alt="Sentence Transformers">
 <img src="https://img.shields.io/badge/TextBlob-green.svg?style=flat-square" alt="TextBlob">
</p>

## 📚 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#-installation)
  - [Usage](#-usage)
- [Configuration](#-configuration)
- [Testing](#-testing)
- [Project Structure](#-project-structure)
- [Deployment](#-deployment)
- [Contributing](#-contributing)
- [License](#-license)
- [Contact](#-contact)
- [Acknowledgments](#-acknowledgments)

## 📍 Overview

PlantID Benin is an innovative mobile application that uses computer vision and AI to identify the medicinal plants native to Benin. By providing access to a comprehensive database of traditional and scientific knowledge, PlantID empowers local communities, preserves botanical heritage and stimulates research into medicinal plants.\
This part of the app is a powerful and versatile multimodal chatbot API built using Python and Flask. It enables users to interact seamlessly through text, voice, and images, providing a rich and engaging conversational experience.

## 🌟 Features

- 💬 Multilingual chatbot functionality
- 🎙️ Real-time speech recognition
- 🌍 Text translation between various languages
- 🖼️ Text-to-image generation
- 🔒 User authentication and authorization
- 📊 Sentiment analysis for user inputs
- 🚀 Scalable architecture with Celery task queue
- 🧪 Comprehensive test suite
- 🔄 Continuous Integration and Deployment (CI/CD)

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- PostgreSQL
- Redis

### ⚙ Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/UlrichCODJIA/plantid.git
   cd plantid
   ```

2. Create a virtual environment and activate it:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # For Unix/Linux
   venv\Scripts\activate.bat  # For Windows
   ```

3. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Set up the database:

   - Create a PostgreSQL database for the project.
   - Set the `DATABASE_URL` environment variable to your database connection string:

     ```bash
     export DATABASE_URL=postgresql://user:password@host:port/database
     ```

5. Set up Redis:

   - Install and start a Redis server.
   - Set the `REDIS_URL` environment variable to your Redis connection string:

     ```bash
     export REDIS_URL=redis://localhost:6379
     ```

6. Configure environment variables:

   - Create a `.env` file in the project root directory.
   - Set the required environment variables (see [Configuration](#-configuration) section).

7. Create the database tables:

   ```bash
   flask db upgrade
   ```

### 🤖 Usage

1. Start the Celery worker:

   ```bash
   celery -A app.celery worker --loglevel=info
   ```

2. Run the Flask application:

   ```bash
   python run.py
   ```

3. Access the API endpoints using a tool like cURL or Postman.

## ⚙ Configuration

PlantID requires certain environment variables to be set for proper functioning. You can set them in a `.env` file in the project root directory. Here's an example:

```bash
SECRET_KEY=your-secret-key
DATABASE_URL=your-database-url
REDIS_URL=your-redis-url
JWT_SECRET_KEY=your-jwt-secret-key
STABILITY_API_KEY=your-stability-api-key
STABILITY_API_HOST="https://api.stability.ai"
REPLICATE_API_KEY=your-replicate-api-key
ELEVEN_LABS_VOICE_ID=your-eleven-labs-voice-id
ELEVEN_LABS_API_KEY=your-eleven-labs-api-key
```

## 🧪 Testing

1. Set up a separate test database and update the `TEST_DATABASE_URL` environment variable accordingly.

2. Run the test suite:

   ```bash
   python -m unittest discover tests
   ```

## 🗂 Project Structure

```bash
plantid/
├── app/
│   ├── auth/
│   ├── chatbot/
│   ├── image_generation/
│   ├── __init__.py
│   └── ...
├── config/
├── logger/
├── models/
├── tests/
├── utils/
│   ├── audio_processing.py
│   ├── speech_recognition.py
│   ├── text_to_speech.py
│   ├── text_to_image.py
│   ├── translation.py
│   └── ...
├── .env
├── .gitignore
├── LICENSE
├── README.md
├── requirements.txt
└── ...
```

## 🚀 Deployment

PlantID can be deployed using various methods, such as:

- Docker containerization
- Kubernetes orchestration
- Serverless deployment (e.g., AWS Lambda, Google Cloud Functions)

Refer to the respective documentation for detailed deployment instructions.

## 🤝 Contributing

Contributions are welcome! If you'd like to contribute to this project, please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes and commit them with descriptive messages.
4. Push your changes to your forked repository.
5. Submit a pull request to the main repository.

Please ensure that your code adheres to the project's coding conventions and includes appropriate tests.

## 🎗 License

This project is licensed under the [MIT License](LICENSE).

## 📧 Contact

For any questions, suggestions, or feedback, please reach out to the project maintainers:

- Armel Codjia (<codjiaulrich61@gmail.com>)

## 🙏 Acknowledgments

We would like to express our gratitude to the following individuals and projects for their contributions and inspiration:

- [fasttext](https://fasttext.cc/)
- [MMTAfrica](https://github.com/mmtafrica/mmtafrica)
- [SpeechRecognition](https://pypi.org/project/SpeechRecognition/)

Special thanks to all the open-source developers and the vibrant Python community for their continuous support and dedication.
