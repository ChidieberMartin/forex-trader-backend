from django.apps import AppConfig
import sys
import threading

class ForexConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'forex'
    
    def ready(self):
        # Only start deriv connection for runserver, not management commands
        if len(sys.argv) > 1 and sys.argv[1] not in ['runserver', 'runserver_plus', 'uvicorn']:
            return
        
        # Import here to avoid loading models at module level
        from .deriv_client import start_deriv_connection
        
        connection_thread = threading.Thread(target=start_deriv_connection)
        connection_thread.daemon = True
        connection_thread.start()
        
