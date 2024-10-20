import sys
from flask import Flask, request, jsonify, make_response
from jira import JiraProject, JiraIssue, JiraAPI
import json
from pyfiglet import Figlet

def create_flask_app(test_config=None):
    """
    This function creates a Flask application instance.

    Args:
        test_config (dict, optional): A dictionary containing configuration options for testing. Defaults to None.

    Returns:
        Flask: A configured Flask application instance.
    """

    app = Flask(__name__, instance_relative_config=True)

    app_name = "Flask app"

    if test_config is not None:
        # load the test config if passed in
        app.config.update(test_config)
        app_name = test_config["APP_NAME"]

    # Show app name
    figlet = Figlet(font="standard")
    print(figlet.renderText(f"{app_name}"))

    # Routes definitions
    @app.route('/issue', methods=['POST'])
    def issue_route():
        """
        This route handles incoming POST requests on the '/issue' endpoint.
        It expects JSON data from a GitHub webhook request and processes it
        using the JiraIssue.request_handler method.

        Returns:
            flask_response: A Flask response object containing the processed data.
        """

        # Get the JSON data from github webhook request
        if  (github_issue_info := request.get_json()) is None:
            return jsonify({'error': 'No JSON data provided.'})

        response = JiraIssue.request_handler(github_issue_info)
        response_message = JiraIssue.response_handler(response)
        print(response_message)

        # Constructing a Flask response from the requests.Response object
        flask_response = make_response(response.content, response.status_code)
        flask_response.headers['Content-Type'] = response.headers['Content-Type']

        return flask_response

    return app

def main():
    """
    This function is the entry point for the application when run directly.
    It creates a Flask app with test configuration and runs it.
    """

    test_config = {
        'APP_NAME': "Issue Sync",
        'TESTING': True,
        'DEBUG': False
    }

    app = create_flask_app(test_config)

    app.run(host='0.0.0.0')

def simulate_github_webhook(flask_client, json_file: str):
    """
    This function simulates a GitHub webhook request by sending a POST request
    to the '/issue' endpoint with data loaded from a JSON file.

    Args:
        flask_client (flask.testing.Client): A Flask test client instance.
        json_file (str): The path to the JSON file containing the payload data.

    Returns:
        response: The response object from the Flask application.
    """

    try:
        with open(json_file, "r") as f:
            payload = json.load(f)
    except FileNotFoundError:
        sys.exit(f"The file {json_file} does not exist.")

    response = flask_client.post("/issue", json=payload)

    return response

def get_jira_api() -> JiraAPI:
    """
    This function returns a new JiraAPI instance for interacting with the Jira server.

    Returns:
        JiraAPI: A JiraAPI instance.
    """

    return JiraAPI()

def get_jira_project(project_key: str) -> JiraProject:
    """
    This function creates and returns a JiraProject instance for a given project key.

    Args:
        project_key (str): The project key for the Jira project.

    Returns:
        JiraProject: A JiraProject instance for the specified project.
    """

    jira_api = JiraAPI()
    jira_project = JiraProject("jira", project_key, jira_api)

    return jira_project

def create_jira_issue() -> JiraIssue:
    """
    This function creates a JiraIssue instance for testing purposes.
    It simulates the data structure of a GitHub webhook payload by loading it from a JSON file.

    Returns:
        JiraIssue: A JiraIssue instance populated with sample data.
    """

    # Load JSON file that mimics the JSON data from the Github webhook
    with open('gh_webhook_open_issue_with_label.json') as f:
        src_issue_info = json.load(f)

    jira_issue = JiraIssue("issue_dict", src_issue_info)

    return jira_issue

if __name__ == "__main__":
    main()
