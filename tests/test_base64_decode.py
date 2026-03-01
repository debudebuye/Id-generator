"""
Tests for base64 PDF decode functionality
"""
import base64
import os
import pytest
from io import BytesIO


def test_decode_route_exists(client):
    """Test that the decode page route exists"""
    response = client.get('/decode')
    assert response.status_code == 200
    assert b'Decode Base64 Document' in response.data


def test_decode_base64_json_with_fin(client):
    """Test decoding with JSON format including FIN"""
    # Minimal valid PDF
    pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids []\n/Count 0\n>>\nendobj\nxref\n0 3\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\ntrailer\n<<\n/Size 3\n/Root 1 0 R\n>>\nstartxref\n110\n%%EOF'
    base64_data = base64.b64encode(pdf_content).decode('utf-8')
    
    response = client.post('/decode_base64',
        json={
            'pdf': base64_data,
            'fullname': 'John Doe',
            'fin': '123456789012'
        },
        content_type='application/json'
    )
    
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['success'] is True
    assert 'redirect' in json_data
    assert json_data['redirect'] == '/preview'
    assert 'extracted_data' in json_data


def test_decode_base64_json_without_fin(client):
    """Test decoding with JSON format without FIN (should fail or extract from PDF)"""
    pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids []\n/Count 0\n>>\nendobj\nxref\n0 3\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\ntrailer\n<<\n/Size 3\n/Root 1 0 R\n>>\nstartxref\n110\n%%EOF'
    base64_data = base64.b64encode(pdf_content).decode('utf-8')
    
    response = client.post('/decode_base64',
        json={
            'pdf': base64_data,
            'fullname': 'John Doe'
        },
        content_type='application/json'
    )
    
    # Should fail because FIN cannot be extracted from minimal PDF
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['success'] is False
    assert 'FIN' in json_data['error']


def test_decode_base64_form_data(client):
    """Test decoding with form data"""
    pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids []\n/Count 0\n>>\nendobj\nxref\n0 3\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\ntrailer\n<<\n/Size 3\n/Root 1 0 R\n>>\nstartxref\n110\n%%EOF'
    base64_data = base64.b64encode(pdf_content).decode('utf-8')
    
    response = client.post('/decode_base64', data={
        'base64_data': base64_data,
        'fin': '123456789012'
    })
    
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['success'] is True


def test_decode_base64_with_data_uri(client):
    """Test decoding base64 with data URI prefix"""
    pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids []\n/Count 0\n>>\nendobj\nxref\n0 3\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\ntrailer\n<<\n/Size 3\n/Root 1 0 R\n>>\nstartxref\n110\n%%EOF'
    base64_data = base64.b64encode(pdf_content).decode('utf-8')
    data_uri = f'data:application/pdf;base64,{base64_data}'
    
    response = client.post('/decode_base64',
        json={
            'pdf': data_uri,
            'fin': '123456789012'
        },
        content_type='application/json'
    )
    
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['success'] is True


def test_decode_base64_invalid_encoding(client):
    """Test decoding invalid base64 data"""
    response = client.post('/decode_base64',
        json={
            'pdf': 'This is not valid base64!!!',
            'fin': '123456789012'
        },
        content_type='application/json'
    )
    
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['success'] is False
    assert 'Invalid base64 encoding' in json_data['error']


def test_decode_base64_not_pdf(client):
    """Test decoding base64 that's not a PDF"""
    text_content = b'This is just plain text, not a PDF'
    base64_data = base64.b64encode(text_content).decode('utf-8')
    
    response = client.post('/decode_base64',
        json={
            'pdf': base64_data,
            'fin': '123456789012'
        },
        content_type='application/json'
    )
    
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['success'] is False
    assert 'not a valid PDF' in json_data['error']


def test_decode_base64_empty_data(client):
    """Test decoding with empty base64 data"""
    response = client.post('/decode_base64',
        json={'pdf': ''},
        content_type='application/json'
    )
    
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['success'] is False
    assert 'No base64 data provided' in json_data['error']


def test_decode_base64_invalid_fin(client):
    """Test decoding with invalid FIN format"""
    pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids []\n/Count 0\n>>\nendobj\nxref\n0 3\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\ntrailer\n<<\n/Size 3\n/Root 1 0 R\n>>\nstartxref\n110\n%%EOF'
    base64_data = base64.b64encode(pdf_content).decode('utf-8')
    
    response = client.post('/decode_base64',
        json={
            'pdf': base64_data,
            'fin': '12345'  # Invalid - not 12 digits
        },
        content_type='application/json'
    )
    
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['success'] is False
    assert 'Invalid FIN' in json_data['error']


def test_decode_base64_with_whitespace(client):
    """Test decoding base64 with whitespace and newlines"""
    pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids []\n/Count 0\n>>\nendobj\nxref\n0 3\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\ntrailer\n<<\n/Size 3\n/Root 1 0 R\n>>\nstartxref\n110\n%%EOF'
    base64_data = base64.b64encode(pdf_content).decode('utf-8')
    
    # Add whitespace and newlines
    base64_with_whitespace = '\n'.join([base64_data[i:i+64] for i in range(0, len(base64_data), 64)])
    
    response = client.post('/decode_base64',
        json={
            'pdf': base64_with_whitespace,
            'fin': '123456789012'
        },
        content_type='application/json'
    )
    
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['success'] is True


@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    from app import create_app
    app = create_app()
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    with app.test_client() as client:
        yield client
