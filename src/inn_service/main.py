from inn_service.core.application import Application
from inn_service.app_container import ApplicationContainer


application = Application(ApplicationContainer)
application.run()