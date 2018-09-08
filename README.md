# Item Catalog

A web application that offers a catalog of items grouped under various categories.

## Installation

Retrieve a copy of this project by running:
```
git clone https://github.com/a9t/nd-fs-item-catalog
```

### Prerequisites

In order to run this project, you will need:
* python 2.7 (later versions might work as well, but I have not tested them)
* SQLAlchemy - https://www.sqlalchemy.org/
* Flask - http://flask.pocoo.org/

### Google secret

The application uses third party authentication through Google, so you will need to register a new project with [Google Cloud Console](https://console.cloud.google.com). Once you have your project, create OAuth credentials for Web application, adding the following URLs under the headings:
* Authorized JavaScript origins
  * http://localhost:5000
* Authorized redirect URIs
  * http://localhost:5000/login
  * http://localhost:5000/gconnect

Save the configuration and download the json to the root of the project under the name client_secrets.json. 

You may check this video https://youtu.be/8aGoty0VXgw for a step by step tutorial of the procedure.

### Database

The application uses an SQLite database stored in itemcatalog.db which needs to be initiated with categories. You may do this by modifying the prefill.py file with the categories you wish your application to have. The provided file contains several categories, items and fake users for testing purposes.
Once you are done modifying the file, you may populate the database by running the following command:
```
python prefill.py
```

## Usage

Run the web application with:
```
python catalog.py
```

(Note that the server listens on port 5000 on all interfaces. If you would like to change the port, edit the catalog.py file; this will also require recreating the secrect file.)

Open your favorite browser and type in localhost:5000 to check that the application is running correctly.

### JSON API

Apart from the regular HTML application, there are also several JSON endpoints that can be accesed at:
* /categories/JSON
* /category/<id>/JSON
* /item/<id>/JSON
