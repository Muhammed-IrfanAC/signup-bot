# Clash of Clans Event Signup Bot

A Discord bot designed to manage event signups for Clash of Clans communities. This bot allows clan leaders to create events and manage player registrations using their in-game tags.

## 🚀 Features

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
- Export event participant lists to Excel

### Admin Features
- Leader role management
- Event creation/deletion
- Registration closure
- Real-time signup tracking
- Data export functionality
- **Event logging system** - Track all event actions in designated channels

## 🏗️ Project Structure

```
signup-bot/
├── signup_bot/               # Main package
│   ├── __init__.py           # Package initialization and config
│   ├── bot.py                # Main bot class and setup
│   ├── api/                  # API implementation
│   │   ├── __init__.py       # API app factory
│   │   ├── routes/           # API route handlers
│   │   │   ├── __init__.py
│   │   │   ├── events.py     # Event-related routes
│   │   │   └── admin.py      # Admin-related routes
│   ├── cogs/                 # Discord cogs (command modules)
│   │   ├── __init__.py
│   │   ├── admin.py          # Admin commands
│   │   ├── events.py         # Event management commands
│   │   └── utilities.py      # Utility commands
├── env.example               # Example environment variables
├── requirements.txt          # Python dependencies
├── run.py                    # Bot entry point
└── run_api.py                # API server entry point
```

## 🛠️ Setup Instructions

### Prerequisites
- Python 3.10 or higher
- Discord Bot Token
- Clash of Clans API credentials
- Firebase credentials (service account JSON)

### Installation

1. **Clone the repository**
   ```bash
   git clone [repository-url]
   cd signup-bot
   ```

2. **Set up a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   - Copy `env.example` to `.env`
   - Fill in your credentials:
     ```
     DISCORD_TOKEN=your_discord_bot_token
     FIREBASE_CRED=your_base64_encoded_firebase_credentials
     AUTH=your_clash_of_clans_api_token
     ```

5. **Encode Firebase credentials**
   ```bash
   # Use the provided script to encode your Firebase JSON file
   python encode_firebase.py path/to/your/firebase-credentials.json
   ```
   Copy the output and paste it as the `FIREBASE_CRED` value in your `.env` file.

## 🚦 Running the Application

The application consists of two main components:

### 1. Discord Bot
```bash
python run.py
```

### 2. API Server
```bash
python run_api.py
```

### Using Docker

1. **Build the images**
   ```bash
   docker-compose build
   ```

2. **Run the services**
   ```bash
   docker-compose up -d
   ```

## 🤖 Available Commands

### Event Commands
- `/create_event [name]` - Create a new event
- `/list_events` - List all events
- `/sign_up [event]` - Sign up for an event
- `/check [event]` - Check your signup status
- `/remove [event]` - Remove your signup
- `/export [event]` - Export event data

### Admin Commands
- `/add_leader_role [role]` - Add a role as a leader
- `/remove_leader_role [role]` - Remove a leader role
- `/list_leader_roles` - List all leader roles

### Utility Commands
- `/ping` - Check bot latency
- `/uptime` - Check bot uptime
- `/version` - Show bot version
- `/invite` - Get bot invite link

### Event Commands (Updated)
- `/create_event [name] [role] [log_channel]` - Create a new event with optional role and logging
- `/list_events` - List all events
- `/sign_up [event]` - Sign up for an event
- `/check [event]` - Check your signup status
- `/remove [event]` - Remove your signup
- `/export [event]` - Export event data

## 📝 Event Logging

The bot now includes a comprehensive logging system that tracks all event-related actions and sends detailed logs to a designated Discord channel.

### Features
- **Automatic Logging**: All event actions (create, signup, remove, export, close) are automatically logged
- **User Information**: Each log includes the user's name and avatar who performed the action
- **Success/Failure Tracking**: Logs show whether actions succeeded or failed with detailed error messages
- **Rich Embeds**: Logs are sent as formatted Discord embeds with relevant information

### Setup
When creating an event, you can specify an optional log channel:
```
/create_event name:War Event role:@Warrior log_channel:#event-logs
```

### Log Format
Each log entry includes:
- User performing the action (name + avatar)
- Action type and success/failure status
- Event context and relevant details
- Error information if the action failed

For detailed documentation, see [LOGGING_FEATURE.md](LOGGING_FEATURE.md).

## 🔧 Development

1. **Code Style**
   - Follow PEP 8 guidelines
   - Use type hints for better code clarity
   - Document public methods and classes

2. **Testing**
   - Write tests for new features
   - Run tests with `pytest`

3. **Pull Requests**
   - Fork the repository
   - Create a feature branch
   - Submit a pull request with a clear description

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Discord.py](https://discordpy.readthedocs.io/) - Python library for Discord
- [Firebase](https://firebase.google.com/) - Backend services
- [Clash of Clans API](https://developer.clashofclans.com/) - Player verification
