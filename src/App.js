import React from 'react';
import { Divider, Layout } from 'antd';
import Header from './Header';
import ClientStats from './ClientStats';
import PingStats from './PingStats';

const localStorageKey = 'settings';

const defaultSettings = {
  pingIntervalSeconds: 5,
  githubAccessToken: undefined,
  githubUsername: undefined,
  serverEndpoint: 'https://mailserver.lokole.ca',
};

class App extends React.Component {
  state = {
    settings: {
      ...defaultSettings,
      ...JSON.parse(localStorage.getItem(localStorageKey) || '{}'),
    },
  };

  _onChangeSettings = settings => {
    localStorage.setItem(localStorageKey, JSON.stringify(settings));
    this.setState({ settings });
  };

  render() {
    const { settings } = this.state;

    return (
      <React.Fragment>
        <Layout style={{ minHeight: '100vh' }}>
          <Header
            settings={settings}
            onChangeSettings={this._onChangeSettings}
          />
          <Layout.Content style={{ padding: '0 50px' }}>
            <Divider>Stats</Divider>
            <PingStats
              settings={settings}
              key={`stats-${settings.updatedAt}`}
            />
            <Divider>Clients</Divider>
            <ClientStats
              settings={settings}
              key={`clients-${settings.updatedAt}`}
            />
          </Layout.Content>
        </Layout>
      </React.Fragment>
    );
  }
}

export default App;
