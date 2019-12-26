import React from 'react';
import { Drawer, PageHeader } from 'antd';
import Button from './Button';
import Settings from './Settings';

class Header extends React.PureComponent {
  state = {
    isSettingsVisible: false
  };

  _onOpenSettings = () => this.setState({ isSettingsVisible: true });

  _onCloseSettings = () => this.setState({ isSettingsVisible: false });

  render() {
    const { isSettingsVisible } = this.state;
    const { onChangeSettings, settings } = this.props;

    return (
      <React.Fragment>
        <PageHeader
          title="Opwen Status Dashboard"
          avatar={settings.githubAvatarUrl != null
            ? { src: settings.githubAvatarUrl }
            : { icon: 'user' }}
          extra={[
            <Button
              onClick={this._onOpenSettings}
              icon="setting"
            />,
          ]}
        />
        <Drawer title="Settings" visible={isSettingsVisible} onClose={this._onCloseSettings}>
          <Settings initialValue={settings} onChange={onChangeSettings} />
        </Drawer>
      </React.Fragment>
    );
  }
}

export default Header;
