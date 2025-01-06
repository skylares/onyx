import json
import os
import time
from pathlib import Path

import pytest

from onyx.configs.constants import DocumentSource
from onyx.connectors.models import Document
from onyx.connectors.salesforce.connector import SalesforceConnector


def load_test_data(file_name: str = "test_salesforce_data.json") -> dict[str, dict]:
    current_dir = Path(__file__).parent
    with open(current_dir / file_name, "r") as f:
        return json.load(f)


@pytest.fixture
def salesforce_connector() -> SalesforceConnector:
    connector = SalesforceConnector(
        requested_objects=["Account", "Contact", "Opportunity"],
    )
    connector.load_credentials(
        {
            "sf_username": os.environ["SF_USERNAME"],
            "sf_password": os.environ["SF_PASSWORD"],
            "sf_security_token": os.environ["SF_SECURITY_TOKEN"],
        }
    )
    return connector


# TODO: make the credentials not expire
@pytest.mark.xfail(
    reason=(
        "Credentials change over time, so this test will fail if run when "
        "the credentials expire."
    )
)
def test_salesforce_connector_basic(salesforce_connector: SalesforceConnector) -> None:
    test_data = load_test_data()
    target_test_doc: Document | None = None
    all_docs: list[Document] = []
    for doc_batch in salesforce_connector.poll_source(0, time.time()):
        for doc in doc_batch:
            all_docs.append(doc)
            if doc.id == test_data["id"]:
                target_test_doc = doc

    assert len(all_docs) == 6
    assert target_test_doc is not None

    test_data = load_test_data()
    assert target_test_doc.source == DocumentSource.SALESFORCE
    assert target_test_doc.semantic_identifier == "Unknown Object"


# TODO: make the credentials not expire
@pytest.mark.xfail(
    reason=(
        "Credentials change over time, so this test will fail if run when "
        "the credentials expire."
    )
)
def test_salesforce_connector_slim(salesforce_connector: SalesforceConnector) -> None:
    # Get all doc IDs from the full connector
    all_full_doc_ids = set()
    for doc_batch in salesforce_connector.load_from_state():
        all_full_doc_ids.update([doc.id for doc in doc_batch])

    # Get all doc IDs from the slim connector
    all_slim_doc_ids = set()
    for slim_doc_batch in salesforce_connector.retrieve_all_slim_documents():
        all_slim_doc_ids.update([doc.id for doc in slim_doc_batch])

    # The set of full doc IDs should be always be a subset of the slim doc IDs
    assert all_full_doc_ids.issubset(all_slim_doc_ids)
