from django.apps import AppConfig
import threading

class ForexConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'forex'
    
    def ready(self):
        # start deriv connection when django starts
        from .deriv_client import start_deriv_connection
        
        # Start separete thread to avoid django startup
        connection_thread = threading.Thread(target=start_deriv_connection)
        connection_thread.daemon = True
        connection_thread.start()
        
