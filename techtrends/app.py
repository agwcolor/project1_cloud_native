import sqlite3
import logging
import logging.config

import os
import sys
from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash

from werkzeug.exceptions import abort
# path = os.getcwd()

total_connections = 0

# Project 1 : Healthcheck and Metric endpoints
logger = logging.getLogger(__name__)
logging.config.fileConfig('logging.cfg')


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

# Return health check
@app.route('/healthz')
def healthcheck():
    # log line
    app.logger.info('Status request successful')
    return (jsonify({"result": "OK - Healthy"}),
            200,
            {'Content-Type': 'application/json'})

# Route for metrics
@app.route('/metrics')
def metrics():
    # log line
    connection = get_db_connection()
    posts = len(connection.execute('SELECT * FROM posts').fetchall())
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
        app.logger.error('Error (404): Page not found')
        return render_template('404.html'), 404
    else:
        app.logger.info('Article, "%s" retrieved!', post['title'])
        count_db_connection()
        return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    app.logger.info('Page, "About Us", retrieved!')
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
            app.logger.info('New post: %s', title)
            count_db_connection()

            return redirect(url_for('index'))

    return render_template('create.html')

# start the application on port 3111
if __name__ == "__main__":
   app.run(host='0.0.0.0', port='3111')
   # app.run(host='127.0.0.1', port='3111')

