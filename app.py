import argparse as ap
import os
from flask import Flask, render_template, request, send_from_directory, session, redirect, url_for
from werkzeug.utils import safe_join
import secrets
import socket
import threading
import time

import logging # Disables flask logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

from model import Password

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

parser = ap.ArgumentParser(prog='localtransfer-py')
parser.add_argument('--path', default=os.getcwd(), help="Directory to share")
parser.add_argument('--length', type=int, default=12, help="Length of auto-generated password")
parser.add_argument('--lifespan', type=int, help="Set a custom lifespan")
group = parser.add_mutually_exclusive_group()
group.add_argument('--password', type=str, help="Set a custom password")
group.add_argument('--autopassword', action='store_true', help="Generate a random password")
args = parser.parse_args()

# Logic to determine the final password
ABSOLUTE_PATH = os.path.abspath(args.path)

if args.lifespan:
    LIFESPAN = args.lifespan
else:
    LIFESPAN = 3153600000

password_exists = True
if args.password or args.autopassword:
    pw_model = Password(password=args.password, length=args.length)
    SECRET_PWD = pw_model.password
    LIFESPAN = pw_model.time_left_seconds
else:
    password_exists = False # Default is no password, TODO : add a warning for that.
    SECRET_PWD = None



try:
    SERVER_DEATH = time.ctime(time.time() + LIFESPAN)
except (OverflowError, OSError):
    SERVER_DEATH = "Indefinite" # Lifespan is too big for a human to bruteforce anyway



def self_destruct_sequence(duration):
    """Background thread that kills the process after the calculated duration."""
    time.sleep(duration)
    print("\n" + "!"*40)
    print(f"SERVER EXPIRED ({duration}s)!")
    print("SERVER SELF-DESTRUCTED.")
    print("!"*40 + "\n")
    os._exit(0)

if SERVER_DEATH != "Indefinite":
    killer_thread = threading.Thread(target=self_destruct_sequence, args=(LIFESPAN,), daemon=True)
    killer_thread.start()

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP



@app.route('/', methods=['GET', 'POST'])
def index():
    server_death = None  # Default is None so the UI stays hidden
    if request.method == 'POST':
        user_input = request.form.get('pwd')
        if user_input == SECRET_PWD:
            session['access_token'] = secrets.token_urlsafe(16)
            server_death=SERVER_DEATH # Only set this on success
        else:
            return "Invalid Password", 401
    elif SECRET_PWD == None:
        session['access_token'] = secrets.token_urlsafe(16)
            
    return render_template('index.html', server_death=server_death, password_state=password_exists)

@app.route('/browse/')
@app.route('/browse/<path:subpath>')
def file_server(subpath=""):
    if 'access_token' not in session:
        return redirect(url_for('index'))
    
    # Securely join the base path with the requested subpath
    requested_path = safe_join(ABSOLUTE_PATH, subpath or "")
    
    if not requested_path or not os.path.exists(requested_path) or not os.path.isdir(requested_path):
            return "Directory not found", 404

    try:
        items = sorted(os.listdir(requested_path))
    except:
        return "Permission denied", 403

    li_elements = []
    
    # Add a "Back" link if we aren't at the root
    if subpath:
        parent_dir = os.path.dirname(subpath)
        back_url = url_for('file_server', subpath=parent_dir) if parent_dir else url_for('file_server')
        li_elements.append(f'<li><a href="{back_url}">.. (Parent Directory)</a></li>')

    for item in items:
        # Create the relative path for the URL
        item_path = os.path.join(subpath, item).replace("\\", "/")
        full_system_path = os.path.join(requested_path, item)
        
        if os.path.isdir(full_system_path):
            # If it's a folder, link to the browse route
            link = url_for('file_server', subpath=item_path)
            display_name = item + "/"
        else:
            # If it's a file, link to the fetch (download) route
            link = url_for('download', filename=item_path)
            display_name = item

        li_elements.append(f'<li><a href="{link}">{display_name}</a></li>')

    links_html = "".join(li_elements)

    return f"""
    <!DOCTYPE HTML>
    <html>
     <head><title>Listing: /{subpath}</title></head>
     <body>
      <a href="https://github.com/shlemmmm/localtransfer-py">Source Code</a>
      <h1>Contents of /{subpath}</h1>
      <hr>
      <ul>{links_html}</ul>
      <hr>
     </body>
    </html>
    """

@app.route('/fetch/<path:filename>')
def download(filename):
    if 'access_token' not in session:
        return "Unauthorized! GTFO", 403
    
    # send_from_directory handles security internally when provided a relative path
    return send_from_directory(ABSOLUTE_PATH, filename, as_attachment=True)

if __name__ == "__main__":
    local_ip = get_local_ip()
    port = 5000
    
    print("\n" + "="*42)
    print("github.com/shlemmmm/localtransfer-py")
    print("="*42)
    print(f"IP:        \thttps://{local_ip}:{port}")
    print(f"PASSWORD:  \t{SECRET_PWD}")
    print(f"TOTAL LIFE:\t{LIFESPAN}s")
    print("="*42+"\n")
    
    app.run(host='0.0.0.0', port=port, ssl_context='adhoc', debug=False)