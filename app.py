from flask import Flask
from controllers.routes import init_routes
import os

app = Flask(__name__, template_folder='views/templates')

app.secret_key = os.urandom(24) 

# Initialize routes from the controller
init_routes(app)

if __name__ == '__main__':
    app.run(debug=True)