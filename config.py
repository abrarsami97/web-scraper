import os

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')
    UPLOAD_FOLDER = 'downloads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'logs/app.log'

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    # Add production-specific settings
    SECRET_KEY = os.environ.get('SECRET_KEY')  # Must be set in production
    LOG_LEVEL = 'WARNING'

class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = True
    TESTING = True

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 