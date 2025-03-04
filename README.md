# Industrial Item Management System

A Flask-based web application for managing industrial items, documents, and projects.

## Getting Started

### Option 1: Clone from GitHub (Recommended)
1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/IndustrialItem.git
cd IndustrialItem
```

### Option 2: Download and Extract
1. Download the project zip file
2. Extract it to your desired location
3. Open a terminal in the project directory

## Docker Setup

### Prerequisites

- Docker
- Docker Compose

### Running the Application

1. Build and start the containers:
```bash
docker-compose up --build
```

2. The application will be available at `http://localhost:5000`

### Stopping the Application

To stop the application:
```bash
docker-compose down
```

### Data Persistence

The application uses two volumes for data persistence:
- `./uploads`: For storing uploaded documents
- `./instance`: For storing the SQLite database

### Development

For development, you can run the application without Docker:
```bash
python app.py
```

## Sharing the Application

### Local Network Access

1. Find your computer's IP address:
   - On Mac/Linux: Open terminal and type `ifconfig` or `ip addr`
   - On Windows: Open command prompt and type `ipconfig`

2. Share the URL with others on the same network:
   ```
   http://YOUR_IP_ADDRESS:5000
   ```
   Example: `http://192.168.1.100:5000`

### Internet Access (Advanced)

To make the application accessible from anywhere on the internet:

1. Configure your router to forward port 5000 to your computer
2. Find your public IP address at `whatismyip.com`
3. Share the URL:
   ```
   http://YOUR_PUBLIC_IP:5000
   ```

⚠️ **Security Note**: Making the application accessible on the internet exposes it to potential security risks. Consider:
- Adding user authentication
- Using HTTPS
- Setting up a firewall
- Using a reverse proxy like Nginx

## Project Structure

```
IndustrialItem/
├── app.py              # Main application file
├── translations.py     # Language translations
├── requirements.txt    # Python dependencies
├── Dockerfile         # Docker configuration
├── docker-compose.yml # Docker Compose configuration
├── .dockerignore      # Docker ignore rules
├── templates/         # HTML templates
├── static/           # Static files (CSS, JS, images)
├── uploads/          # Uploaded documents
└── instance/         # SQLite database
```

## Features

- Item management with categories, materials, and colors
- Document management with categories
- Project management with required items and documents
- Stock level monitoring
- Multi-language support (English and German)
- User-friendly interface with quick actions

## Contributing

Feel free to submit issues and enhancement requests! 