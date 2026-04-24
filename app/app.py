#!/usr/bin/env python

import webbrowser
import logging
import signal
import threading

from threading import Lock
from functools import wraps
from datetime import timedelta
from flask import Flask, render_template, request, session, jsonify, redirect, url_for
from flask_socketio import SocketIO, emit

from flask_utility.utility_flask import UtilityFlask
from flask_utility.menu import Menu

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from util.util import Util

# remove debug messages
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# constants
IP_ADDRESS = Util.get_from_json_file("config")['ip'] 
SHUFFLE = Util.get_from_json_file("config")['shuffle'] 
SHUFFLE_TRIALS = Util.get_from_json_file("config")['shuffle_trials'] 

# Creazione dell'app Flask
app = Flask(__name__, template_folder="./animal_game/template", static_folder="./animal_game/static")
app.config['SECRET_KEY'] = 'secret!'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)
app.config["SESSION_PERMANENT"] = True
socketio = SocketIO(app)

# Application State Manager
class AppState:
    """Manages application state with thread-safe operations."""
    def __init__(self):
        self.client_instances = {}
        self.lock = Lock()
        self.first_start = True
        self.exit_pressed = False
        self.menu_thread_active = False  # Flag to track if menu thread is running
    
    def add_client(self, user_id, utility_flask):
        """Add a client instance with thread safety."""
        with self.lock:
            self.client_instances[user_id] = utility_flask
    
    def get_client(self, user_id):
        """Get a client instance with thread safety."""
        with self.lock:
            return self.client_instances.get(user_id)
    
    def remove_client(self, user_id):
        """Remove a client instance with thread safety."""
        with self.lock:
            return self.client_instances.pop(user_id, None)
    
    def clear_all_clients(self):
        """Clear all client instances."""
        with self.lock:
            self.client_instances.clear()

app_state = AppState()

# global
experimental_condition = None   # new experimental condition received from menu     
cleanup_flag = False            # clear session after CTRL+C
id_player = -1                  # only used for HRI

# read player id from command line and check if dir with that id already exists
id_player = int(sys.argv[1])
Util.check_if_dir_with_id_already_exists(id_player)

def convert_condition_to_str(int_experimental):
    """
    Converts an integer experimental condition code to a string representation.

    Args:
        int_experimental (int): An integer representing the experimental condition:
            - 0: Competent robot (correct card - correct curiosity)
            - 1: Semi-competent robot (wrong card - correct curiosity)
            - 2: Non-competent robot (wrong card - wrong curiosity)

    Returns:
        str: The string representation of the condition:
            - "C" for competent         - (correct card - correct curiosity)
            - "SC" for semi-competent   - (wrong card - correct curiosity)
            - "NC" for non-competent    - non competent (wrong card - wrong curiosity)
    """
    if int_experimental == 0:
        return "C"      
    elif int_experimental == 1:
        return "SC"     
    else:               
        return "NC"   

experimental_condition = int(sys.argv[2])
if experimental_condition not in [0, 1, 2]:
    Util.formatted_debug_message("Do want to choose the experimental condition?", level='INFO')
    Util.formatted_debug_message("Exit...", level='INFO')
    sys.exit(1)

def get_id():
    """Get current user ID from session."""
    return session.get('id')

def get_utility_flask(user_id, log_context):
    """Get utility flask instance for a user with thread safety."""
    utility_flask = app_state.get_client(user_id)
    if utility_flask is None:
        Util.formatted_debug_message(f"[{log_context}] No client instance for user {user_id}", level='WARNING')
        return None
    return utility_flask

def create_new_session(data):
    """Create a new session for a user."""
    Util.create_dir_for_current_user(id_player)
    session['id'] = id_player
    session['language'] = data.get('language')
    Util.formatted_debug_message(f"Session created for user {id_player}", level='INFO')

def cleanup_user_session(user_id):
    """Clean up all user resources and session data."""
    app_state.remove_client(user_id)
    session.clear()
    Util.formatted_debug_message(f"User session {user_id} cleaned up", level='INFO')

def validate_session(f):
    """Decorator to validate user session before accessing protected routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('id')
        if not user_id:
            Util.formatted_debug_message("Access denied: No valid session", level='WARNING')
            return jsonify({'error': 'No valid session'}), 401
        return f(*args, **kwargs)
    return decorated_function

def run_menu_in_background():
    """Run menu operations in a background thread to avoid blocking the web client."""
    global experimental_condition, id_player
    
    def menu_thread():
        try:
            global experimental_condition, id_player
            # Show admin menu
            res = Menu._handle_admin_menu()
            
            if not res:
                Util.formatted_debug_message("Exiting from menu...", level='INFO')
                app_state.exit_pressed = True
                threading.Timer(2.0, os._exit, args=[0]).start()
            else:
                # Show experimental condition menu only if not exiting
                experimental_condition = Menu._handle_admin_menu_experimental_condition(experimental_condition)
                # Increment player ID for next game
                id_player += 1
                Util.formatted_debug_message(f"Menu completed. Next player ID: {id_player}", level='INFO')
                app_state.first_start = False
        except Exception as e:
            Util.formatted_debug_message(f"Error in menu thread: {str(e)}", level='ERROR')
        finally:
            app_state.menu_thread_active = False
    
    # Start menu in a daemon thread so it doesn't block the web server
    if not app_state.menu_thread_active:
        app_state.menu_thread_active = True
        thread = threading.Thread(target=menu_thread, daemon=True)
        thread.start()
        Util.formatted_debug_message("Menu thread started in background", level='INFO')

def clear_session():
    """Clear session and remove client instance."""
    user_id = session.get('id')
    if user_id:
        cleanup_user_session(user_id)

@app.route('/get_id', methods=["GET", "POST"])
def provide_id():
    return jsonify({"id": id_player})

@app.route('/', methods=["GET", "POST"])
@app.route('/index', methods=["GET", "POST"])
def index():
    """Home page route - shows home immediately and handles menu in background."""
    global experimental_condition, id_player

    # If this is not the first start and menu is not already running, start it in background
    if not app_state.first_start and not app_state.exit_pressed and not app_state.menu_thread_active:
        run_menu_in_background()
    
    # Set first_start to False after first visit
    if app_state.first_start:
        app_state.first_start = False
    
    # Always return home page immediately (non-blocking)
    return render_template('home_page.html', session_shuffle=SHUFFLE, session_trials=SHUFFLE_TRIALS)

@app.route('/set_settings', methods=["POST"])
def set_setting():
    # unpack request
    data = request.get_json()

    # create a session for new user, otherwise delete it and create a new one
    if 'id' not in session:
        Util.formatted_debug_message("Creating new session...", level='Settings')
        create_new_session(data)
    else:
        clear_session()
        Util.formatted_debug_message("Session cleared...", level='Settings')
        create_new_session(data)
    
    Menu.clean_shell()
    # return response
    response = jsonify({"message": "ok"})
    response.status_code = 200
    return redirect(url_for("show_game", _external=True), Response=response)

@app.route("/game", methods=["POST", "GET"])
def show_game():
    global experimental_condition
    
    if request.method == "GET":
        user_id = get_id()
        if user_id is not None and app_state.get_client(user_id) is None:
            Util.formatted_debug_message(f"Showing game page to user ID={user_id}", level='INFO')
            experimental_condition_str = convert_condition_to_str(experimental_condition)
            Util.formatted_debug_message(f"Experimental condition is {experimental_condition_str}", level='INFO')
            # create instance for user
            utility_flask = UtilityFlask()
            app_state.add_client(user_id, utility_flask)
            # handle player and run Q-learning
            utility_flask.handle_id_player(user_id, experimental_condition, experimental_condition_str)
            return render_template("index.html", session_id=session.get('id'), session_language=session.get('language'), 
                                   session_shuffle=SHUFFLE, session_trials=SHUFFLE_TRIALS)

    return render_template("index.html", session_id=session.get('id'), session_language=session.get('language'), 
                           session_shuffle=SHUFFLE, session_trials=SHUFFLE_TRIALS)
      
@app.route('/rl_exit', methods=["POST"])
def rl_agent_exit():
    user_id = session.get('id')
    if user_id:
        Util.formatted_debug_message(f"Received data for closing connection with RL agent from user {user_id}", level='INFO')
        # get instance for current user
        utility_flask = get_utility_flask(user_id, "Exit")
        if utility_flask is None:
            return jsonify({'error': 'No client instance'}), 400
        # handle game board and return response
        utility_flask.handle_rl_agent_exit()  
        return jsonify({'message': 'closed connection with rl agent'}), 200
    else:
        Util.formatted_debug_message(f"Closing connection: id user not found", level='INFO')
        return jsonify({'error': 'No client instance'}), 400
    
@app.route('/robot_exit', methods=["POST"])
def robot_exit(id):
    user_id = id  # Use URL parameter, not session
    Util.formatted_debug_message(f"Received data for closing connection with Robot", level='INFO')
    # get instance for current user
    utility_flask = get_utility_flask(user_id, "Exit")
    
    if utility_flask is None:
        return jsonify({'error': 'No client instance'}), 400
    
    # handle game board and return response
    utility_flask.handle_robot_exit()  

    return jsonify({'message': 'closed connection with rl agent'}), 200

# exit UI
@app.route('/exit', methods=['GET'])
def exit():
    """Handle exit from game - returns immediately to home page."""
    user_id = session.get('id')
    if user_id:
        Util.formatted_debug_message(f"User ID={user_id} pressed 'exit'", level='INFO')
        cleanup_user_session(user_id)
    
    Menu.clean_shell()
    Util.formatted_debug_message("Redirecting to home page", level='INFO')
    # Return immediately to home without blocking
    return redirect(url_for("index"))

@app.route('/game_board/<int:id>', methods=["POST"])
def receive_game_board(id):
    user_id = id  # Use URL parameter
    Util.formatted_debug_message(f"Received game board for user ID={user_id}", level='INFO')
    # get instance for current user
    utility_flask = get_utility_flask(user_id, "Game Board")
    
    if utility_flask is None:
        return jsonify({'error': 'No client instance'}), 400
    
    # handle game board and return response
    return utility_flask.handle_game_board(request)

@app.route('/player_move/<int:id>', methods=["POST"])
def receive_player_move_data(id):
    user_id = id  # Use URL parameter
    # get instance for current user
    utility_flask = get_utility_flask(user_id, "Player move")
    if utility_flask is None:
        return jsonify({'error': 'No client instance'}), 400
    
    return utility_flask.handle_player_move(request, socketio)

@app.route('/cheating/<int:id>', methods=["GET", "POST"])
def def_cheater(id):
    user_id = session.get('id')
    Menu.clean_shell()
    Util.formatted_debug_message("Page reloaded during the game...", level='INFO')
    utility_flask = app_state.get_client(user_id)
    if utility_flask is not None:
        utility_flask.handle_cheater()
        utility_flask.handle_id_player(user_id, utility_flask, experimental_condition)
    
    return redirect(url_for("show_game"))

@app.route('/robot_speech/<int:id>', methods=["POST"])
def handle_pop_up(id):
    user_id = id  # Use URL parameter
    utility_flask = get_utility_flask(user_id, "Robot speech")
    if utility_flask is None:
        return jsonify({'error': 'No client instance'}), 400
    
    return utility_flask.handle_robot_speech(request, socketio)
    
@app.route('/turn_change/<int:id>', methods=["POST"])
def handle_turn_change(id):
    user_id = id  # Use URL parameter
    utility_flask = get_utility_flask(user_id, "Agent")
    if utility_flask is None:
        return jsonify({'error': 'No client instance'}), 400
    
    # notify q-learning algorithm that it's robot turn
    return utility_flask.handle_turn_change(request, socketio)

@app.route('/agent_move/<int:id>', methods=["POST"])
def handle_agent_move(id):
    user_id = id  # Use URL parameter (from mixed_team.py)
    utility_flask = get_utility_flask(user_id, "Agent Move")
    if utility_flask is None:
        return jsonify({'error': 'No client instance'}), 400
    
    # notify q-learning algorithm that it's robot turn
    return utility_flask.handle_agent_move(request, socketio)

@app.before_request
def before_request():
    """Handle pre-request operations including cleanup."""
    global cleanup_flag
    if cleanup_flag:
        Util.formatted_debug_message("Cleaning session before exiting...", level='INFO')
        app_state.clear_all_clients()
        session.clear()
        os._exit(0)

@app.after_request
def set_session_timeout(response):
    """Set session timeout and refresh session timer."""
    session.permanent = True
    app.permanent_session_lifetime = timedelta(hours=1)
    return response

def handle_exit(*args):
    global cleanup_flag
    Util.formatted_debug_message('(Server) CTRL-C pressed!', level='INFO')
    Util.formatted_debug_message(f"Close web page and open it again if you want to play again!", level='INFO')
    Util.formatted_debug_message("Exit...", level='INFO')
    cleanup_flag = True
    os._exit(0)

if __name__ == '__main__':
    # handle CTRL+C
    signal.signal(signal.SIGINT, handle_exit)
    # run app
    print("Running on http://" + IP_ADDRESS + ":5000/ (Press CTRL+C to quit)")
    print("Experimental condition is " + convert_condition_to_str(experimental_condition))
    print("\t - C: Both card choice and curiosity are correct (Competent robot)")
    print("\t - SC: Card choice is correct but curiosity is wrong (Semi-competent robot)")
    print("\t - NC: Both card choice and curiosity are wrong (Non-competent robot)")
    print("Server started. Opening URL http://" + IP_ADDRESS + ":5000 ...")
    import time
    time.sleep(1)
    webbrowser.open(f"http://{IP_ADDRESS}:5000", autoraise=True)
    socketio.run(app, host=IP_ADDRESS, port=5000, debug=True, use_reloader=False, log_output=False)