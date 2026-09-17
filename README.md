# Music Playlist Transfer

This project allows you to transfer your playlists between Spotify and YouTube Music.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

*   Node.js and npm
*   Python 3 (`python3` or `py`) and pip

### Installation

1.  **Clone the repository**

    ```bash
    git clone <repository-url>
    cd <repository-name>
    ```

2.  **Frontend Setup**

    Navigate to the root directory and install the necessary npm packages:

    ```bash
    npm install
    ```

3.  **Backend Setup**

    Install the required Python packages using the `requirements.txt` file:

    ```bash
    pip install -r backend/requirements.txt
    ```
    *(Note: Depending on your platform, use `python3 -m pip` or `py -m pip`.)*

4.  **Environment Variables**

    Create a file named `.env` in the `backend` directory (or set environment variables in your environment). Add the following variables:

    ```
    SP_CLIENT_ID=your_spotify_client_id
    SP_CLIENT_SECRET=your_spotify_client_secret
    YT_CLIENT_ID=your_youtube_client_id
    YT_CLIENT_SECRET=your_youtube_client_secret
    APP_SECRET=your_flask_app_secret_key
    ```

## Running the application

To run the application, start both the backend and frontend servers.

1.  **Start the backend server**

    In a terminal, run the following command to start the Flask server:

    ```bash
    python3 backend/server.py
    ```
    *(On Windows systems where `python3` is not in PATH, use `py backend/server.py` or `python backend/server.py`.)*

    The backend will run on `http://localhost:8000`.

2.  **Start the frontend server**

    In a separate terminal, run:

    ```bash
    npm start
    ```
    *(For development mode with auto-reload, run `npm run dev`.)*

    The frontend will run on `http://localhost:3000`.

## Running Tests

To run the automated tests for the backend:

```bash
npm test
```
or
```bash
python3 -m unittest discover -s backend/tests
```
