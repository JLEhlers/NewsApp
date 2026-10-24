# News App

## Description

The News App is a Django web application that allows users to read, write, review and manage news articles. Users have different roles: Readers, Editors and Journalists. Readers can subscribe to publishers and journalists to view relevant articles.

## Features

- User registration and login.
- Different user roles: Reader, Editor and Journalist.
- Journalists can create news articles and newsletters.
- Editors can review, approve, update and delete articles.
- Editors can manage newsletters.
- Readers can browse articles and subscribe to publishers and journalists.
- REST API for accessing and managing articles.
- Token authentication for API requests.
- Email notifications when articles are approved.

## Installation

1. Clone or download the project from GitHub.

2. Open the project folder in your terminal.

3. Create a virtual environment:

   ```bash
   python -m venv myenv
   ```

4. Activate the virtual environment.

   **Windows PowerShell:**

   ```powershell
   myenv\Scripts\activate
   ```

   **Mac/Linux:**

   ```bash
   source myenv/bin/activate
   ```

5. Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

6. Create a MariaDB database.

   Log in to MariaDB:

   ```sql
   mariadb -u root -p
   ```

   Create the database:

   ```sql
   CREATE DATABASE news_app;
   EXIT;
   ```

   If the `mariadb` command is not recognised, use your MariaDB/MySQL client or open the MySQL command-line client provided by your installation.

7. Configure the database connection.

   Open `settings.py` and configure the `DATABASES` setting to use the database you created. For example:

   ```python
   DATABASES = {
       "default": {
           "ENGINE": "django.db.backends.mysql",
           "NAME": "news_app",
           "USER": "root",
           "PASSWORD": "your_database_password",
           "HOST": "localhost",
           "PORT": "3306",
       }
   }
   ```

   Replace `your_database_password` with your local database password. If your project uses environment variables, configure these values in your `.env` file instead. Do not commit passwords or secret keys to GitHub.

8. Run the database migrations:

   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

9. Create an administrator account:

   ```bash
   python manage.py createsuperuser
   ```

   Follow the prompts to enter a username, email address and password.

10. Start the development server:

    ```bash
    python manage.py runserver
    ```

11. Open the application in your browser:

    `http://127.0.0.1:8000/`

    You can access the Django admin page at:

    `http://127.0.0.1:8000/admin/`

## API Authentication

The News App uses token authentication for protected REST API endpoints.

1. Register a user or create one through the Django admin page.
2. Send a POST request to the token endpoint:

   `http://127.0.0.1:8000/api/token/`

3. Include your username and password in the JSON request body:

   ```json
   {
       "username": "your_username",
       "password": "your_password"
   }
   ```

4. If the credentials are valid, the API returns an authentication token:

   ```json
   {
       "token": "your_authentication_token"
   }
   ```

5. Include the token in the `Authorization` header when accessing protected API endpoints:

   ```http
   Authorization: Token your_authentication_token
   ```

**Note:** The token endpoint is configured in `news/urls.py` using Django REST Framework's `obtain_auth_token` view. The endpoint requires a POST request with valid user credentials.

## Publisher Management

The News App allows authorised editors and Django administrators
to manage publishers through the application interface.

### Managing Publishers

1. Log in with an editor account or a Django superuser account.
2. Open the Manage Publishers page.
3. Select Create Publisher.
4. Enter the publisher's name and description.
5. Select the existing editors and journalists affiliated with
   the publisher.
6. Submit the form to create the publisher.
7. Return to Manage Publishers to review the publisher and its
   assigned staff.

### User Roles and Staff Assignments

- Readers can browse articles and subscribe to publishers and
  journalists.
- Journalists can create independent articles or articles on
  behalf of publishers with which they are affiliated.
- Editors can review and approve articles and manage publishers.
- Django superusers can access publisher management regardless
  of their application role.

Editors and journalists must already have registered accounts
before they can be assigned to a publisher. The publisher form
only allows users with the appropriate role to be selected.

### Access Control

Publisher management views require authentication. Only users
with the editor role, membership in the Editor group, or Django
superuser privileges can access the management and creation pages.

The publisher creation form uses Django CSRF protection and
validates the selected staff members.

## Running Tests

Run the automated tests with:

```bash
python manage.py test news.tests
```

## Running Tests

Run the automated tests with:

```bash
python manage.py test news.tests
```

## Notes

- MariaDB must be running before you start the application.
- Make sure your database credentials match your local MariaDB configuration.
- Email notifications depend on the email settings configured in `settings.py`.
- Do not commit your `.env` file, database passwords or Django secret key to GitHub.
