# Consultation Platform

This repository contains a consultation platform built with Django.

## Getting Started

Follow these steps to get the project up and running on your local machine.

### Prerequisites

- Python 3.x
- pip (Python package installer)

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/Satyajit-pradhan-232/consultation_platform.git
cd Consultation_platform
```

2. **Create a virtual environment**

```bash
# For Windows
python -m venv venv

# For macOS/Linux
python3 -m venv venv
```

3. **Activate the virtual environment**

```bash
# For Windows
venv\Scripts\activate

# For macOS/Linux
source venv/bin/activate
```

4. **Install dependencies**

```bash
pip install -r requirements.txt
```

5. **Navigate to the project directory**

```bash
cd consultation_platform
```

6. **Create environment variables file**

```bash
# Create a .env file based on the example

# On Windows, use:
copy .env.example .env

# On macOS/Linux, use:
cp .env.example .env

# Edit the .env file and add your credentials
# Use your favorite text editor to modify the .env file
```

7. **Run the application with Daphne**

```bash
daphne -p 8000 consultation_platfrom.asgi:application
```

Now the application should be running at [http://localhost:8000](http://localhost:8000).

## Technologies Used

- Django Rest Framework
- Django Channels for WebSocket Support
- Daphne for ASGI support
- Redis
- Postgres
