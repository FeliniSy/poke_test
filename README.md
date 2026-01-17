# Pokémon ETL Pipeline

A high-performance ETL (Extract, Transform, Load) pipeline for fetching Pokémon data from the PokeAPI, storing it in PostgreSQL, downloading media files, and uploading them to Google Cloud Storage.

## Features

- **Fast Data Fetching**: Concurrent processing of up to 50 Pokémon simultaneously
- **Database Storage**: PostgreSQL database with connection pooling (up to 20 connections)
- **Media Management**: Automatic download and upload to Google Cloud Storage
- **Error Handling**: Comprehensive error handling and logging
- **Performance Optimized**: Designed to complete processing in under 10 minutes

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────┐
│   PokeAPI   │────▶│  PostgreSQL  │────▶│  Downloads  │────▶│ GCS  │
└─────────────┘     └──────────────┘     └─────────────┘     └──────┘
```

## Requirements

- Python 3.8+
- PostgreSQL database
- Google Cloud Storage account (for media uploads)
- Environment variables configured (see `.env.example`)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd poke_api
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Set up the database:
   - Run the SQL schema in `sql_manager/queries.sql` to create the required tables
   - Ensure your database is accessible via the `DB_URL` connection string

## Configuration

Create a `.env` file in the root directory with the following variables:

```env
# API URLs
POKE_URL=https://pokeapi.co/api/v2/pokemon
ABILITY_URL=https://pokeapi.co/api/v2/ability

# Database
DB_URL=postgresql://user:password@localhost:5432/pokemon_db

# Google Cloud Storage
PROJECT_ID=your-gcp-project-id
BUCKET_NAME=your-gcs-bucket-name
POKE_GCS_URL=https://storage.googleapis.com/your-bucket-name/pokemon
```

## Usage

Run the main pipeline:

```bash
python main.py
```

The pipeline will:
1. Fetch Pokémon IDs from the API (limit: 1400)
2. Fetch detailed data for each Pokémon concurrently
3. Save Pokémon data and abilities to PostgreSQL
4. Download media files (sprites, forms) to local `downloads/` folder
5. Upload media files to Google Cloud Storage
6. Save media URLs to the database

## Project Structure

```
poke_api/
├── etl/
│   ├── extract/          # Data fetching from PokeAPI
│   │   ├── pokemon_fetcher.py
│   │   ├── id_fetcher.py
│   │   └── media_extractor.py
│   ├── load/             # Database operations
│   │   ├── pokemon_saver.py
│   │   ├── ability_saver.py
│   │   └── media_saver.py
│   ├── download/         # Media download operations
│   │   └── media_downloader.py
│   ├── pokemon/          # Pokémon data models
│   │   ├── pokemon.py
│   │   └── pokemon_factory.py
│   └── upload/           # GCS upload operations
│       └── media_uploader.py
├── sql_manager/          # SQL queries and connection pool
│   ├── pool.py
│   ├── queries.py
│   ├── queries.sql
│   └── ability.py
├── utils/                # Utilities
│   ├── helper.py
│   ├── logger.py
│   └── settings.py
├── main.py              # Main entry point
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Database Schema

The pipeline creates and populates the following tables:

- `pokes`: Main Pokémon data (id, name, base_experience, height, weight, order)
- `ability`: Pokémon abilities (id, name, url, url_id)
- `pokes_ability`: Many-to-many relationship between Pokémon and abilities
- `poke_media`: Media URLs for each Pokémon

See `sql_manager/queries.sql` for the complete schema.

## Performance

- **Concurrent Processing**: 50 workers for fetching, 50 for downloading, 20 for uploading
- **Connection Pooling**: Up to 20 database connections
- **Batch Operations**: Database operations use batch inserts for efficiency
- **Expected Runtime**: Under 10 minutes for 1400 Pokémon

## Error Handling

- All database operations are wrapped in try-except blocks
- Failed operations are logged but don't stop the pipeline
- Connection pool management ensures resources are properly cleaned up
- Automatic cleanup of empty folders after uploads

## Logging

The application uses Python's standard logging module. Logs include:
- Info: Pipeline progress and statistics
- Warning: Skipped operations (e.g., missing abilities)
- Error: Failed operations with details

## Contributing

1. Follow PEP 8 style guidelines
2. Add error handling for new features
3. Update documentation for significant changes
4. Test with a small subset before full pipeline runs

## License

[Your License Here]

## Support

For issues or questions, please open an issue in the repository.
