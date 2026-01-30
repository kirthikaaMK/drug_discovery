import os
import json
import logging
from pathlib import Path

class Config:
    """Centralized configuration management for the drug discovery system"""

    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.config_file = self.base_dir / 'config.json'
        self._load_config()

    def _load_config(self):
        """Load configuration from file or create defaults"""
        default_config = {
            "app": {
                "host": "0.0.0.0",
                "port": 5000,
                "debug": True,
                "secret_key": "dev-secret-key-change-in-production"
            },
            "apis": {
                "market_api_url": "",
                "market_api_key": "",
                "exim_api_url": "",
                "exim_api_key": "",
                "patent_api_url": "",
                "patent_api_key": "",
                "clinical_api_url": "",
                "clinical_api_key": "",
                "internal_api_url": "",
                "internal_api_key": "",
                "web_api_url": "",
                "web_api_key": "",
                "literature_api_url": "",
                "literature_api_key": "",
                "pubmed_api_key": ""
            },
            "ml": {
                "enable_ml_prediction": True,
                "enable_generative_ai": True,
                "enable_nlp_analysis": True,
                "model_cache_dir": str(self.base_dir / "models"),
                "max_memory_gb": 4.0
            },
            "data": {
                "data_dir": str(self.base_dir / "data"),
                "cache_dir": str(self.base_dir / "cache"),
                "max_cache_age_hours": 24
            },
            "logging": {
                "level": "INFO",
                "file": str(self.base_dir / "logs" / "drug_discovery.log"),
                "max_file_size_mb": 10,
                "backup_count": 3
            }
        }

        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    user_config = json.load(f)
                # Deep merge user config with defaults
                self._deep_merge(default_config, user_config)
            except Exception as e:
                print(f"Warning: Could not load config file: {e}. Using defaults.")
        else:
            # Create default config file
            self._save_config(default_config)

        self.config = default_config

        # Override with environment variables
        self._load_from_env()

    def _deep_merge(self, base, update):
        """Deep merge two dictionaries"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def _load_from_env(self):
        """Load configuration from environment variables"""
        env_mappings = {
            'FLASK_HOST': ('app', 'host'),
            'FLASK_PORT': ('app', 'port'),
            'FLASK_DEBUG': ('app', 'debug'),
            'SECRET_KEY': ('app', 'secret_key'),
            'PUBMED_API_KEY': ('apis', 'pubmed_api_key'),
            'MARKET_API_URL': ('apis', 'market_api_url'),
            'MARKET_API_KEY': ('apis', 'market_api_key'),
            'EXIM_API_URL': ('apis', 'exim_api_url'),
            'EXIM_API_KEY': ('apis', 'exim_api_key'),
            'PATENT_API_URL': ('apis', 'patent_api_url'),
            'PATENT_API_KEY': ('apis', 'patent_api_key'),
            'CLINICAL_API_URL': ('apis', 'clinical_api_url'),
            'CLINICAL_API_KEY': ('apis', 'clinical_api_key'),
            'INTERNAL_API_URL': ('apis', 'internal_api_url'),
            'INTERNAL_API_KEY': ('apis', 'internal_api_key'),
            'WEB_API_URL': ('apis', 'web_api_url'),
            'WEB_API_KEY': ('apis', 'web_api_key'),
            'LITERATURE_API_URL': ('apis', 'literature_api_url'),
            'LITERATURE_API_KEY': ('apis', 'literature_api_key'),
            'ENABLE_ML_PREDICTION': ('ml', 'enable_ml_prediction'),
            'ENABLE_GENERATIVE_AI': ('ml', 'enable_generative_ai'),
            'ENABLE_NLP_ANALYSIS': ('ml', 'enable_nlp_analysis'),
            'MAX_MEMORY_GB': ('ml', 'max_memory_gb')
        }

        for env_var, (section, key) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert string values to appropriate types
                if isinstance(self.config[section][key], bool):
                    self.config[section][key] = value.lower() in ('true', '1', 'yes', 'on')
                elif isinstance(self.config[section][key], int):
                    try:
                        self.config[section][key] = int(value)
                    except ValueError:
                        pass
                elif isinstance(self.config[section][key], float):
                    try:
                        self.config[section][key] = float(value)
                    except ValueError:
                        pass
                else:
                    self.config[section][key] = value

    def _save_config(self, config):
        """Save configuration to file"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save config file: {e}")

    def get(self, section, key=None, default=None):
        """Get configuration value"""
        if key is None:
            return self.config.get(section, default)
        return self.config.get(section, {}).get(key, default)

    def set(self, section, key, value):
        """Set configuration value"""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
        self._save_config(self.config)

    def ensure_directories(self):
        """Ensure all required directories exist"""
        dirs_to_create = [
            self.get('ml', 'model_cache_dir'),
            self.get('data', 'data_dir'),
            self.get('data', 'cache_dir'),
            Path(self.get('logging', 'file')).parent
        ]

        for dir_path in dirs_to_create:
            Path(dir_path).mkdir(parents=True, exist_ok=True)

    def is_ml_enabled(self, feature):
        """Check if ML feature is enabled"""
        return self.get('ml', f'enable_{feature}', True)

    def get_memory_limit(self):
        """Get memory limit in GB"""
        return self.get('ml', 'max_memory_gb', 4.0)

# Global config instance
config = Config()