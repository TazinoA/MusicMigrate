# Music Playlist Transfer

This project allows you to transfer your playlists from one music streaming service to another.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

*   Node.js and npm
*   Python 3 and pip

### Installation

1.  **Clone the repository**

    You can clone this repository to your local machine using the following command:
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

4.  **Environment Variables**

    Create a file named `.env` in the `backend` directory. This file will store your API credentials and secret keys. Add the following variables to the `.env` file, replacing the placeholder text with your actual credentials:

    ```
    SP_CLIENT_ID=your_spotify_client_id
    SP_CLIENT_SECRET=your_spotify_client_secret
    YT_CLIENT_ID=your_youtube_client_id
    YT_CLIENT_SECRET=your_youtube_client_secret
    APP_SECRET=your_flask_app_secret_key
    ```

## Running the application

To run the application, you will need to start both the backend and frontend servers.

1.  **Start the backend server**

    In a terminal, run the following command to start the Python Flask server:

    ```bash
    python backend/server.py
    ```

    The backend will be running on `http://localhost:8000`.

2.  **Start the frontend server**

    In a separate terminal, run the following command to start the Node.js Express server:

    ```bash
    npm start
    ```

    The frontend will be running on `http://localhost:3000`.

You can now access the application by navigating to `http://localhost:3000` in your web browser.
