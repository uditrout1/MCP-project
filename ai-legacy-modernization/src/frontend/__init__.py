"""
Frontend module initialization.
This module provides the frontend interface for the application.
"""

from flask import Flask, render_template, request, jsonify
import os
import logging

# Create Flask app
app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
            static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Import views after app creation to avoid circular imports
from . import views
