# music-map

A visualization tool for users to compare music preferences based purely on waveform data.

## Installation

Follow these steps to set up the music-map project:

1. Clone the repository:

```
git clone https://github.com/AidanAllchin/music-map.git
cd music-map
```

2. Create and activate a new virtual environment:

```
python -m venv venv
source venv/bin/activate  # On Windows, use venv\Scripts\activate
```

3. Run the initialization script:

```
python __init__.py
```

This script will:
- Install required packages from `requirements.txt`
- Create necessary directories
- Download VGGish model files

4. Set up your Spotify API credentials:
- Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
- Create a new application
- Note your Client ID and Client Secret

5. Update the config file:
- Open `config/config.json`
- Replace the placeholders for `client_id` and `client_secret` with your Spotify API credentials
- Note that this step can be done in `__init__.py` as well

6. Run the main application:

```
python main.py
```

## Usage

After installation, run `main.py` to start the application. Follow the prompts to authenticate with Spotify and analyze your playlists or your likes.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the [MIT License](LICENSE).
