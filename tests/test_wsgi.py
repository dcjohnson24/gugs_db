def test_home_page(test_client):
    response = test_client.get('/')
    assert response.status_code == 200
    text_list = ['RCS Gugulethu AC', 'Home', 'Search Runner',
                 'Search Race', 'Predict Race Time', 'Login']
    text_list_bytes = [str.encode(x) for x in text_list]
    assert all(x in response.data for x in text_list_bytes)


def test_valid_login_logout(test_client, init_database):
    data = {'email': 'some_user@gmail.com',
            'password': 'some_password',
            'follow_redirects': True}
    response = test_client.post('/login', data=data, follow_redirects=True)
    text_list = ['Welcome, Some User', 'Home', 'Search Runner',
                 'Search Race', 'Predict Race Time', 'Logout']
    text_list_bytes = [str.encode(x) for x in text_list]
    assert all(x in response.data for x in text_list_bytes)

    response = test_client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'Login' in response.data
