import React from 'react';
import { Divider, Layout } from 'antd';
import Header from './Header';
import ClientStats from './ClientStats';
import PingStats from './PingStats';

const localStorageKey = 'settings';

const defaultSettings = {
  pingMaxLatencyMillis: 500,
  pingIntervalSeconds: 5,
  githubAccessToken: undefined,
  githubUsername: undefined,
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
        <Layout style={{ minHeight: '100vh' }}>
          <Header settings={this.state.settings} onChangeSettings={this._onChangeSettings} />
          <Layout.Content style={{ padding: '0 50px' }}>
            <Divider>Stats</Divider>
            <PingStats settings={this.state.settings} key={`stats-${this.state.settings.updatedAt}`} />

            <Divider>Clients</Divider>
            <ClientStats settings={this.state.settings} key={`clients-${this.state.settings.updatedAt}`} />
          </Layout.Content>
        </Layout>
      </React.Fragment>
    );
  }
}

export default App;
