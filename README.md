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

The News App uses token authentication for API requests.

1. Register a user or create one through the Django admin page.
2. If required by your project, ensure the user has the appropriate role and permissions.
3. Obtain an API token by sending a POST request to your configured token endpoint. For example, if your project uses Django REST Framework's standard token endpoint:

   ```http
   POST /api-token-auth/
   ```

   Include the username and password in the request body:

   ```json
   {
       "username": "your_username",
       "password": "your_password"
   }
   ```

4. If the request succeeds, the response should contain a token.
5. Include the token in the header of authenticated API requests:

   ```http
   Authorization: Token your_token_here
   ```

**Note:** The token endpoint must be configured in your project's `urls.py`. Check your URL configuration and use the actual endpoint if it differs from `/api-token-auth/`.

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
