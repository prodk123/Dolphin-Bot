# Chess Game

A web-based chess game with AI opponent built using Python Flask and JavaScript.

## Features

- Play chess against an AI opponent
- Drag and drop pieces
- Move highlighting
- Captured pieces display
- Score tracking
- Check and checkmate detection
- Move history tracking

## Technologies Used

- Backend: Python Flask
- Frontend: HTML, CSS, JavaScript
- Chess Logic: Custom Python implementation

## Local Development

1. Install Python 3.8 or higher
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python app.py
   ```
4. Open http://localhost:5000 in your browser

## Deployment

This application can be deployed to Render.com:

1. Create a new account on Render.com
2. Create a new Web Service
3. Connect your GitHub repository
4. Set the following:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
5. Deploy! 