# Industrial Item Management System

A web-based inventory management system for tracking industrial items, their locations, and associated documents.

## Features
- Multi-language support (English, German, French)
- Dark/Light theme
- Item management with categories, materials, and colors
- Location tracking
- Document management
- User authentication
- Responsive design

## Prerequisites
- Docker and Docker Compose (for Docker deployment)
- OR Python 3.9+ and pip (for manual deployment)

## Quick Start with Docker

1. Clone the repository:
```bash
git clone <your-repository-url>
cd IndustrialItem
```

2. Create a `.env` file with your secret key:
```bash
echo "SECRET_KEY=your-secret-key-here" > .env
```

3. Build and start the application:
```bash
docker-compose up -d
```

4. Access the application at http://localhost:5001

## Manual Deployment

1. Clone the repository:
```bash
git clone <your-repository-url>
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

### Direct Internet Access (Not Recommended)
If you must make the application directly accessible from the internet:
1. Set up HTTPS using a reverse proxy (e.g., Nginx)
2. Configure proper firewall rules
3. Use strong authentication
4. Keep the application updated

## Troubleshooting
1. If the application doesn't start, check the logs:
```bash
docker-compose logs -f
```

2. If database issues occur:
```bash
docker-compose down
rm -rf instance/inventory.db
docker-compose up -d
```

3. For permission issues:
```bash
chmod -R 755 uploads/
```

## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License
[Your chosen license] 