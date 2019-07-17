#!/usr/bin/env python

# Import packages to build server, database and login
from flask import Flask, render_template, request
from flask import redirect, jsonify, url_for, flash

from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from sportscatalog_db_setup import Base, Category, Item, User

from flask import session as login_session
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests


# Initialise flask app
app = Flask(__name__)


# Load client_secrets.json to enable Google login
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Sportscatalog"


# Connect to Database and create database session
engine = create_engine('sqlite:///sportscatalog.db',
                       connect_args={'check_same_thread': False})
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create login route and state token to identify a user
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


# Google login connection
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data
    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # Error handling for an error in the access token
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = answer.json()

    # Store user email for use in frontend
    login_session['email'] = data['email']

    # Notify user of successful login
    output = ''
    output += '<h1>Welcome, '
    output += login_session['email']
    output += '!</h1>'
    flash("you are now logged in as %s" % login_session['email'])

    # Check if user is already in database_setup
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id
    print "done!"
    return output


# Build user helper functions

# Create a user based on the login session
def createUser(login_session):
    newUser = User(name=login_session['email'], email=login_session[
                   'email'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


# Get all user info from a user_id
def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


# Get user_id from email
def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# Disconnect from Google login
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['email']
    url = 'https://accounts.google.com/o/oauth2/'
    url += 'revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['email']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# Create route to obtain JSON APIs to view Category and Item Information
@app.route('/catalog/JSON')
def catalogJSON():
    categories = session.query(Category).all()
    result = []
    for i in range(1, len(categories)+1):
        categories = session.query(Category).filter_by(id=i).all()
        items = session.query(Item).filter_by(category_id=i).all()
        items_serialized = [it.serialize for it in items]
        result_category = [c.serialize for c in categories]
        for j in range(len(result_category)):
            result_category[j].update({'Item': items_serialized})
        result.append(result_category[0])
    return jsonify(Category=result)

@app.route('/catalog/JSON/category/<string:category_name>')
def categoryJSON(category_name):
    category = session.query(Category).filter_by(name=category_name).one()
    items = session.query(Item).filter_by(category_id=category.id).all()
    return jsonify(Items=[i.serialize for i in items])

@app.route('/catalog/JSON/item/<string:item_name>')
def ItemJSON(item_name):
    items = session.query(Item).filter_by(name=item_name).all()
    return jsonify(Items=[i.serialize for i in items])


# Create route to show all Categories
@app.route('/')
def showCategories():
    categories = session.query(Category).order_by(asc(Category.name))
    items = session.query(Item).order_by(desc(Item.id)).limit(10)
    if 'email' not in login_session:
        return render_template('publicCategories.html', categories=categories,
                               items=items)
    else:
        return render_template('loggedInCategories.html',
                               categories=categories,
                               items=items)


# Create route to show a Category list
@app.route('/catalog/<string:category_name>/items/')
def showCategoryList(category_name):
    category = session.query(Category).filter_by(name=category_name).one()
    categories = session.query(Category).order_by(asc(Category.name))
    creator = getUserInfo(category.user_id)
    items = session.query(Category,
                          Item).join(Category,
                                     Item.category_id ==
                                     Category.id).filter(Category.name ==
                                                         category_name).all()
    count_items = 0
    for item in items:
        count_items += 1
    if 'email' not in login_session:
        return render_template('publicCategoryList.html', items=items,
                               categories=categories, category=category,
                               creator=creator, count_items=count_items)
    else:
        return render_template('loggedInCategoryList.html', items=items,
                               categories=categories, category=category,
                               creator=creator, count_items=count_items)


# Create route to show an Item Description
@app.route('/catalog/<string:category_name>/<string:item_name>/')
def showItemDescription(category_name, item_name):
    category = session.query(Category).filter_by(name=category_name).one()
    creator = getUserInfo(category.user_id)
    items = session.query(Item).filter_by(name=item_name).one()
    if 'email' not in login_session:
        return render_template('publicItemDescription.html', items=items,
                               category=category, creator=creator)
    else:
        return render_template('loggedInItemDescription.html',
                               items=items, category=category, creator=creator)


# Create route to add an item
@app.route('/catalog/addItem', methods=['GET', 'POST'])
def addItem():
    if 'email' not in login_session:
        return redirect('/login')
    categories = session.query(Category).order_by(asc(Category.name))
    if request.method == 'POST':
        cat = 'category'
        category = session.query(
                                 Category
                                 ).filter_by(name=request.form[cat]).one()
        newItem = Item(name=request.form['name'],
                       description=request.form['description'],
                       category=category, user_id=login_session['user_id'])
        session.add(newItem)
        session.commit()
        return redirect(url_for('showCategories'))
    else:
        return render_template('addItem.html', categories=categories)


# Create route to edit an item
@app.route('/catalog/<string:item_name>/edit', methods=['GET', 'POST'])
def editItem(item_name):
    itemToEd = session.query(Item).filter_by(name = item_name).one()
    if 'email' not in login_session:
        return redirect('/login')
    if itemToEd.user_id != login_session['user_id']:
        text = "<script>function myFunction() "
        text += "{alert('You are not authorized"
        text += "');}</script><body onload='myFunction()''>"
        return text
    categories = session.query(Category).order_by(asc(Category.name))
    editedItem = session.query(Item).filter_by(name=item_name).one()
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['category']:
            cat = 'category'
            cat_edit = session.query(
                                     Category
                                     ).filter_by(name=request.form[cat]).one()
            editedItem.category = cat_edit
        session.add(editedItem)
        session.commit()
        return redirect(url_for('showCategories'))
    else:
        return render_template('editItem.html', categories=categories,
                               item=editedItem)


# Create route do delete an item
@app.route('/catalog/<string:item_name>/delete', methods=['GET', 'POST'])
def deleteItem(item_name):
    if 'email' not in login_session:
        return redirect('/login')
    itemToDelete = session.query(Item).filter_by(name=item_name).one()
    if itemToDelete.user_id != login_session['user_id']:
        text = "<script>function myFunction() "
        text += "{alert('You are not authorized"
        text += "');}</script><body onload='myFunction()''>"
        return text
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        return redirect(url_for('showCategories'))
    else:
        return render_template('deleteItem.html', item=itemToDelete)


if __name__ == '__main__':
    app.secret_key = 'project2'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
