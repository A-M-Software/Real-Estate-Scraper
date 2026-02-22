# Advertisements Scraper

Collects new advertisements from:
- Olx (not implemented yet)
- Dim.Ria

And sends them to configured telegram chat.

## Configuration

Create `.env` file based on `.env.example` and fill in the values:
```dotenv
# Base settings
LOG_LEVEL=INFO
LOG_PATH=
LOG_ECHO=false

# Telegram settings
TELEGRAM_TOKEN=<token>
TELEGRAM_CHAT_ID=<chat_id>

# Dim.Ria settings
DIM_RIA_API_KEY=<api-key>
DIM_RIA_CITY_IDS=[25]
DIM_RIA_DATA_FILE=data/dim_ria.pkl

# OLX settings
OLX_API_KEY=<api-key>
OLX_DATA_FILE=data/olx.pkl
```

## Usage

### Running with Docker

Build Docker container:
```shell
$ docker build -t scraper .
```

Run the container, specifying **logs** and **data** volumes (so they will be stored on the host machine):
```shell
$ docker run -v ./logs:/logs -v ./data:/data scraper
```

Alternatively, you can run `run.sh` script, which will do the same:
```shell
$ ./run.sh
```

### If you want to run the script without Docker, you need to:

Create and activate virtual environment:
```shell
$ python -m venv venv
$ source venv/bin/activate
```

Upgrade PIP and install dependencies:
```shell
$ pip install --upgrade pip
$ pip install -r requirements.txt
```

Then you can run the script:
```shell
$ python run.py
```

Parameters:
- `--after_date` - date & time in format `YYYY-MM-DD HH:MM:SS`. If specified, only advertisements published after this date will be collected.

### Setup Cron job

To set up cron job, run `crontab -e` and add the following line (you can change the schedule as you wish, the example below runs the script every hour):
```cron
0 * * * * /<directory>/run.sh
```

## Collecting

By default, all advertisements are collected and sent to telegram.
After the first run, collected advertisements will be saved to data file, so on the next runs only new advertisements will be collected.

Data is saved using Python `pickle` module in `/dat`a directory.
You can change the path to data file in `.env` file
(but make sure to mount this volume in Docker container if you are using Docker).
