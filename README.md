# RAG-Based Video Transcript Query App

This repository contains a Streamlit application that allows users to ask questions and receive summarized answers based on video transcripts. The application identifies the most relevant segments from a playlist and a course, summarizes the key information, and provides direct links to the related video segments.

**Link to streamlit app:** https://video-rag-dl.streamlit.app/
## Features

* **Natural Language Querying**: Users can input a question in natural language.
* **Relevant Transcript Matching**: The app identifies the three most relevant one-minute transcript segments.
* **Summarized Answers**: Generates a concise summary based on the matched transcripts.
* **Video Segment Linking**: Provides links to the exact timestamps in the videos for further exploration.

## Data Sources

* **Playlist**: [YouTube Playlist](https://www.youtube.com/playlist?list=PLtBw6njQRU-rwp5__7C0oIVt26ZgjG9NI)
* **Course Video**: [Course on YouTube](https://www.youtube.com/watch?v=V_xro1bcAuA)

## Usage

1. Open the app in your browser using the URL provided by Streamlit
2. Enter a question in the input field.
3. View the summarized response and links to the relevant video segments.

## Key Components

### Transcript Preprocessing

Transcripts from the videos are preprocessed into a searchable format, with time stamps retained for direct linking.

### Retrieval-Augmented Generation (RAG)

1. **Retrieval**: Uses a similarity-based search to find the most relevant transcript segments.
2. **Generation**: Summarizes the content of the retrieved transcripts.

### Video Linking

The app constructs direct YouTube links to the exact timestamps of the most relevant transcript segments.

## Future Improvements

* Add support for more data sources.
* Enhance summarization accuracy with advanced NLP models.
* Implement multilingual support.

## Contributing

Contributions are welcome! Please fork the repository and create a pull request for any proposed changes.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Contact

For questions or support, feel free to open an issue or contact the repository owner.
