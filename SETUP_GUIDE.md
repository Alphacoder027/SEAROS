# SAEROS - Complete Setup Guide

## Prerequisites

Before starting, ensure you have:
- **Python 3.10+** installed
- **MySQL 8.0+** installed and running
- **pip** package manager

## Step-by-Step Installation

### 1. Install MySQL (if not already installed)

Download and install MySQL 8.0 from: https://dev.mysql.com/downloads/mysql/

During installation, remember the **root password** you set.

### 2. Create the Database

Open MySQL command line or MySQL Workbench and run:

```sql
CREATE DATABASE saeros_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. Configure Database Credentials

Edit the `.env` file in the project root and update the MySQL password:

```env
DB_PASSWORD=your_actual_mysql_password
```

Replace `your_actual_mysql_password` with the password you set during MySQL installation.

### 4. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 5. Train the ML Model

```bash
python train_model.py
```

This will:
- Load training data from `data/training_data.csv`
- Train a Random Forest model
- Save the model to `models/yield_model.pkl`
- Display model performance metrics (R² ≈ 0.997)

### 6. Initialize the Database

```bash
python init_db.py
```

This will:
- Create all database tables
- Seed roles (admin, agent, scrap_team)
- Create default users

### 7. Run the Application

```bash
python run.py
```

The application will start on: **http://localhost:5000**

## Default Login Credentials

### Admin Account
- **Username**: `admin`
- **Password**: `admin123`
- **Access**: Full system access, user management, reports

### Agent Account (for testing)
- **Username**: `agent1`
- **Password**: `agent123`
- **Access**: Submit raw materials, view batches

### Scrap Team Account (for testing)
- **Username**: `scrap1`
- **Password**: `scrap123`
- **Access**: Process by-products, log treatments

## Troubleshooting

### MySQL Connection Error

**Error**: `Access denied for user 'root'@'localhost'`

**Solution**: 
1. Verify MySQL is running
2. Check your MySQL root password
3. Update `DB_PASSWORD` in `.env` file
4. If you forgot your password, reset it:
   ```bash
   # Stop MySQL service
   # Start MySQL with --skip-grant-tables
   # Reset password using MySQL command line
   ```

### Database Already Exists

If you need to reset the database:

```sql
DROP DATABASE saeros_db;
CREATE DATABASE saeros_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Then run `python init_db.py` again.

### Port 5000 Already in Use

Edit `run.py` and change the port:

```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Change to 5001 or any available port
```

### ML Model Not Found

If you see "Model not found" errors:
1. Ensure `train_model.py` completed successfully
2. Check that `models/yield_model.pkl` exists
3. Re-run `python train_model.py`

## Project Structure

```
saeros/
├── app/                    # Flask application
│   ├── routes/            # Route handlers (admin, agent, scrap_team, api, auth)
│   ├── templates/         # HTML templates
│   ├── static/            # CSS, JS, images
│   ├── utils/             # Utilities (ML model, decorators, algorithms)
│   ├── __init__.py        # App factory
│   └── models.py          # Database models
├── data/                  # Training data
│   └── training_data.csv
├── models/                # Trained ML models
│   └── yield_model.pkl
├── config.py              # Configuration
├── requirements.txt       # Python dependencies
├── schema.sql            # Database schema (reference)
├── init_db.py            # Database initialization script
├── train_model.py        # ML model training script
├── run.py                # Application entry point
└── README.md             # Project documentation
```

## Features Overview

### Admin Dashboard
- User management (approve/suspend/activate)
- System-wide analytics and charts
- Batch monitoring
- By-product assignment
- PDF report generation
- Audit logs

### Agent Dashboard
- Submit raw material batches
- ML-powered yield prediction
- Track processing status
- View submission history
- Monitor Bayer process steps

### Scrap Team Dashboard
- View assigned by-products
- AI-powered treatment recommendations
- Log treatment results
- Track secondary outputs
- Process queue management

## API Endpoints

### Yield Prediction API

```bash
POST /api/predict
Content-Type: application/json

{
  "silica_percent": 5.2,
  "iron_oxide_percent": 12.3,
  "alumina_percent": 48.5,
  "moisture_content": 8.1
}
```

Response:
```json
{
  "predicted_yield": 72.4,
  "confidence_score": 95.2,
  "efficiency_rating": "Excellent",
  "model_used": "random_forest"
}
```

### By-Product Recommendation API

```bash
POST /api/recommend-byproduct
Content-Type: application/json

{
  "byproduct_type": "red_mud",
  "iron_oxide_percent": 35.0,
  "alumina_percent": 15.0,
  "silica_percent": 12.0
}
```

## Development

### Running in Development Mode

```bash
export FLASK_ENV=development  # Linux/Mac
set FLASK_ENV=development     # Windows CMD
$env:FLASK_ENV="development"  # Windows PowerShell

python run.py
```

### Database Migrations

If you modify models:

```bash
flask db init                 # First time only
flask db migrate -m "message" # Create migration
flask db upgrade              # Apply migration
```

## Production Deployment

1. Set `FLASK_ENV=production` in `.env`
2. Change `SECRET_KEY` to a strong random value
3. Use a production WSGI server (gunicorn, uWSGI)
4. Set up HTTPS/SSL
5. Configure firewall rules
6. Use a reverse proxy (nginx, Apache)

Example with gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

## Support

For issues or questions:
1. Check this guide first
2. Review the README.md
3. Check database connection settings
4. Verify all dependencies are installed
5. Ensure MySQL service is running

## License

MIT License - See LICENSE file for details
