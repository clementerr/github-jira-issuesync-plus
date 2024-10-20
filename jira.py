import sys
import os
import json
import re
from typing import Optional
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

class JiraAPI():
    """
    This class represents a Jira API and provides methods for interacting with the Jira server.
    """

    def __init__(self) -> None:
        """
        Initializes a JiraAPI object.

        - Loads API definitions from a JSON file (jira_api_info.json).
        - Loads credentials (username and token) from environment variables (.env).
        - Sets up authentication using username and token.
        """

        api_defs = self.get_api_info("jira_api_info.json")

        self.id = api_defs["id"]
        self.name = api_defs["name"]
        self.auth_type = api_defs["authentication"]["type"]
        self.load_jira_creds()
        self.auth = self.get_auth(self.get_user(), self.get_token())
        self.base_url = api_defs["base_url"]
        self.endpoints = api_defs["endpoints"]

    @staticmethod
    def get_api_info(file_name) -> dict:
        """
        Loads API definitions from a JSON file.

        - Raises FileNotFoundError if the file doesn't exist.

        Args:
            file_name (str): The name of the JSON file containing API definitions.

        Returns:
            dict: A dictionary containing the API definitions.
        """

        try:
            with open(file_name) as f:
                return json.load(f)
        except FileNotFoundError:
            sys.exit(f"The file {file_name} does not exist.")


    def get_endpoint(self, endpoint_name: str) -> dict:
        """
        Retrieves the details of a specific API endpoint from the loaded definitions.

        - Raises SystemExit if the endpoint is not found.

        Args:
            endpoint_name (str): The name of the API endpoint.

        Returns:
            dict: A dictionary containing the details of the endpoint (method, path, headers).
        """

        try:
            return next(endpoint for endpoint in self.endpoints if endpoint["name"] == endpoint_name)
        except StopIteration:
            sys.exit(f"Endpoint '{endpoint_name}' not found.")

    @staticmethod
    def load_jira_creds():
        """
        Loads Jira API credentials (username and token) to the environment from environment variables in file .env.

        - Uses the `dotenv` library.
        """

        load_dotenv()

    @staticmethod
    def get_user() -> str:
        """
        Retrieves the username for Jira API authentication from environment variable.

        Returns:
            str: The username for Jira API authentication.
        """

        return os.getenv("JIRA_API_USER", "")

    @staticmethod
    def get_token() -> str:
        """
        Retrieves the API token for Jira API authentication from environment variable.

        Returns:
            str: The API token for Jira API authentication.
        """

        return os.getenv("JIRA_API_TOKEN", "")

    @staticmethod
    def get_auth(user: str, token: str) -> HTTPBasicAuth:
        """
        Creates an HTTPBasicAuth object for authentication with Jira API.

        Args:
            user (str): The username for Jira API authentication.
            token (str): The API token for Jira API authentication.

        Returns:
            HTTPBasicAuth: An HTTPBasicAuth object for authentication.
        """

        return HTTPBasicAuth(user, token)

class JiraProject():
    """
    This class represents a Jira project and provides methods for interacting with it.
    """

    def __init__(self, source_type: str, key: str, jira_api: Optional[JiraAPI] = None) -> None:
        """
        Initializes a JiraProject object.

        Args:
            source_type (str): The source for project information ("json" or "jira").
            key (str): The key of the Jira project.
            jira_api (Optional[JiraAPI], optional): A JiraAPI object (required for "jira" source).

        Raises:
            ValueError: If source_type is not supported or jira_api is None for "jira" source.
        """

        match source_type:
            case "json":
                self.initialize_from_json(key)
            case "jira":
                if jira_api is not None:
                    self.initialize_from_jira(key, jira_api)
                else:
                    raise ValueError("jira_api must not be None for source_type 'jira'")
            case _:
                sys.exit(f"Unsupported source type {source_type}")

    def initialize_from_jira(self, key: str, jira_api: JiraAPI) -> None:
        """
        Initializes a JiraProject object from Jira API project data.

        Args:
            key (str): The key of the Jira project.
            jira_api (JiraAPI): A Jira API object used to interact with the Jira server.
        """

        response = self.get_project(jira_api, key)
        project_info = json.loads(response.text)

        self.id = project_info["id"]
        self.key = project_info["key"]
        self.name = project_info["name"]
        self.description = project_info["description"]
        self.project_type = project_info["projectTypeKey"]
        self.lead_accountid = project_info["lead"]["accountId"]
        self.lead_displayname = project_info["lead"]["displayName"]

    def initialize_from_json(self, key: str) -> None:
        """
        Initializes a JiraProject object from a JSON file.

        Args:
            key (str): The key of the Jira project.

        Raises:
            FileNotFoundError: If the JSON file (jira_projects.json) does not exist.
            StopIteration: If the project with the given key is not found in the JSON file.
        """

        try:
            with open("jira_projects.json", "r") as file:
                self.data = json.load(file)
        except FileNotFoundError:
            sys.exit("The file jira_projects.json does not exist.")

        try:
            project_info = next((project for project in self.data["projects"] if project["key"] == key))
        except StopIteration:
            sys.exit(f"Project with id {key} not found.")

        self.id = id,
        self.key = project_info["key"]
        self.name = project_info["name"]
        self.description = project_info["description"]
        self.project_type = project_info["projectTypeKey"]
        self.lead_accountid = project_info["lead"]["accountId"]
        self.lead_displayname = project_info["lead"]["displayName"]

    @staticmethod
    def get_project(jira_api: JiraAPI, key: str) -> requests.Response:
        """
        Retrieves project information from Jira API.

        Args:
            jira_api (JiraAPI): A Jira API object used to interact with the Jira server.
            key (str): The key of the Jira project.

        Returns:
            requests.Response: The response from the Jira API.
        """

        endpoint_info = jira_api.get_endpoint("get_project")

        response = requests.request(
            endpoint_info["method"],
            jira_api.base_url + endpoint_info["path"].format(projectIdOrKey=key),
            headers = endpoint_info["headers"],
            auth = jira_api.auth
        )

        return response

    @staticmethod
    def get_issuetypes(jira_api: JiraAPI, project_key: str) -> requests.Response:
        """
        Retrieves available issue types for a project from Jira API.

        Args:
            jira_api (JiraAPI): A Jira API object used to interact with the Jira server.
            project_key (str): The key of the Jira project.

        Returns:
            requests.Response: The response from the Jira API.
        """

        endpoint_info = jira_api.get_endpoint("get_metadata_issuetypes")

        response = requests.request(
            endpoint_info["method"],
            jira_api.base_url + endpoint_info["path"].format(projectIdOrKey=project_key),
            headers=endpoint_info["headers"],
            auth=jira_api.auth
        )

        return response

    @staticmethod
    def get_metadata_issuetype(jira_api: JiraAPI, project_key: str, issue_type_id: str) -> requests.Response:
        """
        Retrieves metadata for a specific issue type from Jira API.

        Args:
            jira_api (JiraAPI): A Jira API object used to interact with the Jira server.
            project_key (str): The key of the Jira project.
            issue_type_id (str): The ID of the issue type.

        Returns:
            requests.Response: The response from the Jira API.
        """

        endpoint_info = jira_api.get_endpoint("get_metadata_issuetype")

        response = requests.request(
            endpoint_info["method"],
            jira_api.base_url + endpoint_info["path"].format(projectIdOrKey=project_key, issueTypeId=issue_type_id),
            headers = endpoint_info["headers"],
            auth = jira_api.auth
        )

        return response

class JiraIssue():
    """
    This class represents a Jira issue and provides methods for interacting with it.
    """

    GITHUB_SYNC_LABEL = "sync-to-jira"

    def __init__(self, source_type: str, issue_info: Optional[dict] = None, issue_id: Optional[str] = None, jira_api: Optional[JiraAPI] = None) -> None:
        """
        Initializes a JiraIssue object.

        Args:
            source_type (str): The source for issue information ("issue_dict" or "jira").
            issue_info (Optional[dict], optional): Issue information as a dictionary.
            issue_id (Optional[str], optional): The ID of the Jira issue (required for "jira" source).
            jira_api (Optional[JiraAPI], optional): A JiraAPI object (required for "jira" source).

        Raises:
            ValueError: If source_type is not supported or jira_api is None for "jira" source.
        """

        match source_type:
            case "issue_dict":
                if issue_info is not None:
                    self.initialize_from_dict(issue_info)
            case "jira":
                if issue_id is not None and jira_api is not None:
                    self.initialize_from_jira(issue_id, jira_api)
            case _:
                sys.exit(f"Unsupported source type {source_type}")

    def initialize_from_jira(self, id: str, jira_api: JiraAPI) -> None:
        """
        Initializes a JiraIssue object from Jira API issue data.

        Args:
            id (str): The ID of the Jira issue.
            jira_api (JiraAPI): A Jira API object used to interact with the Jira server.
        """

        response = self.get_issue(jira_api, id)
        issue_info = json.loads(response.text)

        self.id = issue_info["id"]
        self.key = issue_info["key"]
        self.name = issue_info["name"]
        self.description = issue_info["description"]
        self.project_type = issue_info["projectTypeKey"]
        self.lead_accountid = issue_info["lead"]["accountId"]
        self.lead_displayname = issue_info["lead"]["displayName"]

    def initialize_from_dict(self, issue_info: dict) -> None:
        """
        Initializes a JiraIssue object from a dictionary.

        Args:
            issue_info (dict): A dictionary containing issue information.
        """

        self.id = str(issue_info["issue"]["id"])
        self.title = issue_info["issue"]["title"]
        self.action = issue_info["action"]
        self.number = issue_info["issue"]["number"]
        self.url = issue_info["issue"]["url"]
        self.user = issue_info["issue"]["user"]["login"]
        self.label_name = issue_info["issue"]["labels"]
        self.state = issue_info["issue"]["state"]
        self.created_at = issue_info["issue"]["created_at"]
        self.updated_at = issue_info["issue"]["updated_at"]
        self.body = issue_info["issue"]["body"]
        self.repository = issue_info["repository"]["full_name"]

    @staticmethod
    def get_issue(jira_api: JiraAPI, issue_id: str) -> requests.Response:
        """
        Retrieves a Jira issue from the Jira API.

        Args:
            jira_api (JiraAPI): A Jira API object used to interact with the Jira server.
            issue_id (str): The ID of the Jira issue.

        Returns:
            requests.Response: The response from the Jira API.
        """

        endpoint_info = jira_api.get_endpoint("get_issue")

        response = requests.request(
            endpoint_info["method"],
            jira_api.base_url + endpoint_info["path"].format(issueIdOrKey=issue_id),
            headers = endpoint_info["headers"],
            auth = jira_api.auth
        )

        return response

    @staticmethod
    def response_handler(response: requests.Response) -> str:
        """
        Handles the response from Jira API calls.

        Args:
            response (requests.Response): The response from the Jira API.

        Returns:
            str: A formatted message indicating the success or failure of the action.
        """

        try:
            # Parse the JSON response
            data = json.loads(response.text)
        except json.JSONDecodeError:
            print("Failed to decode JSON response")
            return

        match (response.status_code, data["action_performed"]):

            case (201, "open"):
                return f'Action performed: open. Successfully created Jira issue with id {data["id"]} and key {data["key"]} from Github issue with id {data["github_issue_id"]} and Github action {data["github_issue_action"]}'
            case (204, "delete"):
                return f'Action performed: delete. Successfully deleted Jira issue with id {data["id"]} corresponding to Github issue with id {data["github_issue_id"]} and Github action {data["github_issue_action"]}'
            case (200, "No action"):
                return f'Action performed: No action when processing Github issue id {data["github_issue_id"]} and Github action {data["github_issue_action"]}'
            case _:
                return f"Jira issue action {data['action_performed']} failed with status code: {str(response.status_code)}"

    @staticmethod
    def request_handler(issue_info: dict) -> requests.Response:
        """
        Handles the GitHub webhook request and interacts with Jira API.

        Args:
            issue_info (dict): The data from the GitHub webhook.

        Returns:
            requests.Response: The response from the Jira API or a default response if no action is taken.
        """

        sync_actions = ("labeled", "deleted")

        # Default Response object to return if no action is handled
        response = requests.Response()
        response.status_code = 200
        response._content = b'{"action_performed": "No action"}'
        response.headers["Content-Type"] = "application/json"

        if issue_info["action"] in sync_actions:

            jira_api = JiraAPI()
            jira_project = JiraProject("jira", "CD", jira_api)
            jira_issue_id = JiraIssue.github_issue_exists(jira_api, jira_project.key, issue_info["issue"]["id"])

            if issue_info["action"] == "labeled" and issue_info["label"]["name"] == JiraIssue.GITHUB_SYNC_LABEL:

                if jira_issue_id == "0":
                    # Issue was opened in github
                    jira_issue = JiraIssue("issue_dict", issue_info)
                    response = jira_issue.open(jira_api, jira_project)
                    # Add action performed to response.text
                    response_dict = json.loads(response.text)
                    response_dict["action_performed"] = "open"
                    response._content = json.dumps(response_dict).encode("utf-8")

            else:
                # action deleted does not contain any label
                if jira_issue_id != "0":
                    response = JiraIssue.delete(jira_api, jira_issue_id)
                    # Create response.text with action performed key because deleted API reponse returns empty .text
                    #response._content = f'{{"action_performed": "delete", "id": "{jira_issue_id}"}}'
                    response._content = f'{{"action_performed": "delete", "id": "{jira_issue_id}"}}'.encode('utf-8')

        # Add Github issue id and action to response.text
        response_dict = json.loads(response.text)
        response_dict["github_issue_id"] = issue_info["issue"]["id"]
        response_dict["github_issue_action"] = issue_info["action"]
        response._content = json.dumps(response_dict).encode("utf-8")

        return response

    @staticmethod
    def delete(jira_api: JiraAPI, issue_id: str) -> requests.Response:
        """
        Deletes a Jira issue.

        Args:
            jira_api (JiraAPI): A Jira API object used to interact with the Jira server.
            issue_id (str): The ID of the Jira issue.

        Returns:
            requests.Response: The response from the Jira API.
        """

        endpoint_info = jira_api.get_endpoint("delete_issue")

        response = requests.request(
            endpoint_info["method"],
            jira_api.base_url + endpoint_info["path"].format(issueIdOrKey=issue_id),
            auth = jira_api.auth
        )

        return response

    @staticmethod
    def github_issue_exists(jira_api: JiraAPI, project_key: str, github_issue_id: str) -> str:
        """
        Checks if a Jira issue exists for a given GitHub issue ID in a specific project.

        Args:
            jira_api (JiraAPI): A Jira API object for interacting with the Jira server.
            project_key (str): The key of the Jira project to search.
            github_issue_id (str): The ID of the GitHub issue.

        Returns:
            str:
            - The ID of the Jira issue if found (as a string).
            - "0" if no matching Jira issue is found.
        """

        response = JiraIssue.jql_issue_search(jira_api, f"project = {project_key} AND description ~ \"githubIssueId: {github_issue_id}\n\"")
        if json.loads(response.text)["total"] == 1:
            return json.loads(response.text)["issues"][0]["id"]
        else:
            return "0"

    @staticmethod
    def jql_issue_search(jira_api: JiraAPI, jql_query: str) -> requests.Response:
        """
        Searches for Jira issues using a JQL (Jira Query Language) query.

        Args:
            jira_api (JiraAPI): A Jira API object for interacting with the Jira server.
            jql_query (str): The JQL query string.

        Returns:
            requests.Response: The response from the Jira API containing the search results.
        """

        endpoint_info = jira_api.get_endpoint("search_for_issues_using_JQL")

        query = {
            "jql": jql_query
        }

        response = requests.request(
            endpoint_info["method"],
            jira_api.base_url + endpoint_info["path"],
            headers = endpoint_info["headers"],
            params=query,
            auth = jira_api.auth
        )

        return response

    def open(self, jira_api: JiraAPI, jira_project: JiraProject) -> requests.Response:
        """
        Opens (creates) a new Jira issue based on information from a GitHub issue.

        Args:
            self (JiraIssue): The JiraIssue object representing the GitHub issue information.
            jira_api (JiraAPI): A Jira API object for interacting with the Jira server.
            jira_project (JiraProject): The JiraProject object representing the target project.

        Returns:
            requests.Response: The response from the Jira API containing the creation result.
        """

        endpoint_info = jira_api.get_endpoint("open_issue")

        # Default issue type is Bug
        issue_type_name = "Bug"

        if self.body is not None:
            # Check for issuetype keyword:value in issue comment
            keyword = "githubIssueType"
            pattern = re.compile(rf"{keyword}\s*:\s*(.*)")
            if (match := pattern.search(self.body)):
                issue_type_name = match.group(1)

        project_issue_types = JiraProject.get_issuetypes(jira_api, jira_project.key)

        # Pythonic way
        try:
            issue_type_id = next(project_issue_type["id"] for project_issue_type in json.loads(project_issue_types.text)["issueTypes"] if project_issue_type["name"] == issue_type_name)
        except StopIteration:
            sys.exit(f"Issue type {issue_type_name} does not exist in project {jira_project.key}.")

        list_of_fields = JiraProject.get_metadata_issuetype(jira_api, jira_project.key, issue_type_id)

        data = json.loads(list_of_fields.text)
        required_fields = [field for field in data["fields"] if field["required"]]

        dst_issue_info: dict = {}
        dst_issue_info["fields"] = {}

        for field in required_fields:
            match field["fieldId"]:
                case "project":
                    dst_issue_info["fields"][field["fieldId"]] = {}
                    dst_issue_info["fields"][field["fieldId"]]["key"] = jira_project.key
                case "issuetype":
                    dst_issue_info["fields"][field["fieldId"]] = {}
                    dst_issue_info["fields"][field["fieldId"]]["id"] = issue_type_id
                case "summary":
                    dst_issue_info["fields"][field["fieldId"]] = self.title
                case "reporter":
                    dst_issue_info["fields"][field["fieldId"]] = {}
                    dst_issue_info["fields"][field["fieldId"]]["id"] = jira_project.lead_accountid
                case _:
                    dst_issue_info["fields"][field["fieldId"]] = "Place Holder"

        description = (
            f"githubIssueId: {self.id}\n"
            f"githubIssueURL: {self.url}\n"
            f"githubCreatedAt: {self.created_at}\n"
            f"githubUpdatedAt: {self.updated_at}\n"
            f"{self.body + '\n' if self.body is not None else ''}"
        )

        dst_issue_info["fields"]["description"] = {
            "content": [
                {
                "content": [
                    {
                    "text": description,
                    "type": "text"
                    }
                ],
                "type": "paragraph"
                }
            ],
            "type": "doc",
            "version": 1
        }

        payload = json.dumps(dst_issue_info)

        response = requests.request(
            endpoint_info["method"],
            jira_api.base_url + endpoint_info["path"],
            data=payload,
            headers=endpoint_info["headers"],
            auth = jira_api.auth
        )

        return response
