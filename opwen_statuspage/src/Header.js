import React from 'react';
import PropTypes from 'prop-types';
import { Drawer, PageHeader } from 'antd';
import Button from './Button';
import Settings from './Settings';

class Header extends React.PureComponent {
  state = {
    isSettingsVisible: false,
  };

  _onOpenSettings = () => this.setState({ isSettingsVisible: true });

  _onCloseSettings = () => this.setState({ isSettingsVisible: false });

  render() {
    const { isSettingsVisible } = this.state;
    const { onChangeSettings, settings } = this.props;

    const settingsForm = (
      // @ts-ignore
      <Settings initialValue={settings} onChange={onChangeSettings} />
    );

    return (
      <React.Fragment>
        <PageHeader
          title="Lokole Status Dashboard"
          avatar={
            settings.githubAvatarUrl != null
              ? { src: settings.githubAvatarUrl }
              : { icon: 'user' }
          }
          extra={[
            <Button
              onClick={this._onOpenSettings}
              icon="setting"
              key="setting"
            />,
          ]}
        />
        <Drawer
          title="Settings"
          visible={isSettingsVisible}
          onClose={this._onCloseSettings}
        >
          {settingsForm}
        </Drawer>
      </React.Fragment>
    );
  }
}

Header.propTypes = {
  onChangeSettings: PropTypes.func.isRequired,
  settings: PropTypes.object.isRequired,
};

export default Header;
