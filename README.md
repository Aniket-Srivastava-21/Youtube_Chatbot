# YouTube Chatbot Streamlit Application

This project is a Streamlit application that serves as a chatbot for YouTube video content. It allows users to interact with video transcripts, asking questions and receiving answers based on the content of the videos.

## Project Structure

```
youtube-chatbot-streamlit
├── src
│   ├── streamlit_app.py       # Main entry point for the Streamlit application
│   ├── extractor.py            # Functions for downloading and extracting transcripts from YouTube
│   ├── cleaner.py              # Functions to clean transcript data
│   ├── splitter.py             # Functions to split cleaned transcripts into smaller chunks
│   ├── embeddings.py           # Functions for generating and storing embeddings
│   ├── vectorstore.py          # Manages storage and retrieval of embeddings
│   ├── chain.py                # Logic for querying the vector store and generating responses
│   └── config.py               # Configuration settings and environment variable loading
├── notebooks
│   └── Chatbot_prototype.ipynb # Original Jupyter notebook with prototype code
├── requirements.txt            # Lists project dependencies
├── .env.example                # Template for environment variables
├── .gitignore                  # Specifies files to ignore by Git
└── README.md                   # Documentation for the project
```

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd youtube-chatbot-streamlit
   ```

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your environment variables:
   - Copy `.env.example` to `.env` and fill in the necessary API keys.

## Usage

To run the Streamlit application, execute the following command in your terminal:
```bash
streamlit run src/streamlit_app.py
```

After successful run, you should get a webpage like this:

<img width="1914" height="542" alt="Screenshot 2025-11-02 224413" src="https://github.com/user-attachments/assets/575cf677-2b18-4c42-af67-2fd0929f339e" />

After the transcript for the yt video is successfully indexed, you should be able to answer any question to the chatbot related to it:

<img width="1919" height="724" alt="Screenshot 2025-11-02 224353" src="https://github.com/user-attachments/assets/8d7ed29a-2a4d-4524-a1fb-dfdb32c47414" />

