import React from 'react';
import { Card, Icon, List, Statistic } from 'antd';
import axios from 'axios';
import Grid from './Grid';

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
    const { serverEndpoint } = this.props.settings;

    const pingStart = new Date();

    let pingSuccess, pingError;
    try {
      await axios.get(`${serverEndpoint}/healthcheck/ping`);
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

  _renderListItem = props => {
    return (
      <List.Item key={props.title}>
        <Card>
          <Statistic {...props} />
        </Card>
      </List.Item>
    );
  };

  async componentDidMount() {
    const { pingIntervalSeconds } = this.props.settings;

    await this._onPing();

    this._pingInterval = setInterval(this._onPing, pingIntervalSeconds * 1000);
  }

  componentWillUnmount() {
    if (this._pingInterval != null) {
      clearInterval(this._pingInterval);
    }
  }

  render() {
    const { pingTimeMillis, pingSuccess, pingError } = this.state;
    const { pingMaxLatencyMillis } = this.props.settings;

    return (
      <Grid
        loading={pingTimeMillis == null || pingSuccess == null}
        dataSource={[
          {
            title: 'Ping time',
            value: pingTimeMillis,
            suffix: 'ms',
            valueStyle: {
              color:
                pingTimeMillis <= pingMaxLatencyMillis
                  ? colors.success
                  : colors.failure,
            },
          },
          {
            title: 'Ping status',
            value: pingSuccess ? 'Ok' : pingError,
            prefix: pingSuccess ? undefined : <Icon type="warning" />,
            valueStyle: {
              color: pingSuccess ? colors.success : colors.failure,
            },
          },
        ]}
        renderItem={this._renderListItem}
      />
    );
  }
}

export default PingStats;
