import random
import string
import httplib2
import json
import requests

from functools import wraps

from flask import Flask, render_template, request, redirect, jsonify, url_for
from flask import flash, make_response
from flask import session as login_session

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item, User

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Item Catalog"

# Connect to Database and create database session
engine = create_engine('sqlite:///itemcatalog.db',
                       connect_args={'check_same_thread': False})
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' in login_session:
            return f(*args, **kwargs)
        else:
            flash("You need to be logged in to perform this action")
            return redirect('/login')
    return decorated_function


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state, CLIENT_ID=CLIENT_ID)


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

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    if getUserID(data['email']) is None:
        createUser(login_session)

    login_session['user_id'] = getUserID(data['email'])

    output = ''
    output += '<h2>Welcome, '
    output += login_session['username']
    output += '!</h2>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "border-radius: 150px;'
    output += '-webkit-border-radius: 150px;-moz-border-radius: 150px;'
    output += 'display: block;'
    output += 'margin-left: auto;'
    output += 'margin-right: auto;"> '
    flash("You are now logged in as %s" % login_session['username'])
    return output


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(
            json.dumps('User not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s' % access_token
    print 'User name is: '
    print login_session['username']

    access_token = login_session['access_token']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token

    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        return redirect('/')
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# Show all categories
@app.route('/')
@app.route('/categories/')
def showCategories():
    categories = session.query(Category).order_by(asc(Category.name))
    return render_template('categories.html', categories=categories,
                           username=login_session.get('username'))


# Show one category
@app.route('/category/<int:category_id>/')
def showItemsOfCategory(category_id):
    category = session.query(Category).filter_by(id=category_id).one_or_none()
    if category is None:
        flash('Requested category does not exist')
        return redirect(url_for('showCategories'))
    items = session.query(Item).filter_by(category_id=category_id)
    return render_template('category.html', items=items, name=category.name,
                           username=login_session.get('username'))


# Show an item
@app.route('/item/<int:item_id>/')
def showItem(item_id):
    item = session.query(Item).filter_by(id=item_id).one_or_none()
    if item is None:
        flash('Requested item does not exist')
        return redirect(url_for('showCategories'))
    category = session.query(Category).filter_by(
                                         id=item.category_id).one_or_none()
    if category is None:
        # should not happen unless someone deleted the category after
        # the previous SQL query
        flash('Internal error: item does not have a category')
        return redirect(url_for('showCategories'))
    return render_template('item.html', item=item, category=category,
                           user_id=login_session.get('user_id'),
                           username=login_session.get('username'))


# Create a new item
@app.route('/item/new/', methods=['GET', 'POST'])
@login_required
def newItem():
    if request.method == 'POST':
        if 'name' not in request.form:
            flash('No name parameter present in request')
            return redirect(url_for('newItem'))
        if len(request.form['name']) == 0:
            flash('The name must not be empty')
            return redirect(url_for('newItem'))
        if 'category_id' not in request.form:
            flash('No category id parameter present in request')
            return redirect(url_for('newItem'))
        category = session.query(Category).filter_by(
                           id=request.form['category_id']).one_or_none()
        if category is None:
            flash('Provided category does not exist')
            return redirect(url_for('newItem'))

        newItem = Item(name=request.form['name'],
                       description=request.form.get('description', ''),
                       category_id=request.form['category_id'],
                       user_id=login_session['user_id'])
        session.add(newItem)
        session.commit()
        flash('Successfully created item %s' % (newItem.name))
        return redirect(url_for('showItemsOfCategory',
                                category_id=request.form['category_id']))
    else:
        categories = session.query(Category).order_by(asc(Category.name))
        return render_template('newitem.html', categories=categories,
                               username=login_session.get('username'))


# Edit an item
@app.route('/item/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def editItem(item_id):
    editedItem = session.query(Item).filter_by(id=item_id).one_or_none()
    if editedItem is None:
        flash('Item deleted in the meantime')
        return redirect(url_for('showCategories'))
    if editedItem.user_id != login_session['user_id']:
        flash('You are not the creator of the item')
        return redirect(url_for('showItem', item_id=item_id))
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['category_id']:
            category = session.query(Category).filter_by(
                               id=request.form['category_id']).one_or_none()
            if category is None:
                flash('Could not update item category')
                return redirect(url_for('showItem', item_id=item_id))
            editedItem.category_id = request.form['category_id']
        session.add(editedItem)
        session.commit()
        flash('Item Successfully Edited')
        return redirect(url_for('showItem', item_id=item_id))
    else:
        categories = session.query(Category).order_by(asc(Category.name))
        return render_template('edititem.html', item=editedItem,
                               categories=categories,
                               username=login_session.get('username'))


# Delete an item
@app.route('/item/<int:item_id>/delete', methods=['GET', 'POST'])
@login_required
def deleteItem(item_id):
    itemToDelete = session.query(Item).filter_by(id=item_id).one_or_none()
    if itemToDelete is None:
        flash('Item deleted in the meantime')
        return redirect(url_for('showCategories'))
    if itemToDelete.user_id != login_session['user_id']:
        flash('You are not the creator of the item')
        return redirect(url_for('showItem', item_id=item_id))
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Item Successfully Deleted')
        return redirect(url_for('showItemsOfCategory',
                                category_id=itemToDelete.category_id))
    else:
        return render_template('deleteitem.html', item=itemToDelete,
                               username=login_session.get('username'))


# JSON APIs
@app.route('/category/<int:category_id>/JSON')
def categoryJSON(category_id):
    items = session.query(Item).filter_by(category_id=category_id).all()
    return jsonify(Items=[i.serialize for i in items])


@app.route('/item/<int:item_id>/JSON')
def itemJSON(item_id):
    item = session.query(Item).filter_by(id=item_id).one_or_none()
    if item is None:
        return jsonify(Item={})
    return jsonify(Item=item.serialize)


@app.route('/categories/JSON')
def categoriesJSON():
    categories = session.query(Category).all()
    return jsonify(Categories=[c.serialize for c in categories])


# Helper methods
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one_or_none()
    return user


def getUserID(email):
    user = session.query(User).filter_by(email=email).one_or_none()
    if user is None:
        return None
    return user.id


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
