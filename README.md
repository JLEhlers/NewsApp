# News App

## Description

The News App is a Django web application that allows users to read, write, review and manage news articles. Users have different roles: Readers, Editors and Journalists. Readers can subscribe to publishers and journalists to view relevant articles.

## Features

- User registration and login.
- Different user roles: Reader, Editor and Journalist.
- Journalists can create news articles and newsletters.
- Editors can review, approve and delete articles.
- Readers can browse articles and subscribe to publishers and journalists.
- REST API for accessing and managing articles.
- Token authentication for API requests.
- Email notifications when articles are approved.

## Installation

1. Clone or download the project.
2. Open the project folder in your terminal.
3. Create and activate a virtual environment.
4. Install the required packages:

## Running Tests

Run the automated tests with:

python manage.py test news.tests

