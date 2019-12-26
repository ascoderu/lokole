import React from 'react';
import { Layout } from 'antd';
import Header from './Header';

const localStorageKey = 'settings';

const defaultSettings = {
  githubAccessToken: undefined,
  serverEndpoint: 'https://mailserver.lokole.ca',
};

class App extends React.Component {
  state = {
    settings: { ...defaultSettings, ...JSON.parse(localStorage.getItem(localStorageKey)) },
  };

  _onChangeSettings = settings => {
    localStorage.setItem(localStorageKey, JSON.stringify(settings));
    this.setState({ settings });
  };

  render() {
    return (
      <React.Fragment>
        <Layout>
          <Header settings={this.state.settings} onChangeSettings={this._onChangeSettings} />
          <Layout.Content style={{ padding: '25px 50px 0 50px' }}>
            hi
          </Layout.Content>
        </Layout>
      </React.Fragment>
    );
  }
}

export default App;
