import React from 'react';
import { Card, Icon, List, Statistic } from 'antd';
import axios from 'axios';

const colors = {
  success: '#3f8600',
  failure: '#cf1322',
};

class PingStats extends React.Component {
  state = {
    pingTimeMillis: undefined,
    pingSuccess: undefined,
    pingError: undefined,
  };

  _pingInterval = undefined;

  _onPing = async () => {
    const pingStart = new Date();

    let pingSuccess, pingError;
    try {
      await axios.get(`${this.props.settings.serverEndpoint}/healthcheck/ping`);
      pingSuccess = true;
    } catch (e) {
      pingError = (e.response && e.response.data) || e.message;
      pingSuccess = false;
    }

    this.setState({
      pingTimeMillis: new Date() - pingStart,
      pingSuccess,
      pingError,
    });
  };

  _renderListItem = (props) => {
    return (
      <List.Item key={props.title}>
        <Card>
          <Statistic {...props} />
        </Card>
      </List.Item>
    );
  }

  async componentDidMount() {
    await this._onPing();
    this._pingInterval = setInterval(this._onPing, this.props.settings.pingIntervalSeconds * 1000);
  }

  componentWillUnmount() {
    if (this._pingInterval != null) {
      clearInterval(this._pingInterval);
    }
  }

  render() {
    return (
      <List
        grid={{ gutter: 16, column: 4 }}
        itemLayout="vertical"
        loading={this.state.pingTimeMillis == null || this.state.pingSuccess == null}
        dataSource={[
          {
            title: 'Ping time',
            value: this.state.pingTimeMillis,
            suffix: 'ms',
            valueStyle: {
              color: this.state.pingTimeMillis <= this.props.settings.pingMaxLatencyMillis
                ? colors.success
                : colors.failure,
            },
          },
          {
            title: 'Ping status',
            value: this.state.pingSuccess ? 'Ok' : this.state.pingError,
            prefix: this.state.pingSuccess ? undefined : <Icon type="warning" />,
            valueStyle: { color: this.state.pingSuccess ? colors.success : colors.failure },
          },
        ]}
        renderItem={this._renderListItem}
      />
    );
  }
}

export default PingStats;
