# Stroke Prediction System

This project is a **Stroke Prediction System** designed to manage patient data, predict stroke risks, and provide a user-friendly interface for healthcare professionals. The system includes features such as patient management, risk analysis, and dashboard statistics.

## Features

- **User Authentication**: Secure login and registration for users.
- **Patient Management**: Add, edit, view, and delete patient records.
- **Dashboard**: View key statistics such as total patients, high-risk patients, and predictions made today.
- **Risk Analysis**: Predict stroke risk levels based on patient data.
- **Search and Pagination**: Easily search and navigate through patient records.
- **Responsive Design**: User-friendly interface optimized for various devices.

## Installation

Follow these steps to set up the project locally:

### Prerequisites

- Python 3.8 or higher
- Flask
- Node.js (if the backend API requires it)
- A virtual environment (recommended)

### Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/CS-LTU/com7033-assignment-RichardEjikeleedstrinity.git
   cd stroke-prediction-system
   ```

2. **Set Up a Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Environment Variables**
   Create a `.env` file in the root directory and configure the following:
   ```
   FLASK_APP=run.py
   FLASK_ENV=development
   SECRET_KEY=your_secret_key
   API_BASE_URL=http://localhost:3000/api
   ```

5. **Run the Application**
   ```bash
   flask run
   ```

6. **Access the Application**
   Open your browser and navigate to `http://127.0.0.1:5000`.

## File Structure

```
assignment/
├── backend/
│   ├── api/
│   │   ├── auth/               # Authentication-related API endpoints
│   │   ├── dashboard/          # Dashboard-related API endpoints
│   │   ├── database/           # Database connection and utilities
│   │   ├── help_utils/         # Helper utilities for the backend
│   │   ├── models/             # Database models
│   │   ├── patients/           # Patient-related API endpoints
│   ├── app.py                  # Backend application entry point
│   ├── config.py               # Backend configuration file
│   ├── users.db                # SQLite database file
│   ├── .env                    # Environment variables for the backend
│   ├── requirements.txt        # Backend dependencies
├── frontend/
│   ├── app/
│   │   ├── routes/             # Flask route handlers
│   │   ├── models/             # Frontend models
│   │   ├── services/           # API client and utility services
│   │   ├── templates/          # HTML templates for the frontend
│   │   ├── utils/              # Helper functions and validators
│   ├── run.py                  # Frontend application entry point
│   ├── requirements.txt        # Frontend dependencies
├── ml_model/
│   ├── healthcare-dataset-stroke-data.csv  # Dataset for stroke prediction
│   ├── stroke_prediction_model_improved.joblib  # Trained ML model
│   ├── update_data.py          # Script to update the dataset
│   ├── prediction.py           # Script for making predictions
├── tests/
│   ├── backend/                # Tests for the backend
│   ├── __init__.py             # Test package initialization
│   ├── test_auth.py            # Tests for authentication
│   ├── test_routes.py          # Tests for routes
```

## Key Functionalities

### 1. **Authentication**
- Users can register and log in securely.
- CSRF protection is implemented for all forms.

### 2. **Patient Management**
- Add new patients with detailed demographic and medical information.
- Edit existing patient records.
- View detailed patient profiles.
- Delete patient records.

### 3. **Dashboard**
- View statistics such as total patients, high-risk patients, and today's predictions.
- Recent patient activity is displayed for quick access.

### 4. **Risk Analysis**
- Predict stroke risk levels based on patient data.
- Risk levels are categorized as `High`, `Medium`, or `Low`.

## API Integration

The system communicates with a backend API for data management. The API endpoints include:

- `/auth/login` - User authentication
- `/patients` - Fetch, create, update, and delete patient records
- `/dashboard/stats` - Fetch dashboard statistics

## Testing

To run tests, use the following command:
```bash
pytest
```

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Commit your changes and push the branch.
4. Open a pull request.


