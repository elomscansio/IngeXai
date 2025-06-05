# Mock external document management API service

import logging

def external_create_document(document_data):
    logging.info(f"Simulating external document creation: {document_data}")
    # Simulate external API response
    return {"external_id": f"ext_{document_data.get('name', 'doc')}", "status": "created"}

def external_delete_document(external_id):
    logging.info(f"Simulating external document deletion: {external_id}")
    return {"external_id": external_id, "status": "deleted"}

def external_fetch_document(external_id):
    logging.info(f"Simulating external document fetch: {external_id}")
    return {"external_id": external_id, "content": "Simulated external content"}
