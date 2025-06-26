# Clash of Clans Event Signup Bot

A Discord bot designed to manage event signups for Clash of Clans communities. This bot allows clan leaders to create events and manage player registrations using their in-game tags.

## Features

### Event Management
- Create events with unique names
- Leader role management (add/remove leader roles)
- Event deletion
- Registration closure
- Real-time signup tracking

### Player Management
- Sign up for events using Clash of Clans player tags
- Automatic player verification using CoC API
- Check signup status
- Remove signups (with leader permission)
- Export event participant lists

### Admin Features
- Leader role management
- Event creation/deletion
- Registration closure
- Export participant lists to Excel
- Real-time signup tracking

## Setup Instructions

### Prerequisites
- Python 3.13 or higher
- Discord Bot Token
- Clash of Clans API credentials
- Firebase credentials

### Installation
1. Clone the repository:
```bash
git clone [repository-url]
cd signup-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file with the following variables:
```
DISCORD_TOKEN=your_discord_bot_token
FIREBASE_CRED=your_base64_encoded_firebase_credentials
AUTH=your_auth_token
```

4. Run the bot:
```bash
python bot.py
```

### Docker Deployment
1. Build the Docker image:
```bash
docker build -t signup-bot .
```

2. Run the container:
```bash
docker run -d --name signup-bot -e DISCORD_TOKEN=your_token -e FIREBASE_CRED=your_credentials signup-bot
```

## Usage

### Creating Events
```bash
/create_event [event_name]
```

### Signing Up
```bash
/sign_up [event_name]
```

### Checking Signups
```bash
/check [event_name]
```

### Removing Signups
```bash
/remove [event_name]
```

### Exporting Signups
```bash
/export [event_name]
```

## Contributing
1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## Support
For support, please open an issue in the GitHub repository.

## Acknowledgments
- Discord.py for the Discord bot framework
- Firebase for data storage
- Clash of Clans API for player verification
