import pytest


def test_csrf_blocks_post_without_token(client, app):
    """State-changing POST must include CSRF token when protection is enabled."""
    app.config['TESTING'] = False
    app.config['WTF_CSRF_ENABLED'] = True
    response = client.post(
        '/add_transaction',
        data={'merchant': 'Test', 'amount': '10.00', 'category': 'food'},
    )
    assert response.status_code == 400


def test_csrf_allows_post_with_token(client, app):
    app.config['TESTING'] = False
    app.config['WTF_CSRF_ENABLED'] = True
    page = client.get('/add_transaction')
    assert page.status_code == 200
    token = None
    for line in page.data.decode('utf-8').splitlines():
        if 'csrf_token' in line and 'value=' in line:
            start = line.find('value="') + len('value="')
            end = line.find('"', start)
            token = line[start:end]
            break
    assert token
    response = client.post(
        '/add_transaction',
        data={
            'csrf_token': token,
            'merchant': 'CSRF_Test',
            'amount': '3.00',
            'category': 'test',
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
