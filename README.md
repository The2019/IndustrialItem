# Industrial Item Inventory Management

A Flask-based inventory management system for industrial items.

## Running with Docker

### Prerequisites
- Docker and Docker Compose installed on your system

### Steps to Run

1. Clone the repository:
```bash
git clone https://github.com/The2019/IndustrialItem
cd IndustrialItem
```

2. Build and start the Docker containers:
```bash
docker-compose up -d
```

3. Access the application:
Open your browser and navigate to http://localhost:5000

### Import/Export Data

- To export data: Go to Settings > Export Data
- To import data: Go to Settings > Import Data (upload a ZIP file containing CSV files)

### Stopping the Application

```bash
docker-compose down
```

## Development

For development, you can use volume mounts to see changes in real-time:

```bash
docker-compose up
```

This will mount your local directory to the container, allowing you to make changes to the code and see them reflected immediately.

## Troubleshooting

- If you encounter database issues, you can reset it by removing the instance folder:
```bash
docker-compose down
rm -rf instance
docker-compose up -d
```

- Check logs with:
```bash
docker-compose logs -f
```

## Features
- Multi-language support (English, German)
- Diffrent Colorthemes
- Item management with categories, materials, and colors
- Location tracking
- Document management
- Responsive design

## Prerequisites
- Docker and Docker Compose (for Docker deployment)
- OR Python 3.9+ and pip (for manual deployment)

## Manual Deployment

1. Clone the repository:
```bash
git clone https://github.com/The2019/IndustrialItem
cd IndustrialItem
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
export FLASK_APP=app.py
export FLASK_ENV=production
export SECRET_KEY=your-secret-key-here
```

5. Initialize the database:
```bash
flask db init
flask db migrate
flask db upgrade
```

6. Run the application:
```bash
gunicorn --bind 0.0.0.0:5000 app:app
```

## Configuration

### Environment Variables
- `SECRET_KEY`: Secret key for Flask session encryption
- `FLASK_APP`: Set to app.py
- `FLASK_ENV`: Set to production for production deployment

### Port Configuration
- Default port: 5001 (Docker) or 5000 (manual)
- Can be changed in docker-compose.yml or gunicorn command

## Data Persistence
- Database: Stored in `instance/inventory.db`
- Uploads: Stored in `uploads/` directory
- Both are persisted using Docker volumes when using Docker deployment

## Static Files
The application includes static files (icons and images) that are required for the interface:
- Icons: Located in `static/icons/`
- Images: Located in `static/images/`
- Logo: Located in `static/IndustrialItem.png`

These files are essential for the application's interface and should be included when cloning the repository.

## Security Notes
1. Always change the default secret key in production
2. HTTPS is recommended only when:
   - Making the application directly accessible from the internet
   - Not using a VPN for remote access
3. Set up proper firewall rules
4. Keep the application and dependencies updated

## Access Methods

### Local Network Access
- Access via `http://localhost:5001` or `http://YOUR_LOCAL_IP:5001`
- No HTTPS needed as traffic stays within your network
- Example: `http://192.168.1.100:5001`

### Remote Access via VPN
1. Set up a VPN server on your network
2. Connect to your VPN from remote devices
3. Access the application via local network address
4. No HTTPS needed as VPN provides encryption