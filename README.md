# Discord Bot Panel

A simple web panel for managing a Python Discord bot. This panel provides a user-friendly interface for monitoring and controlling your Discord bot.

## Features

- User authentication system
- Bot status monitoring (online/offline, PID, uptime)
- Bot control (start, restart, stop)
- Live console logs with color highlighting
- SSH key management for Git integration
- Webhook endpoint for automatic updates
- File editor for whitelisted configuration files
- User management
- Environment variable management
- Dark mode UI with Tailwind CSS

## Requirements

- Python 3.10+
- Supabase account (for database)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/discord-bot-panel.git
   cd discord-bot-panel
   ```

2. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Configure the application:
   - Run the application once to generate a default `.env` file:
     ```
     python run.py
     ```
   - Edit the `.env` file and add your Supabase credentials

4. Create the first admin user:
   ```
   python run.py create-user
   ```

5. Start the application:
   ```
   python run.py
   ```

6. Access the panel at http://localhost:8000

## Bot Integration

1. Place your Discord bot code in the `./bot` directory
2. Make sure your bot has a virtual environment in `./bot/venv`
3. The main bot script should be named `bot.py` (or configure a different name in `.env`)

## Webhook Integration

1. Generate a webhook URL and key in the panel
2. Add the webhook URL to your Git repository (GitHub, GitLab, etc.)
3. The panel will automatically pull changes and restart the bot when you push to the main branch

## License

This project is licensed under the MIT License - see the LICENSE file for details.
