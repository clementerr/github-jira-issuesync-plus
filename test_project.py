import pytest
from project import get_jira_project, get_jira_api, create_jira_issue, create_flask_app, simulate_github_webhook

@pytest.fixture(scope='module')
def app():
    """
    This fixture creates a Flask application instance with test configuration
    and yields it for use in tests within the same module.

    Returns:
        Flask: A configured Flask application instance.
    """

    test_config = {
        'APP_NAME': "Issue Sync",
        'TESTING': True,
        'DEBUG': False
    }

    app = create_flask_app(test_config)

    yield app

@pytest.fixture(scope='module')
def test_client(app):
    """
    This fixture creates a test client for the Flask application created in the 'app' fixture.
    It yields the test client for use in tests within the same module.

    Args:
        app (Flask): The Flask application instance created by the 'app' fixture.

    Yields:
        flask.testing.Client: A test client for interacting with the Flask application.
    """

    yield app.test_client()

def test_simulate_github_webhook(test_client):
    """
    This test simulates sending different types of GitHub webhook payloads to the
    '/issue' endpoint and asserts the expected behavior based on the payload data.

    Args:
        test_client (flask.testing.Client): The test client from the 'test_client' fixture.
    """

    # Issue opened but label "sync-to-jira" is not applied to it, so no action performed
    response = simulate_github_webhook(test_client, "gh_webhook_open_issue_without_label.json")
    assert response.status_code == 200
    assert 'No action performed.' in response.text

    # Issue already opened and label "sync-to-jira" is applied to it, so it is created in jira project
    response = simulate_gh_webhook(test_client, "gh_webhook_label_issue_already_opened.json")
    assert response.status_code == 201
    assert '"id":' in response.text

    # Issue is opened and label "sync-to-jira" is applied to it at the same time, so it is created in jira project
    response = simulate_gh_webhook(test_client, "gh_webhook_open_issue_with_label.json")
    assert response.status_code == 201
    assert '"id":' in response.text

    # The issue already exists so no action is performed
    response = simulate_gh_webhook(test_client, "gh_webhook_open_issue_with_label.json")
    assert response.status_code == 200
    assert 'No action performed.' in response.text

    # Deletes the issue that already exists in jira project
    response = simulate_gh_webhook(test_client, "gh_webhook_delete_issue.json")
    assert response.status_code == 204

def test_get_jira_api():
    """
    This test verifies that the get_jira_api function returns a valid JiraAPI object.

    It asserts that the returned object has the expected:
        - ID (set during initialization)
        - Name (set during initialization)
    """

    jira_api = get_jira_api()
    assert jira_api.id == 1
    assert jira_api.name == "Jira API"

def test_get_jira_project():
    """
    This test verifies that the get_jira_project function returns a valid JiraProject object
    for a specific project key ("CD" in this case).

    It asserts that the returned object for project key "CD" has the expected:
        - ID
        - Name
        - Lead display name
    """

    jira_project = get_jira_project("CD")
    assert jira_project.id == "10002"
    assert jira_project.name == "Python project"
    assert jira_project.lead_displayname == "Clemente Reyes Ricardo"

def test_create_jira_issue():
    """
    This test verifies that the create_jira_issue function returns a valid JiraIssue object
    populated with sample data (loaded from a JSON file).

    It asserts that the returned object has the expected:
        - ID (from the sample data)
        - Title (from the sample data)
    """

    jira_issue = create_jira_issue()
    assert jira_issue.id == "2425281906"
    assert jira_issue.title == "Fix bug 2"
