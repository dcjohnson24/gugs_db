from bs4 import BeautifulSoup
import pytest


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


@pytest.mark.parametrize('name', ['Joe Smith', 'Enzokuhle Khumalo'])
def test_runner_race_search(test_client, init_database, name):
    data = {'select': 'Runner Name', 'search': f'{name}'}
    response = test_client.post('/runner_race_search',
                                data=data,
                                follow_redirects=True)
    assert response.status_code == 200
    assert b'Search Results - GUGS DB' in response.data

    result_names = []
    soup = BeautifulSoup(response.data, 'html.parser')
    for row in soup.findAll('table')[0].tbody.findAll('tr'):
        result_names.append(row.findAll('td')[1].contents[0])

    assert all(x == result_names[0] for x in result_names)


# TODO Add a parametrize fixture here
@pytest.mark.parametrize('gender', ['male', 'female'])
def test_top_runners(test_client, init_database, gender):
    data = {'select': f'{gender}', 'search': 'peninsula', 'n': 10}
    response = test_client.post('/top_runners_search',
                                data=data,
                                follow_redirects=True)
    assert response.status_code == 200
    assert b'Search Results - GUGS DB' in response.data
    soup = BeautifulSoup(response.data, 'html.parser')
    assert len(soup.findAll('table')[0].tbody.findAll('tr')) == data['n']


@pytest.mark.parametrize('name', ['Joe Smith', 'Enzokuhle Khumalo'])
def test_prediction(test_client, init_database, name):
    data = {'search': name}
    response = test_client.post('/predict', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert str.encode('results for {}'.format(name.lower())) in response.data.lower() 
