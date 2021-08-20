import sqlite3
import logging
import logging.config

import os
import sys
from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash

from werkzeug.exceptions import abort
path = os.getcwd()

total_connections = 0
'''
log_format = "INFO:%(name)s:127.0.0.1 - - [08/Jan/2021 22:40:06] "GET /metrics HTTP/1.1" 200 -
# logger = logging.getLogger(__name__)
# formatter = logging.Formatter(log_format)
log_format = '%(levelname)s: %(name)s %(asctime)s  %(threadName)s : %(message)s'
file_handler = logging.FileHandler(filename=path + '/app.log',
                                   filemode='w')
stdout_handler = logging.StreamHandler(sys.stdout),
handlers = [file_handler, stdout_handler]

logging.basicConfig(level=logging.DEBUG,
                    format=log_format,
                    datefmt="%F %A %T",
                    handlers = handlers,
                    force=True)
'''
# Project 1 : Healthcheck and Metric endpoints
logging.config.fileConfig('logging.cfg')
logger = logging.getLogger('techTrends')


# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    global total_connections
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post

# Function to keep track of database connections for metrics
def count_db_connection():
    global total_connections
    total_connections += 1
    return total_connections

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    count_db_connection()
    return render_template('index.html', posts=posts)

@app.route('/healthz')
def healthcheck():
    # log line
    app.logger.info('Status request successful')
    return (jsonify({"result": "OK - Healthy"}),
            200,
            {'Content-Type': 'application/json'})

@app.route('/metrics')
def metrics():
    # log line
    connection = get_db_connection()
    posts = len(connection.execute('SELECT * FROM posts').fetchall())
    connections = connection.execute('')
    app.logger.info("Metrics request successfull")
    return (jsonify({
        "result": "OK - Healthy",
        "status": "success",
        "code": 0,
        "data": {"db_connection_count": total_connections, "post_count": posts}}),
            201,
            {'Content-Type': 'application/json'})

# Define how each individual article is rendered
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
        logging.error('Error (404): %s page not found')
        return render_template('404.html'), 404
    else:
        logging.info('Article: %s', post['title'])
        count_db_connection()
        return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    logging.info('Page: About Us')
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',(title, content))
            connection.commit()
            connection.close()
            logging.info('New post: %s', title)
            count_db_connection()

            return redirect(url_for('index'))

    return render_template('create.html')

# start the application on port 3111
if __name__ == "__main__":
   # app.run(host='0.0.0.0', port='3111')
   app.run(host='127.0.0.1', port='3111')

